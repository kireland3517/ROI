# Project Checklist

> Renamed from `walkthrough-checklist.md` (June 2026): this file is the operational **project tracker**, not a property walkthrough. The name collided with the seller-facing walkthrough concept.

Condensed from `Master Running Checklist V1.docx` and `Static Data Source Register and Download Checklist V2.docx`. This is an operational tracker — governing artifacts (PRD, Decisions Log, Tech Spec) still take precedence on conflicts.

**Status values:** Not Started | In Progress | Blocked | Ready for Review | Done | Deferred | Rejected

**Controlling question:** What should this seller spend money on, in what order, and why?

---

## Executive status (June 2026)

| Area | Status | Next move |
|---|---|---|
| Product definition | Mostly stable (PRD v0.8) + D-V13 decisions | Keep PRD unless owner changes scope |
| Decisions governance | Current through V13 | Use V13 for scope/intake/seed-handoff topics; V12 for regression |
| Technical specification | V4 exists in raw exports | Confirm V4 as governing spec; close remaining gates |
| Sequencer seed data | Partially ready, gated | Source citations, expert validation; CSV handoff format decided (D-V13-003) |
| Regression pipeline | Runnable, not product-approved | Promotion checker, diagnostics, refusal tests (refusal loader shipped in first build slice) |
| First build slice | In Progress | Walking skeleton: progressive intake → ATTOM facts → Tier-1 starter report |
| Legal / UX | Open | Staging copy, disclaimers, public-release review |

---

## Immediate priorities (ordered)

| # | Item | Status | Owner | Blocked until |
|---|---|---|---|---|
| 1 | Confirm Technical Specification V4 as governing technical spec | Ready for Review | Product/technical architect | — |
| 2 | Finalize row-level source URLs and access dates for duration/lead-time rows | Open / Blocked | Product owner / data reviewer | Final seed-table approval |
| 3 | Obtain GC/remodeling PM expert validation for dependency rules | Open / Blocked | Construction reviewer | Sequencer coding |
| 4 | Decide authoritative seed handoff format (xlsx vs CSV vs DB migration) | **Done — D-V13-003 (versioned CSV)** | Product owner / architect | — |
| 5 | Export full dependency matrix to normalized seed rows | Not Started | Product/technical architect | Sequencer coding |
| 6 | Resolve accessibility subtype alignment across catalog, DOM, dependency, duration, UI | Open | Product architect | Catalog finalization |
| 7 | Finalize staging under-21-days anomaly user-facing copy | Open | UX / legal | Public report output |
| 8 | Add regression promotion-readiness checker | Not Started | Modeling reviewer / engineer | Any model approval discussion |
| 9 | Define provisional model-promotion thresholds | Open | Architect / modeling reviewer | Any model marked candidate |
| 10 | Add recommendation-engine refusal tests for unapproved artifacts | **In Progress — first build slice** | Engineer / QA | Coefficient integration |

---

## Product and scope

| Item | Status | Classification |
|---|---|---|
| Central MVP question preserved | Done / Ongoing | MVP |
| Goals: Sell, Flip, Refinance only | Done | MVP |
| Output: Top 5, full plan, Beyond Timeline, Do Not Spend | Defined | MVP |
| Tier 1 priority rules | Defined | MVP |
| Budget/risk as inferred (PRD) | **Resolved — D-V13-001 (spend-comfort band at start)** | MVP |
| National scope; Simpsonville Analyzer reference-only | **Done — D-V13-002** | MVP |
| Active supply / scarcity in Phase 1 | Defined | MVP |
| PDF, branding, seasonal demand, HOA expansion, multi-unit | Deferred | Phase 2 |
| MLS, contractor data, energy module | Deferred | Phase 3 |

---

## Seed tables and sequencer

