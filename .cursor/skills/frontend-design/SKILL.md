---
name: frontend-design
description: Improves ROI Tool screen-level UI polish — layout hierarchy, intake flow, address landing, responsive design, and product-specific visuals. Use when redesigning intake screens or seller-facing pages in the ROI Tool repo.
---

# ROI Tool Frontend Design

## Product feel

Calm, polished, editorial, seller-facing — **sharp advisor**, not software dashboard. National product; no local market hardcoding in UI.

## Avoid

- Generic SaaS dashboard layouts (dense sidebars, metric tiles, chart junk)
- Simpsonville Analyzer UI patterns
- Stock house photography or real property photos
- Prototype feel (bare forms on empty pages, tiny wordmarks, weak hierarchy)
- Overdesigned marketing fluff

## Prefer

- Centered, intentional composition with generous whitespace
- Strong typography hierarchy: display headline → body lede → panel content → fineprint
- Form inside `.intake-panel` card with stone border and soft shadow
- Mobile-first; elegant two-column split on desktop (form + visual panel)
- Product-specific imagery from `partials/_intake_visuals.html` and `visual-system.css`:
  - Stylized plan preview cards
  - Timeline/checklist motifs
  - Source chips and blueprint grid texture
  - Line SVG icons (parcel, check, skip, clock)

## Intake layout pattern

```
.topbar (wordmark + step indicator)
.intake-page
  .intake-layout[--split|--solo]
    .intake-main (intro + panel + optional value row)
    aside.intake-visual (decorative preview, aria-hidden)
```

## Address entry must include

- Quiet product mark in topbar
- Hero headline + one-sentence value prop
- Address form in panel with `.form-label`, helper text, CTA
- Trust/support line inside panel
- Optional 3-item “what you get” row
- Plan preview visual (right/below)

## Issue picker

Organize with fieldsets/legends (Water & moisture, Systems, Exterior & wear) — not a random flat grid.

## States to polish

- Validation errors (`.field-error`)
- Autocomplete unavailable (helper text, not secrets)
- Confirm address with record chips
- Building screen with status lines + animated preview

## Stack constraints

FastAPI + Jinja + tokenized CSS only. No build step. Keep Railway deployability (`Procfile`, env vars).
