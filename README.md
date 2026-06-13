# Property ROI Analysis Tool

A national seller decision-support product answering one question:

> **What should this seller spend money on, in what order, and why?**

This repo contains two workstreams:

1. **`app/` — the product (first build slice).** Progressive intake → address validation → ATTOM property facts → a deterministic, seed-table-driven Seller Action Plan with provenance labels on every number.
2. **`regression/` — the market calibration pipeline.** ATTOM comps ETL and the Greenville smoke regression. Model artifacts live in `model_registry/` and are governed by promotion gates — **no artifact is consumed by the product unless `status == "approved"` and `approved_for_recommendations == true`** (Decisions Log V12). The current Greenville artifact is `diagnostic_only` and is refused by the app by design.

Product definition lives in [`docs/product/organized/`](docs/product/organized/) (PRD synthesis, decisions log, recommendation logic, report structure, open questions). Raw Google Drive exports are under `docs/product/raw/` and are read-only sources.

## Seller flow

1. **Address entry** — standardized address + optional autocomplete (server-side proxy)
2. **Confirm property** — verify USPS-standardized or demo formatting-check address
3. **Three questions** — goal, timeline, spend comfort (one screen each)
4. **Known problems** — optional grouped issue picker + custom note
5. **Building** — plan generation with plain-language progress steps
6. **Seller Action Plan** — executive verdict, timeline-ordered actions, Do Not Spend, assumptions, disclaimer

Local market context (recorded comp stats) is **presentation-only** when available — it never influences recommendations.

## Running the app

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Then open http://127.0.0.1:8000.

### Environment

Copy `.env.example` to `.env` for local development (never commit `.env` — it is gitignored). The app reads the local `.env` via python-dotenv; real process environment variables (e.g. Railway service variables) always take precedence.

| Variable | Required | Behavior |
|---|---|---|
| `APP_ENV` | no (default `development`) | `development` or `production` |
| `USE_DEMO_FALLBACK` | no | Default `true` in development, `false` in production. `true`: run keyless (stub address check, labeled ATTOM fallback). `false`: Smarty credentials are required — the app fails clearly rather than running the validation gate on a stub. |
| `SMARTY_AUTH_ID` / `SMARTY_AUTH_TOKEN` | production: yes | Real USPS standardization via the Smarty US Street API. Without them (demo mode only), a formatting-check stub runs behind the same interface. |
| `SMARTY_LICENSE` | no | Optional license slug from Smarty → Account → Subscriptions. Pass it only if autocomplete fails or Smarty told you to pin a specific license when multiple apply. |
| `ATTOM_API_KEY` | no | Property facts from county records. If absent or the call fails, the report falls back to user-entered facts with a visible warning — it never crashes the flow (PRD error UX). |
| `DEBUG_PROPERTY_FACTS` | no | Log ATTOM mapping + session facts to the server console (never logs API keys). |

**Demo mode (no keys):** with `APP_ENV=development` (or `USE_DEMO_FALLBACK=true`), the full flow works end to end with zero credentials — address validation runs as a labeled formatting check and the report renders with the county-records-unavailable warning.

### Deploying to Railway

The repo includes a `Procfile` (`web: uvicorn app.main:app --host 0.0.0.0 --port $PORT`). After creating the service, connect the GitHub repo and deploy `main`. Set these variables in Railway:

```
APP_ENV=production
USE_DEMO_FALLBACK=false
SMARTY_AUTH_ID=<your id>
SMARTY_AUTH_TOKEN=<your token>
ATTOM_API_KEY=<your key>
```

`PORT` is injected by Railway automatically — do not set it.

**Operational notes:** sessions are in-memory (lost on redeploy; fine for a single instance). There is no auth — anyone with the URL can generate plans against your ATTOM quota. Pushes to `main` trigger redeploys when GitHub integration is enabled.

## UI and design system

Seller-facing UI is **FastAPI + Jinja + tokenized CSS** — no frontend build step.

| Layer | Path | Role |
|---|---|---|
| Tokens | `app/static/css/tokens.css` | Slate-blue palette, type, spacing, shadows |
| Base / components | `base.css`, `components.css` | Buttons, inputs, chips, cards, warnings |
| Intake / report | `intake.css`, `report.css` | Screen layouts, horizon timeline |
| Visual motifs | `visual-system.css`, `partials/_intake_visuals.html` | CSS/SVG plan previews (no stock photography) |

Palette roles: slate primary (`#3F5F73`), warm paper (`#F7F4EE`), muted brass for timeline rail only (`#B8935A`). Do not add one-off hex colors outside `tokens.css`.

### Cursor skills (project)

UI/copy conventions for agents and contributors live in `.cursor/skills/`:

- `design-system` — tokens and components
- `frontend-design` — intake screen patterns
- `report-design` — Seller Action Plan sections
- `ux-copy` — seller-facing language rules
- `accessibility-review` — focus, ARIA, contrast checklist

## Architecture (first slice)

- `app/main.py` — FastAPI routes: intake flow, building screen, plan rendering
- `app/engine.py` — deterministic engine v0: eligibility, tier ordering, timeline feasibility, Do Not Spend / Beyond Your Timeline, citation validation, trace IDs
- `app/registry.py` — model artifact loader whose only v0 behavior is refusal of unapproved artifacts
- `app/adapters/` — Smarty validation gate (stub) and ATTOM property-facts adapter with fallback
- `app/seeds/` — versioned CSV seed tables (D-V13-003) + review-status-aware loader
- `app/templates/`, `app/static/` — server-rendered Jinja, tokenized CSS, light JS

### Seed tables and issue picker groups

- `app/seeds/catalog_v0.csv` — repair catalog and cost bands
- `app/seeds/issue_picker_v0.csv` — intake issue options
- `app/seeds/issue_picker_groups_v0.csv` — UI grouping for the issue picker

**Sync rule:** every row in `issue_picker_v0.csv` must appear exactly once in `issue_picker_groups_v0.csv`. `load_issue_picker_groups()` fails at startup/tests if they drift apart.

### Hard rules

- No regression coefficients in any seller-facing path (enforced by `app/registry.py` + tests)
- No market names, addresses, or local cost assumptions hardcoded in code or copy (enforced by `tests/test_copy_guard.py`)
- Every recommendation carries citations and a seed-table trace ID (enforced by engine validation)
- All cost figures are labeled static assumptions ("Standard estimate v1.0") pending source QA
- No unsupported ARV, ROI, or home-value claims in seller-facing copy (enforced by tests)

## Tests

```bash
python -m pytest tests/ -v
```

## Regression pipeline

See `regression/` scripts (`pull_comps.py`, `run_greenville_smoke_regression.py`, `validate_model_registry_artifact.py`). Governed by `docs/product/organized/decisions-log.md` — the smoke model passed pipeline validation only and is prohibited from recommendations.
