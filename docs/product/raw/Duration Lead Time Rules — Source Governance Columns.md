# Duration Lead Time Rules — Source Governance Column Expansion

## Purpose

This artifact documents the non-destructive expansion of the authoritative `ROI Tool` → `Seed Tables` Google Sheet, tab `Duration Lead Time Rules`, so each timing rule can support row-level source governance for final seed-table approval.

The current sheet has a single `source_reference` column. That column mixes URLs, generic source labels, and reviewer caveats. This is not sufficient for final approval because each duration/lead-time row needs auditable provenance: source name, URL, access date, extracted evidence, and reviewer notes.

## Proposed Column Model

The update preserves all existing values by renaming the current `source_reference` column to `legacy_source_reference`, then adding new auditable fields immediately before `version`.

| Column | Field | Purpose | Initial population rule |
|---|---|---|---|
| I | `legacy_source_reference` | Preserves the exact pre-existing source/caveat text. | Existing `source_reference` values retained exactly. |
| J | `source_name` | Controlled source-family value for reviewer filtering. | Derived from existing URL/domain where clear; otherwise set to a conservative descriptive status. |
| K | `source_url` | Exact URL used for row-level citation. | Populated only when the legacy value is an explicit URL. |
| L | `access_date` | Date the reviewer accessed or verified the source. | Left blank unless the existing row already contained a sufficiently precise access date. |
| M | `source_excerpt` | Short source quotation or paraphrased timing statement supporting the row. | Left blank for reviewer completion. |
| N | `review_notes` | Caveats, scope mismatch, reviewer judgment, or action needed. | Populated with the legacy caveat where the legacy value is not an explicit URL. |
| O | `version` | Existing seed-table version value. | Existing values moved right unchanged by column insertion. |

## Controlled Values

The following dropdown values are appropriate for `source_name`.

| Value | Intended use |
|---|---|
| `Angi` | Source URL is an Angi page. |
| `HomeAdvisor` | Source URL is a HomeAdvisor page. |
| `Angi/HomeAdvisor` | Existing evidence only names the source family without a row-level URL. |
| `No single-source baseline` | Current value is an estimate/caveat rather than a citation. |
| `Expert review required` | Row requires contractor, GC, inspector, or product-owner review before approval. |
| `Other` | Valid source outside the above controlled values. |
| `TBD` | Source not yet identified. |

The `access_date` field should be completed using ISO format `YYYY-MM-DD` after a reviewer actually opens or verifies the cited source. The update does not fabricate access dates.

## Validation Scope

Strict dropdown validation should be applied to `source_name`. The existing strict dropdowns for `review_status` and `decision_reference` should be shifted to their new locations by the Google Sheets column insertion behavior and then re-applied explicitly if needed.

The `source_url`, `source_excerpt`, and `review_notes` fields should remain free text because they are evidence fields. `source_url` should ideally contain complete URLs, but Google Sheets data validation for URLs is not applied in this pass to avoid blocking non-URL rows that still need manual source discovery.

## Applied Workbook Changes — 2026-06-04

The authoritative **Seed Tables** workbook in the Google Drive **ROI Tool** folder was updated on the **Duration Lead Time Rules** tab. The former single `source_reference` area was expanded into row-level governance fields while preserving the original source text in a legacy column.

| Column | Header after update | Purpose |
|---|---|---|
| I | `legacy_source_reference` | Preserves the original source-reference value exactly enough for audit continuity. |
| J | `source_name` | Controlled source-family label such as `Angi`, `HomeAdvisor`, `Angi/HomeAdvisor`, `No single-source baseline`, `Expert review required`, `Other`, or `TBD`. |
| K | `source_url` | Exact source URL where one exists. |
| L | `access_date` | Date the reviewer accessed and verified the source. This remains blank for reviewer completion. |
| M | `source_excerpt` | Short supporting excerpt or paraphrased timing statement. This remains blank for reviewer completion. |
| N | `review_notes` | Caveats, scope mismatches, or evidence limitations. Non-URL legacy notes were copied here for reviewer continuity. |
| O | `version` | Existing version column preserved after the inserted governance columns. |

The `source_name` column now has strict dropdown validation for the controlled labels above. Existing URL rows were classified as `Angi` or `HomeAdvisor` based on the source domain. Rows with narrative caveats rather than specific URLs were classified as `No single-source baseline` and the legacy note was copied into `review_notes`.

The workbook now supports the row-level citation workflow needed for final seed-table approval, but it does not complete the underlying source review. The remaining product-owner/data-reviewer task is to fill `access_date`, `source_excerpt`, and any additional `review_notes`, then promote each row’s `review_status` only when the evidence is acceptable.

## Verification

A post-update readback confirmed the following header sequence on the authoritative tab:

| Position | Header |
|---|---|
| A | `rule_id` |
| B | `repair_type` |
| C | `duration_low_days` |
| D | `duration_high_days` |
| E | `lead_time_low_days` |
| F | `lead_time_high_days` |
| G | `review_status` |
| H | `decision_reference` |
| I | `legacy_source_reference` |
| J | `source_name` |
| K | `source_url` |
| L | `access_date` |
| M | `source_excerpt` |
| N | `review_notes` |
| O | `version` |

The source-governance update was applied only to the authoritative `Seed Tables` workbook located in the Google Drive `ROI Tool` folder.
