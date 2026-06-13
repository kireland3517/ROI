# Report Structure

Synthesized from PRD v0.8 §§10–11 and Recommendation Anomaly Rules v1.0 (staging copy draft).

## Report types

| Type | Audience / tone |
|---|---|
| Homeowner Report | Plain language; DIY vs contractor; Top 5 + carrying-cost summary |
| Agent Report | More formal client-facing; Phase 2 may add branding |
| Investor Rehab Report | Cost, ceiling, margin, structural risk, price-per-square-foot |

## Required output sections (PRD)

| Section | Contents |
|---|---|
| Property Summary | Address, specs, AVM, tax assessed value, equity (where available), comp range, data freshness |
| Market Snapshot | Price/sqft, DOM, trend, buyer profile, neighborhood ceiling, active supply, supply velocity |
| Condition Assessment | Photo-based and user-confirmed condition summary |
| Seller ROI Action Plan | **Top 5** sequenced recommendations with rationale |
| Full Improvement List | Full ranked/sequenced list: costs, ROI, DOM, dependencies, timeline feasibility, anomaly callouts |
| Do Not Spend List | Improvements recommended against, with explanation |
| Beyond Your Timeline | High-value items that do not fit stated sale timeline |
| Carrying Cost Analysis | Daily carrying cost, DOM scenarios, cost-of-waiting |
| Risk Notes | Tier 1 unresolved risks, over-improvement flags, missing-data notes, legal/disclosure warnings |
| Uniqueness Factors | Scarcity/uniqueness signals when toggle is on |
| Photography & Presentation | Photography, staging, 3D tour, presentation recommendations |
| Next Steps | 3–5 concrete actions by goal and timeline |
| Disclaimer | Required legal language |

## Action plan structure within the report

The Seller ROI Action Plan is not a flat ranked list. User sees:

1. **Top 5 Actions** summary
2. Full sequenced action plan
3. **Beyond Your Timeline**
4. **Do Not Spend** — including items that may tempt the seller but do not fit property, timeline, market, ceiling, or buyer segment

## Line-item fields (per recommendation)

| Field | Description |
|---|---|
| improvement | Specific recommended action |
| tier | Critical / deferred maintenance / cosmetic-value-add |
| diy_materials_cost | Materials-only range where DIY reasonable |
| contractor_total | Full project cost range |
| diy_recommended | Yes / No / Conditional |
| diy_not_advised_reason | When DIY not recommended |
| permit_required | Yes / No / Unknown |
| estimated_resale_lift | Sale-price impact range; supply-modulated where supported |
| roi_diy / roi_contractor | ROI by execution path |
| dom_impact | +1 / 0 / -1 |
| dom_penalty_if_skipped | Carrying-cost and offer-quality implication |
| dependency_notes | Upstream/downstream sequencing |
| timeline_feasibility | Fits user timeline or not |
| contractor_lead_time_note | Static or data-fed risk note |
| priority_rank | Rank within sequenced plan |
| anomaly_callout | Inline explanation when signals conflict or data limited |

## Timeline status labels (Tech Spec V4 alignment)

Recommendations should communicate: **urgent**, **feasible**, **constrained**, **beyond timeline**, or **not recommended**.

## Confidence and model language

- Distinguish empirical, static assumption, owner-approved, expert-validated, placeholder, or approved-model basis
- Do **not** present diagnostic regression coefficients as valid value-uplift estimates
- Seller-facing copy must not expose model internals, coefficients, or registry status

## Approved anomaly: professional staging under 21 days

**Rule ID:** `ANOM-STAGING-UNDER-21-DAYS`  
**Trigger:** Professional staging recommended AND `target_list_date - current_date < 21` calendar days  
**Behavior:** Does not automatically remove staging; marks timeline risk; show callout on line item

**Draft user-facing copy** (not final — OQ-ANOM-001 / UX-legal review open):

> **Timeline risk:** Professional staging often requires advance scheduling. Because your target list date is less than 21 days away, staging may still be worthwhile, but availability could limit whether it can be completed before listing. Consider calling stagers immediately or using a faster partial-staging/photo-prep alternative.

## Data-first anomaly types (PRD framework)

| Type | Example trigger |
|---|---|
| Valuation conflict | AVM, comps, tax assessment materially disagree |
| Limited comp data | Fewer than 3 qualifying comps after 90-day → 180-day hierarchy |
| Supply-price contradiction | Low supply vs generic over-improvement logic |
| Condition mismatch | User overall condition vs confirmed photo findings |
| Timeline infeasibility | Project cannot complete before target list date |
| Fallback-driven calculation | Metric uses fallback constants |

Anomalies must be **inline** on affected recommendations; not hidden when material.

## Layout requirements

| Platform | Requirement |
|---|---|
| Mobile | Wizard-style intake; summary-card report; **no** forced 13-column table |
| Desktop | Full form and full report |
| Cross-device | UUID session persistence |

## Export formats

| Format | Phase |
|---|---|
| On-screen interactive report | Phase 1 (MVP primary) |
| PDF export | Phase 2 |
| Agent branding (name, brokerage, logo) | Phase 2 |

## Freshness labeling

Every time-sensitive section shows **source date or freshness**, not only report generation date (ATTOM query date, Redfin period end, FHFA file date, coefficient set version, etc.).

## Legal disclaimer (required before external use)

> This tool provides estimates and recommendations for informational purposes only. It does not constitute a professional property inspection, appraisal, or legal advice. Output does not create, fulfill, or substitute for seller disclosure obligations under applicable state law. This tool does not constitute a home inspection under any state's home inspection licensing statute. Output does not represent a licensed inspection or the findings of a licensed home inspector in any jurisdiction. Consult a licensed inspector, appraiser, and/or real estate attorney before making decisions based on this analysis.

Attorney review is a **required public-release gate** (national, risk-based framing).

## Source references

- `docs/product/raw/Property_ROI_Analysis_Tool_PRD_v0_8.docx` — §§9–11, 14, 17
- `docs/product/raw/Recommendation Anomaly Rules v1.0`
- `docs/product/raw/Property ROI Analysis Tool — Technical Specification V4` — §§18–19
