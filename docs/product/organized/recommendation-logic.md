# Recommendation Logic

Synthesized from PRD v0.8, seed-table artifacts, hedonic matrix, anomaly rules, dependency addendum, and regression/model governance docs. Describes **documented** logic only.

---

## Engine overview (Tech Spec V4)

Deterministic, explainable, seed-table-driven MVP pipeline:

1. Input normalization
2. Candidate generation (catalog + property signals)
3. Eligibility filtering
4. Model artifact selection (approved artifacts only)
5. ROI scoring
6. Timeline feasibility (duration/lead-time, target list date)
7. Dependency sequencing
8. Anomaly detection
9. Output assembly with trace IDs

Every step must persist trace data (rule IDs, seed versions, source IDs, anomaly IDs, model IDs where used).

---

## Repair tiers (PRD)

| Tier | Definition | Plan position |
|---|---|---|
| Tier 1: Critical | Inspection-failing, lender-blocking, disclosure-sensitive, safety, habitability, deal-killing | Always first; market scarcity cannot eliminate |
| Tier 2: Deferred maintenance | Not failing but neglected or likely inspection objections | After Tier 1 |
| Tier 3: Cosmetic / value-add | Functional but dated or presentation-related | After Tier 1–2 |

**Ordering within tiers:** Tier 1 by cost-of-not-fixing penalty, safety/disclosure seriousness, dependency position. Tier 2–3 by ROI adjusted for DOM impact, timeline feasibility, dependencies, buyer-segment fit, supply context, carrying-cost impact.

---

## Scarcity-Aware Seller Action Sequencer

### Inputs (V4)

| Input | Source | Status |
|---|---|---|
| Repair/improvement catalog | Recommendation catalog | Parent-child support required for accessibility |
| Duration / lead-time | `duration_lead_time_rules` seed table | Draft; source QA open |
| Dependency ordering | `dependency_rules` | Build blocker — expert validation open |
| Target list date | Seller input | Required |
| Budget constraint | Seller input (PRD: inferred; Intake Strategy: spend comfort — see `user-flow.md` conflict) | Required for prioritization |
| Carrying-cost assumptions | Product/financial assumptions | Must be source-labeled |
| Anomaly rules | `recommendation_anomaly_rules` | Staging rule approved |
| ROI calibration | Static assumptions or **approved** model artifacts only | Diagnostic models prohibited |

### Sequencer rules

- **No generic fallback timing** for the 13 previously missing duration/lead-time repair types (Decisions Log V11 / V12 references via V4)
- Rows pending source QA: block final readiness OR label as static assumption in internal traces
- Accessibility: engine uses **subtype rows** internally; UI may show parent label

### Accessibility subtypes (approved direction)

| Parent | Subtype | MVP treatment |
|---|---|---|
| Accessibility improvements | Minor accessibility improvements (grab bars, threshold mods) | Subtype-specific duration, dependency, cost, trace |
| Accessibility improvements | Exterior access modifications (ramps, access-path) | Subtype-specific; do not merge with minor |

Broad row `DLT-030-REPLACED` retained for traceability only — **do not use** for sequencing after subtype migration.

**Open:** Whether DOM impact inherits from parent or splits by subtype (OQ-SEQ-004).

---

## Duration and lead-time seed data

### Authoritative workbooks

| Artifact | Rows | Notes |
|---|---|---|
| `Seed Tables.xlsx` — Duration Lead Time Rules | 31 | Expanded source-governance columns (legacy ref, source_name, URL, etc.) |
| `duration_lead_time_rules_v1_0.xlsx` | 16 | Partial export: 13 missing types + accessibility subtypes + replaced row |

### Review status vocabulary (inconsistent across exports — normalize before implementation)

`pending`, `estimated`, `proposed_pending_source_QA`, `replaced_by_subtypes`, `approved_by_owner`, `expert_validated`

### Key duration rows (13 previously missing + staging)

Includes: non-functional minor systems, HVAC filter/tune-up, worn deck boards, caulking/weatherstripping, cracked driveway/walkway, window seal failure, kitchen cabinet hardware, fixture replacement, landscaping/curb appeal, **professional staging** (lead-time high = 21 days), professional photography, closet organization, accessibility subtypes DLT-030A/B.

**Staging linkage:** Duration row DLT-024 supports anomaly `ANOM-STAGING-UNDER-21-DAYS`.

---

## Dependency rules

### Status

- **Build blocker** before sequencer coding (expert GC/remodeling PM validation required)
- `Seed Tables.xlsx` Dependency Rules sheet: 31 rows, all `review_status = pending`
- 9 rows reference D-V11-003; 22 have no decision reference

### Examples from addendum + seed sheet

| Repair type | Dependency treatment |
|---|---|
| Mold remediation | Hard dependency on water intrusion, broken plumbing, roof (critical path) |
| Gutter repair | Hard dependency on roof replacement |
| Interior paint / flooring | Hard dependency on resolving water intrusion (and flooring before paint chain) |
| Fixture replacement | Hard dependency on rough plumbing/electrical work + inspection |
| Landscaping / curb appeal | Hard dependency on sewer/septic when present |
| Deep cleaning | Hard dependency on messy repairs completing first |
| Professional staging | Soft sequencing after repairs; **anomaly** handles lead-time risk |
| Minor accessibility | No hard dependency by default |
| Exterior access modifications | Potential dependency on site/concrete/grading/walkway work |

### Required seed fields

`rule_id`, `repair_type`, `depends_on_repair_type`, `dependency_type` (hard/soft/none), `critical_path_flag`, `source_reference`, `review_status`, `version`

