# Open Questions

Consolidated from `Open Questions Log V1`, `Regression Open Questions and Next Actions.docx`, and blocker tables in Technical Specification V4. Resolved items are retained for traceability.

---

## Recently resolved

| ID | Question | Resolution | Decision ref | Affected areas |
|---|---|---|---|---|
| OQ-SEQ-001 | Split accessibility into subtypes vs one conservative range? | Split: minor vs exterior access modifications | D-V11-001 (cited) | Catalog, duration, dependency, Tech Spec |
| OQ-SEQ-002 | Staging anomaly when target list &lt; 21 days? | Yes — timeline-risk anomaly | D-V11-002 (cited) | Anomaly rules, duration, report output |
| OQ-UX-001 | Intake architecture: PRD v0.8 heavy intake vs Intake Strategy V1 progressive disclosure? | Intake Strategy V1 adopted; PRD deep intake becomes optional unlock modules; Smarty gate retained | D-V13-001 | User flow, intake UI, report degradation |
| FU-SRC-003 | Authoritative seed handoff format (xlsx vs CSV vs migration)? | Versioned CSV committed under `app/seeds/`; xlsx remains source workbook | D-V13-003 | Seed tables, seed loader |

---

## Sequencing, seed data, and governance (Open Questions Log V1)

| ID | Question | Why it matters | Owner | Required before | Status |
|---|---|---|---|---|---|
| OQ-DATA-001 | Final source citations, URLs, access dates for each Angi/HomeAdvisor duration/lead-time row? | Seed table must be auditable | Product owner / data reviewer | Final seed-table approval | **Open** |
| OQ-SEQ-003 | Has GC/remodeling PM validated dependency rules and critical-path flags? | Build blocker per Tech Spec / source register | Construction reviewer | Sequencer coding | **Open** |
| OQ-SEQ-004 | Separate DOM-impact rows for accessibility subtypes vs inherit from parent? | Taxonomy alignment across engine tables | Product architect | Catalog finalization | **Open** |
| OQ-ANOM-001 | Exact user-facing copy for staging under-21-days anomaly? | Approved rule exists; copy needs UX/legal review | UX writer / legal | Report-output spec | **Open** |
| OQ-GOV-001 | Mark duration table `approved_by_owner` now vs `proposed_pending_source_QA` until row QA complete? | Affects whether duration table is "complete" in Tech Spec | Product owner | Tech Spec signoff | **Open** |

---

## Regression and model promotion (Regression Open Questions)

| ID | Question | Owner | Priority |
|---|---|---|---|
| RQ-REG-001 | Minimum acceptable model-quality thresholds for MVP promotion? | Product owner + modeling reviewer | High |
| RQ-REG-002 | Required metrics: R², MAE, RMSE, MAPE, CV, residual bias — which are mandatory? | Technical architect | High |
| RQ-REG-003 | Keep `log(price_per_sqft)` as primary target vs compare `log(sale_amount)` with size controls? | Modeling reviewer | High |
| RQ-REG-004 | Acceptable residual-bias thresholds by ZIP, price band, size band? | Product owner + modeling reviewer | High |
| RQ-REG-005 | What condition/renovation/quality proxies can be sourced without excessive cost? | Product + data owner | High |
| RQ-REG-006 | Who may set `approved_for_recommendations: true`? | Product owner | High |
| RQ-REG-007 | File-based registry for MVP vs database tables before launch? | Technical architect | Medium |
| RQ-REG-008 | Is Greenville MVP calibration market or only first smoke-test market? | Product owner | Medium |
| RQ-REG-009 | Repull all 12 metros after diagnostics vs limit to launch markets? | Product owner | Medium |

### Regression immediate next actions (from source)

1. Add promotion-readiness checker → `model_promotion_readiness_report.json`
2. Expand Greenville diagnostics (residuals by segment)
3. Define provisional promotion thresholds
4. Add recommendation-engine refusal tests
5. Review feature gaps before broader data pull