| Item | Status | Acceptance criteria |
|---|---|---|
| Duration row-level citations | Open / Blocked | No row relies only on generic source names |
| Duration review status finalization | Open | Reflects actual governance confidence |
| Accessibility subtype split preserved | Done / Ongoing | Subtypes remain separate |
| DOM impact for accessibility subtypes | Open | No taxonomy mismatch |
| Seed Tables.xlsx → executable handoff | **In Progress — CSV export under `app/seeds/` (D-V13-003)** | Row IDs, subtypes, review metadata preserved |
| Starter catalog seed (Tier-1 + listing-readiness) | **In Progress — `proposed_pending_source_QA` until owner approves** | National ranges, no market literals |
| Full dependency matrix export | Not Started | All sequencer repair types covered |
| Expert dependency validation | Open / Blocked | Reviewer, date, exceptions recorded |
| Staging anomaly seed row | Not Started | Fires at &lt;21 days with staging recommended |
| Staging anomaly copy | Open | Clear warning, not absolute |
| Seed-table validation tests | **In Progress — first build slice** | Fail on missing rows/statuses |

---

## Regression and model governance

| Item | Status |
|---|---|
| ATTOM sale_date mapping preserved | Defined — needs implementation QA |
| sale_date coverage validation before regression | Not Started |
| Greenville smoke fixture retained | Done / Ongoing |
| Cursor regression files committed for review | Not Started |
| Promotion-readiness checker | Not Started |
| Provisional promotion thresholds | Open |
| Greenville diagnostics (residuals by segment) | Not Started |
| Target choice comparison (log ppsf vs log sale amount) | Open |
| Recommendation-engine refusal logic | **In Progress — `app/registry.py` refusal loader + tests in first build slice** |
| Full 12-metro repull | Deferred by D-V12-006 |
| Seller-facing Greenville v0.1 coefficients | **Rejected** |

---

## Data sources and APIs

| Item | Status |
|---|---|
| Smarty address validation + confirmation gate | **In Progress — stub adapter behind interface; credentials open (PRE-API-001)** |
| ATTOM adapter with source logging | **In Progress — property-facts adapter with fallback UX in first build slice** |
| Comp recency hierarchy (90d → 180d → limited data) | Defined — needs implementation |
| Redfin weekly ingestion + 24h derived cache | Defined — needs implementation |
| Freshness labels on reports | **In Progress — provenance chips in first build slice** |
| Enriched ATTOM field audit | Open |
| Source register kept current | Ongoing |
| OEWS files identified and downloaded | Open |
| Redfin source file + market-key mapping | Open |
| ACS table list selected | Open |
| FEMA flood strategy selected | Open |
| SchoolDigger access method selected | Open |
| Walk Score API + cache policy | Open |
| Hedonic workbook extraction to seed tables | Open |

### Readiness gates (from Source Register V2)

| Gate | Status |
|---|---|
| RG-SEQ-006 source register merge | **Closed** |
| Dependency rules GC/PM validated | **Open — build blocker (sequencer only; starter report does not sequence dependencies)** |
| Duration/lead-time row-level source QA | Conditionally open |
| Recommendation anomaly rules seeded | Open |
| Accessibility taxonomy aligned | Open |
| Legal disclaimer templates reviewed | Release blocker |

---

## UX, report, and legal

| Item | Status |
|---|---|
| Intake: PRD vs progressive disclosure strategy | **Resolved — D-V13-001 (Intake Strategy V1 adopted)** |
| Progressive 4-question intake + issue picker | **In Progress — first build slice** |
| Starter report (verdict, Top 5, Do Not Spend, Beyond Timeline, Next Steps, disclaimer) | **In Progress — first build slice** |
| Guided room-by-room photo flow | Defined — deferred to later slice (D-V13-001) |
| Finding-level confirm/dismiss/add | Defined — deferred with photo flow |
| Severity not in vision output | Defined — needs implementation (photo slice) |
| Required disclaimer in UI and reports | Draft in starter report, labeled "pending legal review" — legal review open |
| Staging anomaly copy legal/UX review | Open |

---

## Maintenance rule

Update this checklist in the same session when items complete, block, defer, or reject. Do not create new checklist versions unless structure changes materially.

---

## Source references

- `docs/product/raw/Master Running Checklist V1.docx`
- `docs/product/raw/Static Data Source Register and Download Checklist V2.docx`
- `docs/product/raw/Source Register V2 Merge Findings.docx`