---

## Anomaly rules

Separate from ranking/scoring. First approved MVP rule:

| Field | Value |
|---|---|
| rule_id | `ANOM-STAGING-UNDER-21-DAYS` |
| repair_type | Professional staging |
| trigger | target list date &lt; 21 days away |
| severity | Timeline / scheduling risk |
| ranking effect | Do not auto-remove staging; mark timeline-risk |
| decision_reference | D-V11-002 |

Model-artifact refusal is an **engine guardrail**, not a seller-facing anomaly.

---

## DOM impact (PRD Appendix A)

Every recommendation carries `dom_impact`: +1 (reduces DOM), 0 (no clear effect), -1 (increases DOM/concession/deal risk).

Values vary by **repair type** and **market supply band** (Low / Normal / High supply from Redfin data).

When DOM logic conflicts with supply context, surface as **anomaly callout** (e.g., water intrusion stays severe in any market).

---

## Supply-modulated logic

Redfin Phase 1 fields: active listings, median DOM, months of supply, supply velocity.

- Modulates Tier 2–3 urgency, resale-lift interpretation, over-improvement warning severity
- Does **not** remove Tier 1 disclosure/safety concerns

### Neighborhood ceiling / over-improvement

- Ceiling from comps + market context
- **Over-improvement flag** when current value + projected lift exceeds ceiling by **>7%** (trigger, not substitute for reasoning)
- Supply context may downgrade severity or add context in constrained markets; must not hide ceiling calculation

---

## Buyer segment scoring (PRD)

Five segments via normalized weighted index: first-time buyers, move-up, retirees/downsizers, investors/flippers, relocation buyers.

**Mixed-market flag** when top two segment scores within 10 points.

Hedonic matrix (`Property_Attribute_Hedonic_Matrix_v2.xlsx`) defines:
- Signal encoding (-1 / 0 / 1) with UAD/FEMA/Walk Score/etc. thresholds
- Segment signal matrix (how each segment interprets each attribute)
- Placeholder coefficients for Phase 1 calc engine

Phase 1 coefficients are **placeholders**, labeled calibration v0.1 — not appraisal-grade.

---

## Cost and value vectors (PRD)

| Layer | Source | Role |
|---|---|---|
| Cost | EstimationPro.ai (primary); BLS labor fallback | Localized construction cost ranges |
| Value | ATTOM AVM + comps | Baseline, ceiling, comp range |
| Trend | FHFA HPI | Trend modifier |
| Supply | Redfin Data Center | Differentiator / DOM / scarcity |
| Condition | Photo analysis + user confirmation | Repair candidates |

---

## Carrying cost

- Calculated in **days**: total monthly carrying cost ÷ 30
- Required: total monthly mortgage payment, HOA if applicable, target list date, sale timeline
- DOM source priority: Redfin median DOM → ATTOM sold DOM → documented fallback

---

## DIY boundary (PRD §18)

DIY **not advised** when: permit/inspection required, licensed trade required, structural/load-bearing, health/safety risk, or warranty/liability risk.

Examples not advised: knob-and-tube, foundation, active water intrusion, mold &gt;10 sqft, roof replacement, septic, HVAC replacement, gas line.

Conditional: fixtures, windows, gutters, attic insulation, deck boards.

---

## Regression and model consumption (Decisions Log V12 / Model Registry v1)

### Hard rule

Product may consume coefficients only when artifact is:
- Versioned and structurally valid
- `status == "approved"` **and** `approved_for_recommendations == true`
- Manually approved via decision record

### Calibration states

| State | Seller-facing use? |
|---|---|
| Pipeline-runnable | No |
| Diagnostic (`diagnostic_only`) | No |
| Candidate | No |
| Approved recommendation model | Yes (with approval flag) |
| Retired / rejected | No |

### Greenville v0.1 current status

| Item | Value |
|---|---|
| Path | `model_registry/greenville_sc/hedonic_ppsf_v0_1.json` |
| Status | `diagnostic_only` |
| approved_for_recommendations | `false` |
| test_r2 | ~0.09 |
| Validator | PASS 11/11 (structural only) |
| **Recommendation use** | **Prohibited** |

Numeric features were **standardized** before Ridge fit — coefficients are not raw-dollar effects.

### ATTOM sale_date mapping (D-V12-001)

Export mapper fallback order:
1. `sale.saleTransDate`
2. `sale.salesearchdate`
3. `sale.amount.salerecdate`

**Rejected:** `sale.amount.saletransdate` (produced blank dates in 12-metro package)

---

## Comp recency (PRD v0.8)

1. Primary: 5–10 comps within **90 days**
2. If &lt;3 qualifying comps: broaden to **180 days**
3. If still &lt;3: limited-data handling + zip-level Redfin median fallback

---

## Source references

- `docs/product/raw/Property_ROI_Analysis_Tool_PRD_v0_8.docx`
- `docs/product/raw/Property ROI Analysis Tool — Technical Specification V4`
- `docs/product/raw/Seed Tables.xlsx`
- `docs/product/raw/Duration_Lead-Time Seed Table v1.0`
- `docs/product/raw/Dependency Rules v1.0 Addendum`
- `docs/product/raw/Recommendation Anomaly Rules v1.0`
- `docs/product/raw/Property_Attribute_Hedonic_Matrix_v2.xlsx`
- `docs/product/raw/Regression Model Registry and Promotion Governance v1.docx`
- `docs/product/raw/Decisions Log V12.docx`
