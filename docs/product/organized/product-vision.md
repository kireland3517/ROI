# Product Vision

Synthesized from `Property_ROI_Analysis_Tool_PRD_v0_8.docx` and `Property ROI Analysis Tool — Technical Specification V4`. PRD is highest product authority where sources differ.

## Core question

> What should this seller spend money on, in what order, and why?

The Property ROI Analysis Tool is a **seller decision tool**, not a generic renovation calculator. It analyzes property condition, seller timeline, market context, carrying costs, buyer-segment fit, and improvement options to produce a prioritized **Seller ROI Action Plan**.

## MVP differentiator

**Scarcity-Aware Seller Action Sequencer** — surfaced through the Seller ROI Action Plan. It combines:

1. **Automated schedule recalibration and setup-dependency tracking** — sequences work so upstream repairs complete before dependent cosmetic or presentation tasks; recalculates when critical-path items delay.
2. **Supply-modulated resale lift and over-improvement logic** — adjusts ROI interpretation using active local supply and market velocity (Redfin Phase 1).

## User types and goals

| User type | Primary need |
|---|---|
| Homeowner | Plain-language guidance on what to fix, what not to fix, and why |
| Agent | Credible, explainable client-facing action plan |
| Investor / flipper | Price-per-square-foot discipline, neighborhood ceiling awareness, structural-risk clarity |

| Supported goal | Emphasis |
|---|---|
| Sell | Full seller action plan with repair, cosmetic, DOM, and carrying-cost logic |
| Flip | Tier 1, structural, margin-protective, ceiling-aware items |
| Refinance | Appraiser-weighted and condition-supported improvements |

**Not in MVP:** "Renovate" as a standalone goal.

## Sale timeline scopes recommendations

| Timeline | Recommendation scope |
|---|---|
| Under 30 days | Critical repairs, listing-readiness, presentation, cosmetic quick wins only |
| 30–90 days | Moderate scope; contractor work if scheduled immediately |
| 3–6 months | Full improvement plan including permitted work where realistic |
| 6+ months | Longer-horizon planning; larger rehab if data-supported |

Items infeasible before target list date go to **Beyond Your Timeline**, not the main plan.

## What MVP must do

- Rank and explain seller-specific repair and improvement actions
- Sequence actions with duration, lead-time, dependency, and budget constraints
- Show confidence labels and anomaly callouts when data or timing is uncertain
- Use governed seed tables and static assumptions where calibration is not approved
- **Refuse** diagnostic or unapproved regression coefficients in seller-facing recommendations (Decisions Log V12 / Tech Spec V4)

## What MVP must not do

- Present outputs as appraisals, legal advice, tax advice, contractor guarantees, or guaranteed resale outcomes
- Use generic fallback timing for sequencer-required repair types without explicit seed rows
- Wire Greenville v0.1 (`diagnostic_only`, `approved_for_recommendations: false`) into seller-facing ROI logic
- Ship without legal review of public claims and disclaimers

## Phase framing (from PRD build sequence)

| Phase | Focus |
|---|---|
| Phase 1 (prototype/MVP) | Guided intake, ATTOM/Smarty, condition photos, sequencer, seed tables, Redfin supply, carrying cost, DOM, anomalies, mobile + desktop layouts |
| Phase 2 | SKU-level pricing decision, PDF export, agent branding, seasonal demand, after-photo comparison, expanded HOA, multi-unit/condo |
| Phase 3 | MLS integration, contractor-market data, energy-efficiency module, richer quote validation |

## Current project posture (June 2026)

Per Technical Specification V4 and Master Running Checklist:

- Product definition is **mostly stable** (PRD v0.8)
- Project is in **pre-build specification and implementation-readiness** mode
- Sequencer coding is **blocked** until seed QA, dependency export, and expert validation close
- Regression pipeline is **runnable for Greenville smoke test** but **not approved** for product recommendations

## Source references

- `docs/product/raw/Property_ROI_Analysis_Tool_PRD_v0_8.docx`
- `docs/product/raw/Property ROI Analysis Tool — Technical Specification V4`
- `docs/product/raw/Decisions Log V12.docx`
