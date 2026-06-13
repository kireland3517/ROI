# Source Inventory — Property ROI Analysis Tool

Inventory of every file under `docs/product/raw`, classified by actual content (not filename). Generated June 2026 from Google Drive exports.

## Summary

| Category | Count |
|---|---|
| Total raw files | 22 |
| Important / authoritative | 14 |
| Duplicate or superseded partial export | 4 |
| Outdated relative to newer artifacts | 1 |
| Unclear filename only (content is clear) | 3 |

**Cross-cutting conflict:** `Property_ROI_Analysis_Tool_PRD_v0_8.docx` and `Intake Question Strategy — Low-Friction Progressive Disclosure Specification V1.docx` disagree on required intake fields and when mortgage/payment data is collected. Both are preserved; see `user-flow.md`.

**Note:** Decisions Log V10 and V11 are referenced throughout but are **not** present in `raw/`. Only `Decisions Log V12.docx` is exported here.

---

## File-by-file inventory

### Cursor Regression Implementation Capture.docx

| Field | Value |
|---|---|
| **File type** | Word document (.docx) |
| **Contains** | Owner-reported Cursor implementation status: Greenville model registry artifact paths, validator pass (11/11), intercept 5.2216, `diagnostic_only` / `approved_for_recommendations: false` governance |
| **Product area** | Regression / model registry / implementation status |
| **Assessment** | **Important** — implementation evidence, not independent approval |
| **Feeds into** | `decisions-log.md`, `open-questions.md`, `recommendation-logic.md` (model gating section) |

---

### Decisions Log V12.docx

| Field | Value |
|---|---|
| **File type** | Word document (.docx) |
| **Contains** | Approved decisions D-V12-001 through D-V12-006: ATTOM `sale_date` mapping, Greenville smoke fixture, pipeline-vs-production calibration distinction, model registry artifact pattern, validation/promotion gates, defer 12-metro repull |
| **Product area** | Governance / regression / data quality |
| **Assessment** | **Important** — latest decisions log in this export set |
| **Feeds into** | `decisions-log.md`, `open-questions.md`, `recommendation-logic.md` |

---

### Dependency Rules v1.0 Addendum

| Field | Value |
|---|---|
| **File type** | Markdown (misnamed; extension is `.0 Addendum`) |
| **Contains** | Governance addendum for `dependency_rules` seed family: 13 missing repair types, accessibility subtype handling, per-repair dependency treatment table, required export fields, build-blocker status pending expert validation |
| **Product area** | Sequencer / dependency rules |
| **Assessment** | **Important** — draft; expert validation still required |
| **Feeds into** | `recommendation-logic.md`, `open-questions.md`, `project-checklist.md` |

---

### Duration Lead Time Rules — Source Governance Columns.md

| Field | Value |
|---|---|
| **File type** | Markdown (.md) |
| **Contains** | Column expansion spec for `Duration Lead Time Rules` sheet: `legacy_source_reference`, `source_name`, `source_url`, `access_date`, `source_excerpt`, `review_notes`; applied workbook changes dated 2026-06-04 |
| **Product area** | Seed-table governance / data provenance |
| **Assessment** | **Important** — operational metadata spec for duration rows |
| **Feeds into** | `recommendation-logic.md`, `project-checklist.md` |

---

### Duration_Lead-Time Seed Table v1.0

| Field | Value |
|---|---|
| **File type** | Markdown (misnamed; extension is `.0`) |
| **Contains** | Governed duration/lead-time rows for 13 previously missing repair types + accessibility subtypes (DLT-030A/B), review statuses, sequencer implications |
| **Product area** | Sequencer / duration-lead-time rules |
| **Assessment** | **Important** — overlaps with xlsx exports; markdown is the narrative spec |
| **Feeds into** | `recommendation-logic.md`, `open-questions.md` |

---

### duration_lead_time_rules_v1_0.xlsx

| Field | Value |
|---|---|
| **File type** | Excel workbook (.xlsx) |
| **Contains** | 16-row partial CSV-style export: 13 missing types + accessibility subtypes + replaced broad accessibility row |
| **Product area** | Sequencer / duration-lead-time seed data |
| **Assessment** | **Duplicate (partial)** — subset of `Seed Tables.xlsx` Duration sheet (31 rows) |
| **Feeds into** | `recommendation-logic.md` |

---

### Greenville Coefficient Review Table.xlsx

