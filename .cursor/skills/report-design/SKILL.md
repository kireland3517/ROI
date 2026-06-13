---
name: report-design
description: Guides Seller Action Plan report structure, section hierarchy, action cards, and market context presentation in the ROI Tool. Use when editing report templates or report CSS.
---

# ROI Tool Report Design

The report is a **single-scroll decision document** — mobile-first, strong section hierarchy, timeline horizon as signature element.

## Required sections (in order)

1. **Report header** — title, address, date, assumption chips (compact)
2. **Executive verdict** — headline + supporting body from engine
3. **Plan at a Glance** — fact grid; national cost ranges, not value estimates
4. **Property facts and confidence** — beds/baths/sqft/year + source chips + warnings for fallback/partial
5. **What you told us** — goal, timeline, spend, issues/custom note from `plan.context`
6. **Local market context** — presentation-only; comp stats when available
7. **Top recommended actions** — horizon timeline with action cards
8. **Also worth doing** — lower-priority items (`plan.additional_items`)
9. **Beyond Your Timeline** — feasible-if-you-wait items
10. **Do Not Spend** — low-return / not-recommended items
11. **Assumptions and confidence** — explain timing/spend/condition/facts assumptions
12. **Next steps** — ordered list from engine
13. **Disclaimer** — legal boundary copy

## Action cards

Use `action_card` macro in `partials/_macros.html`. Each card shows:

- Title, cost band, timeline status (dot + label)
- Tier badge, DIY/contractor flag
- Source/confidence chips
- Expandable: citations, effort/duration, skip risk (existing data only)

Do **not** invent ROI, resale lift, ARV, or “value added” claims.

## Local market context

From `partials/_market_context.html` — safe presentation only:

- Comp count, median sale, middle-50% band, median $/sqft, data-through date
- Support/confidence label
- Explicit “context only, not a value estimate” language

Market context must **not** influence recommendations (engine rule unchanged).

## Visual treatment

- Section headings: `h2` with `.section-sub` helper line
- Wrap major blocks in `.report-section-panel` where helpful
- Horizon: brass rail (`--horizon`) with numbered sequence markers
- Do Not Spend: muted/strike treatment, not alarm-red dashboard
- No 13-column tables; use `.facts-row` flex facts

## Banned in seller copy

ARV, after-repair value, expected return, “your home is worth”, resale value claims, regression/tier jargon, market city names in copy.
