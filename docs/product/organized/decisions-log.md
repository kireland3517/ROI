# Decisions Log

**Scope of this file:** Only decisions present in the `raw/` export set. `Decisions Log V12.docx` is the latest log here. V10 and V11 are **referenced** by other artifacts but **not exported** to `raw/` — their decisions are cited below only where V12 or other raw files quote them.

**Governing constraint (V12):** A regression artifact may be used by the product only after it is versioned, validated, explicitly approved, and marked `approved_for_recommendations: true`.

---

## Decisions Log V13 (June 2026)

V13 records product-scope, intake-architecture, and seed-handoff decisions made at the start of the first build slice. **V13 does not approve any regression artifact for recommendations.**

### Summary table

| ID | Decision | Classification | Primary artifacts affected |
|---|---|---|---|
| D-V13-001 | Adopt Intake Question Strategy V1 progressive intake over PRD v0.8 heavy intake | MVP | User flow, intake UI, report degradation rules |
| D-V13-002 | ROI Tool is the national/scalable main product; Simpsonville Analyzer is reference-only | MVP scope | Product vision, repo boundaries, engine architecture |
| D-V13-003 | Seed handoff format is versioned CSV committed to the repo | MVP architecture | Seed tables, seed loader, `app/seeds/` |

---

### D-V13-001 — Progressive intake (Intake Strategy V1 wins)

Resolves the PRD v0.8 vs Intake Question Strategy V1 conflict logged in `user-flow.md` and `open-questions.md`.

| Topic | Decision |
|---|---|
| Starter intake | Four required inputs: address, seller objective, target timing, spend comfort range |
| Smarty gate | Retained from PRD §2.1 — user must confirm standardized address before ATTOM |
| Budget | Collected as spend-comfort band at start (Intake Strategy position) |
| Mortgage payment / payoff | Removed from starter flow; moves behind optional Net Proceeds / carrying-cost module |
| Condition assessment | Optional issue picker in starter flow (Condition Boost lite); guided photo flow deferred to a later slice |
| Starter report | Generated before any deep asks; skipped inputs degrade confidence labels, never fabricate |
| PRD deep intake | Survives as optional unlock modules (Budget Refinement, Net Proceeds, Timeline Compression) |

Rationale: a national-product stranger will not complete a heavy intake before seeing value; graceful degradation is already specified; the Simpsonville Analyzer's budget-scenario UX is field evidence that spend-band framing is legible to sellers.

---

### D-V13-002 — National product scope and Simpsonville Analyzer boundary

| Topic | Decision |
|---|---|
| ROI Tool scope | National/scalable seller decision-support product; works for any US single-family address |
| Market specificity | Configurable data only (seed tables, market data feeds, per-market registry artifacts) — never hardcoded |
| Hardcoding prohibition | No addresses, comps, ARV figures, ZIP/city/state names, contractor rates, or market commentary as code literals in seller-facing paths |
| Engine architecture | Deterministic, explainable, seed-table-driven (Tech Spec V4). LLMs may later power the explanation/copy layer only |
| Simpsonville Analyzer | Reference/prototype/lab only. Zero modifications of any kind. Patterns (evidence tiers, citation rationale, traceability) are rebuilt in the ROI Tool, never copied as code |

---

### D-V13-003 — Seed handoff format: versioned CSV

Resolves FU-SRC-003.

| Topic | Decision |
|---|---|
| Authoritative handoff | Versioned CSV files committed under `app/seeds/` |
| Source workbooks | `docs/product/raw/Seed Tables.xlsx` remains the source workbook; CSVs are the executable export |
| Loader behavior | Seed loader is review-status aware; rows pending QA are labeled as static assumptions in output provenance |
| Versioning | Seed files carry a version suffix (`*_v0.csv`); row-level `review_status` and `version` columns preserved |

---

## Decisions Log V12 (June 2026)

V12 records Greenville regression calibration workstream decisions. **V12 does not approve Greenville coefficients for product recommendations.**

### Summary table

| ID | Decision | Classification | Primary artifacts affected |
|---|---|---|---|
| D-V12-001 | Correct ATTOM `sale_date` export mapping | MVP | ATTOM adapter, regression pulls, QA tests |
| D-V12-002 | Greenville corrected CSV = first governed regression smoke-test fixture | MVP | Fixtures, smoke-test script |
| D-V12-003 | Greenville smoke regression passed **pipeline validation only**, not production calibration | MVP / diagnostic-only | Diagnostics, model registry, promotion gates |
| D-V12-004 | Coefficients live in versioned model registry artifact, not diagnostics or hardcoded app logic | MVP architecture | Model registry, backend loader, Tech Spec |
| D-V12-005 | Registry validation + promotion-readiness required before recommendation use | MVP governance | Validator, promotion report, testing plan |
| D-V12-006 | Do not repull all metros until diagnostics justify expansion | MVP cost-control | Regression roadmap, ATTOM usage plan |

---

### D-V12-001 — ATTOM sale_date export mapping

Populate application `sale_date` from ATTOM sale snapshot in this order:

| Priority | Field |
|---|---|
| Primary | `sale.saleTransDate` |
| Fallback 1 | `sale.salesearchdate` |
| Fallback 2 | `sale.amount.salerecdate` |
| **Rejected** | `sale.amount.saletransdate` |

- Fix belongs in **pull/export mapper**, not regression logic
- QA: validate nonblank and parseable `sale_date` coverage before regression

---

### D-V12-002 — Greenville smoke-test fixture

Corrected Greenville-Anderson-Greer CSV accepted as first governed MVP regression smoke-test fixture.

| Metric | Value |
|---|---|
| Corrected rows | 4,000 |
| Nonblank / parseable sale_date | 3,980 |
| Usable rows (all dates, conservative) | 1,477 |
| Recommended smoke window | 2024-01-01 through 2026-06-03 |
| Usable rows in window | 1,169 |

Sufficient for pipeline validation; **not** sufficient alone to approve production model.

---

### D-V12-003 — Pipeline validation vs product calibration

| Area | Status |
|---|---|
| Smoke-test | Passed |
| Product calibration | Not approved |
| Reported test R² | ~0.09 |
| Interpretation | Acceptable for smoke test; weak for recommendation calibration |
| Next step | Diagnostics and promotion-readiness, **not** recommendation-engine wiring |

---

### D-V12-004 — Versioned model registry artifact

| Artifact class | Treatment |
|---|---|
| Development diagnostics | Engineering review only |
| Modeling dataset | Reproducibility / debugging |
| Versioned coefficient artifact | Product-facing calibration **pattern** |
| Application code | Load only approved artifacts via controlled interface |

Owner-reported Greenville artifact: `model_registry/greenville_sc/hedonic_ppsf_v0_1.json`  
Status: `diagnostic_only`, `approved_for_recommendations: false`, intercept 5.2216

---

### D-V12-005 — Validation and promotion gates

| Gate | Requirement |
|---|---|
| Registry artifact validation | Required for every coefficient artifact |
| Required fields | Model ID, version, market, target, type, coefficients, features, metrics, paths, status, approval flag |
| Diagnostic rule | `diagnostic_only` must have `approved_for_recommendations: false` |
| Promotion-readiness | Required before manual approval |
| Automatic approval | **Rejected** |

Validator reported: `regression/validate_model_registry_artifact.py` — PASS 11/11 (structural only).

---

### D-V12-006 — Defer API expansion

| Action | Treatment |
|---|---|
| Full 12-metro repull | **Defer** |
| Greenville-only diagnostics | **Do next** |
| Recommendation-engine wiring | **Reject for now** |
| Additional feature sourcing | Evaluate after diagnostics |

---

## Readiness gate updates (V12)

| Gate | Prior | V12 |
|---|---|---|
| RG-REG-001 | Open | Partially closed / narrowed |
| RG-REG-002 | New | Closed for Greenville smoke test |
| RG-REG-003 | New | Closed structurally (registry + validator) |
| RG-REG-004 | New | Open (promotion-readiness) |
| RG-API-001 | Open | Partially closed for sale-date path only |

---

## Explicit non-decisions (V12)

Not decided by V12 — do not infer:

- Approval of Greenville v0.1 for seller-facing recommendations
- Final R² / MAE / RMSE / residual-bias thresholds
- Final model class (Ridge or other)
- Final target (`log(price_per_sqft)` vs alternatives)
- Immediate 12-metro repull (rejected for now, not permanently)
- File-only vs database model registry for production
- ATTOM enriched field availability for calibration

---

## Referenced decisions from V11 (not in raw export)

Other raw artifacts cite these V11 decisions. Treat as governing for sequencer topics unless superseded:

| Referenced ID | Topic (from citing artifacts) |
|---|---|
| D-V11-001 | Split accessibility improvements into subtypes (minor vs exterior access) |
| D-V11-002 | Professional staging anomaly when target list &lt; 21 days |
| D-V11-003 | 13 missing duration/lead-time repair types are legitimate sequencer items |
| D-V11-004 | Angi/HomeAdvisor values acceptable as Phase 1 static assumptions v1.0 pending row-level QA |

**Source for V11 text:** `Open Questions Log V1`, `Duration_Lead-Time Seed Table v1.0`, `Dependency Rules v1.0 Addendum`, `Recommendation Anomaly Rules v1.0`, `Static Data Source Register V2`. Full V11 log not in `raw/`.

---

## Implementation capture (owner-reported, not a decision)

`Cursor Regression Implementation Capture.docx` records:

- `run_greenville_smoke_regression.py` writes diagnostics + registry artifact
- `validate_model_registry_artifact.py` — PASS 11/11, exits 1 on failure, does not approve model
- Accepted as implementation milestone; **does not** approve model for recommendations

---

## Source references

- `docs/product/raw/Decisions Log V12.docx`
- `docs/product/raw/Cursor Regression Implementation Capture.docx`
- `docs/product/raw/Regression Model Registry and Promotion Governance v1.docx`