### Explicitly deferred (regression)

- Full 12-metro repull
- Seller-facing coefficient integration
- Automatic model approval
- Final DB schema for model coefficients (file registry sufficient for now)

---

## Product / UX conflicts (unlogged — needs owner decision)

| Topic | Conflict | Sources |
|---|---|---|
| ~~Intake architecture~~ | **Resolved by D-V13-001** — Intake Strategy V1 progressive flow adopted; PRD deep intake → optional modules | PRD v0.8 vs Intake Strategy V1 |
| ~~Budget input~~ | **Resolved by D-V13-001** — spend-comfort band collected at start; "I'm not sure yet" supported with band-grouping degradation | Same |
| Tech Spec V4 status | Master Checklist says "Create V4" Not Started; V4 document exists in raw | Master Checklist vs raw export |

---

## Build prerequisites (first build slice)

| ID | Item | Why it matters | Status |
|---|---|---|---|
| PRE-API-001 | Smarty account/credentials (`SMARTY_AUTH_ID`, `SMARTY_AUTH_TOKEN`) | Address validation gate currently runs on a stub adapter behind the same interface; real USPS standardization requires credentials | **Open** |

---

## Technical Specification V4 blockers

| ID | Blocker | Owner | Required before |
|---|---|---|---|
| B-SEQ-001 | Row-level source URLs/dates for duration/lead-time | Product owner / data reviewer | Final seed approval |
| B-SEQ-002 | Lead-time TBD for accessibility subtype rows | Product owner / data reviewer | Sequencer implementation |
| B-SEQ-003 | Full 30-type dependency matrix → executable seed rows | Product / architect | Sequencer coding |
| B-SEQ-004 | Expert dependency validation | Construction expert | Sequencer coding |
| B-SEQ-005 | Accessibility subtype alignment across all rule tables | Product architect | Recommendation engine |
| B-ANOM-001 | Final staging anomaly copy | UX / legal | Public report |
| B-DATA-001 | Complete Static Data Source Register V2 as full artifact | Product/data owner | Implementation readiness |
| B-REG-001 | Production regression calibration open despite smoke pass | Data/modeling owner | Seller-facing model use |
| B-REG-002 | Promotion thresholds not finalized | Product + modeling | Model approval |
| B-REG-003 | Residual diagnostics incomplete | Data/modeling owner | Promotion review |
| B-REG-004 | Target choice undecided | Data/modeling owner | Model approval |
| B-REG-005 | Condition/quality/micro-location feature sourcing open | Product + data owner | Improved calibration |
| B-REG-006 | Authority to set approval flag not finalized | Product owner | Model promotion |
| B-REG-007 | File vs DB registry architecture | Technical architect | Production hardening |
| B-LEGAL-001 | Public-release legal review | Legal reviewer | Public release |

---

## Source register follow-ups (V2)

| ID | Follow-up | Status |
|---|---|---|
| FU-SRC-001 | Attach final URLs/dates to Angi/HomeAdvisor duration rows | Open |
| FU-SRC-002 | Normalize review-status vocabulary across xlsx/CSV/DB | Open |
| FU-SRC-003 | Authoritative seed handoff format (xlsx vs CSV vs migration) | Open |
| FU-SEQ-001 | GC/PM dependency validation | Open — build blocker |
| FU-SEQ-002 | Accessibility alignment across rule tables | Open |
| FU-ANOM-001 | Staging anomaly runtime seed row + tests | Open |

---

## Logging rule

Add questions here when they need owner, legal, data, expert, or architecture judgment before implementation. When resolved, move to **Recently resolved** with decision/spec reference — do not delete.

---

## Source references

- `docs/product/raw/Open Questions Log V1`
- `docs/product/raw/Regression Open Questions and Next Actions.docx`
- `docs/product/raw/Property ROI Analysis Tool — Technical Specification V4` — §§25–26
- `docs/product/raw/Static Data Source Register and Download Checklist V2.docx` — §11