| Field | Value |
|---|---|
| **File type** | Excel workbook (.xlsx) |
| **Contains** | Human-review spreadsheet for Greenville `hedonic_ppsf_v0_1`: model metadata, preprocessing notes, per-coefficient review rows; `diagnostic_only`, test R² ~0.09 |
| **Product area** | Regression / hedonic calibration / model review |
| **Assessment** | **Important** — review artifact; not product-approved coefficients |
| **Feeds into** | `recommendation-logic.md`, `open-questions.md` |

---

### Intake Question Strategy — Low-Friction Progressive Disclosure Specification V1.docx

| Field | Value |
|---|---|
| **File type** | Word document (.docx) |
| **Contains** | Draft UX spec: 4-question starter intake, progressive modules (Condition Boost, Budget Refinement, Net Proceeds), reject mortgage in starter flow |
| **Product area** | User flow / intake / UX |
| **Assessment** | **Important** — **conflicts with PRD v0.8** on required fields |
| **Feeds into** | `user-flow.md`, `open-questions.md` |

---

### Master Running Checklist V1.docx

| Field | Value |
|---|---|
| **File type** | Word document (.docx) |
| **Contains** | Operational checklist: executive status, immediate priorities, product/scope/tech/seed/regression/data/UX/legal checklists with status values |
| **Product area** | Project operations / readiness |
| **Assessment** | **Important** — primary walkthrough checklist source |
| **Feeds into** | `project-checklist.md`, `open-questions.md` |

**Conflict note:** Checklist item "Create Technical Specification V4" is marked Not Started, but `Property ROI Analysis Tool — Technical Specification V4` already exists in raw.

---

### Open Questions Log V1

| Field | Value |
|---|---|
| **File type** | Markdown (no extension) |
| **Contains** | Sequencing/governance open questions OQ-DATA-001, OQ-SEQ-003/004, OQ-ANOM-001, OQ-GOV-001; resolved OQ-SEQ-001/002 from V11 |
| **Product area** | Governance / open questions |
| **Assessment** | **Important** — partially superseded by regression open questions doc for REG topics |
| **Feeds into** | `open-questions.md` |

---

### Property ROI Analysis Tool — Regression Readiness Action Plan.docx

| Field | Value |
|---|---|
| **File type** | Word document (.docx) |
| **Contains** | Pre-Greenville-smoke plan: states comp training data missing from project folder, prerequisites before regression script, baseline model scope, cleaning rules, output schema |
| **Product area** | Regression readiness |
| **Assessment** | **Outdated** for pipeline status — superseded by Decisions Log V12 and Cursor capture for Greenville path; still useful for general regression prerequisites |
| **Feeds into** | `open-questions.md` (historical context only) |

---

### Property ROI Analysis Tool — Technical Specification V4

| Field | Value |
|---|---|
| **File type** | Markdown (no extension) |
| **Contains** | Consolidated technical spec (~30 sections): architecture, data model, ATTOM mapping, recommendation engine, sequencer, anomaly rules, model registry, readiness gates, blockers, implementation sequence |
| **Product area** | Technical architecture / implementation control |
| **Assessment** | **Important** — supersedes V3 for regression topics; not implementation-ready until gates close |
| **Feeds into** | All organized docs as cross-reference; primary for `recommendation-logic.md`, `project-checklist.md` |

---

### Property_Attribute_Hedonic_Matrix_v2.xlsx

| Field | Value |
|---|---|
| **File type** | Excel workbook (.xlsx) |
| **Contains** | Hedonic seed structure: signal encoding thresholds (UAD/FEMA/Walk Score/etc.), segment signal matrix, placeholder coefficients, calc engine prototype |
| **Product area** | ROI / hedonic / buyer-segment logic |
| **Assessment** | **Important** — Phase 1 placeholder coefficients; extraction to seed tables still needed |
| **Feeds into** | `recommendation-logic.md`, `product-vision.md` |

---

### Property_ROI_Analysis_Tool_PRD_v0_8.docx

| Field | Value |
|---|---|
| **File type** | Word document (.docx) |
| **Contains** | Full PRD: product purpose, user types, data inputs, guided photo flow, market data, cost/ROI/DOM/carrying cost, report sections, APIs, error handling, cache TTL, hedonic governance, anomaly framework, DIY boundaries, build phases, DOM appendix |
| **Product area** | Product vision / requirements (highest product authority in export set) |
| **Assessment** | **Important** — authoritative product requirements |
| **Feeds into** | `product-vision.md`, `user-flow.md`, `report-structure.md`, `recommendation-logic.md` |

---

### Recommendation Anomaly Rules v1.0

| Field | Value |
|---|---|
| **File type** | Markdown (misnamed; extension is `.0`) |
| **Contains** | Approved MVP anomaly `ANOM-STAGING-UNDER-21-DAYS`: trigger, draft copy, engine behavior, seed-table shape |
| **Product area** | Anomaly / timeline warnings |
| **Assessment** | **Important** — rule approved; UX copy still open |
| **Feeds into** | `recommendation-logic.md`, `report-structure.md`, `open-questions.md` |

---

### Regression Model Registry and Promotion Governance v1.docx

| Field | Value |
|---|---|
| **File type** | Word document (.docx) |
| **Contains** | Model registry contract, status values, promotion gates, Greenville v0.1 prohibited-for-recommendations rule, implementation sequence |
| **Product area** | Regression governance / model lifecycle |
| **Assessment** | **Important** — overlaps Tech Spec V4 §12–13; standalone governance artifact |
| **Feeds into** | `decisions-log.md`, `recommendation-logic.md`, `open-questions.md` |

---

### Regression Open Questions and Next Actions.docx

| Field | Value |
|---|---|
| **File type** | Word document (.docx) |
| **Contains** | Regression-specific open questions RQ-REG-001–009, immediate next actions, deferred actions, recommended Cursor promotion-readiness checker task |
| **Product area** | Regression / open questions |
| **Assessment** | **Important** — complements Open Questions Log V1 |
| **Feeds into** | `open-questions.md`, `project-checklist.md` |

---

### Seed Tables.xlsx

| Field | Value |
|---|---|
| **File type** | Excel workbook (.xlsx) |
| **Contains** | Two sheets: **Dependency Rules** (31 rows, mostly `pending`) and **Duration Lead Time Rules** (31 rows with expanded source-governance columns) |
| **Product area** | Executable seed data / sequencer |
| **Assessment** | **Important** — broadest seed workbook; row-level QA and expert validation still open |
| **Feeds into** | `recommendation-logic.md`, `project-checklist.md` |

---

### Source Register V2 Merge Findings.docx

| Field | Value |
|---|---|
| **File type** | Word document (.docx) |
| **Contains** | Short merge report: RG-SEQ-006 closure for addendum merge, Seed Tables.xlsx row counts, relationship to partial CSV export |
| **Product area** | Data governance / source register |
| **Assessment** | **Important (brief)** — merge status memo, not standalone register |
| **Feeds into** | `project-checklist.md` |

---

### Static Data Source Register and Download Checklist V2 Addendum.docx

| Field | Value |
|---|---|
| **File type** | Word document (.docx) |
| **Contains** | Addendum rows for duration/sequencing workpapers, Angi/HomeAdvisor, Decisions Log V11 references, new seed artifacts |
| **Product area** | Data sources / governance |
| **Assessment** | **Duplicate (merged)** — content incorporated into V2 full register |
| **Feeds into** | `project-checklist.md` (via V2 register) |

---

### Static Data Source Register and Download Checklist V2.docx

| Field | Value |
|---|---|
| **File type** | Word document (.docx) |
| **Contains** | Full source register: classification, required seed tables, acquisition checklist (BLS, Redfin, FHFA, ACS, FEMA, APIs), metadata requirements, readiness gates |
| **Product area** | Data sources / implementation prerequisites |
| **Assessment** | **Important** — authoritative data-source inventory |
| **Feeds into** | `project-checklist.md`, `recommendation-logic.md` |

---

### Technical Specification V3 Regression Calibration Addendum.docx

| Field | Value |
|---|---|
| **File type** | Word document (.docx) |
| **Contains** | Regression architecture addendum: sale-date export, Greenville fixture, smoke-test status, model registry — precursor to V4 §12 |
| **Product area** | Technical spec / regression |
| **Assessment** | **Duplicate (superseded)** — consolidated into Technical Specification V4 |
| **Feeds into** | `recommendation-logic.md` (only where V4 does not add detail) |

---

## Organized output files created

| Organized file | Primary raw sources |
|---|---|
| `product-vision.md` | PRD v0.8, Tech Spec V4 §1–3 |
| `user-flow.md` | PRD v0.8 §2–3, Intake Question Strategy V1 |
| `report-structure.md` | PRD v0.8 §10–11 |
| `recommendation-logic.md` | PRD v0.8 §3.4–5, §16–18; seed artifacts; anomaly rules; hedonic matrix; model registry |
| `project-checklist.md` | Master Running Checklist V1, Source Register V2 |
| `decisions-log.md` | Decisions Log V12 |
| `open-questions.md` | Open Questions Log V1, Regression Open Questions, blockers from Tech Spec V4 |
| `source-inventory.md` | This file |

**Not created:** `monetization-gating.md` — no source in `raw` defines pricing tiers, paywalls, or feature gating beyond a single Phase 2 mention of "SKU-level pricing decision" in the PRD build sequence.
