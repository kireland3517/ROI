---
name: design-system
description: Defines and enforces the ROI Tool visual system — slate-blue palette, typography, spacing, components, and tokens. Use when editing CSS, templates, or UI in the Property ROI Analysis Tool (ROI Tool repo).
---

# ROI Tool Design System

Apply this skill for all seller-facing UI in the ROI Tool (`app/static/css/`, `app/templates/`). Do not use Simpsonville Analyzer patterns.

## Palette (token names in `tokens.css`)

| Token | Hex | Role |
|---|---|---|
| `--field` | `#3F5F73` | Primary slate blue — buttons, links, selection, focus |
| `--field-deep` | `#243B4A` | Hover, pressed, emphasis text |
| `--field-tint` | `#DDE7EC` | Soft blue-gray backgrounds, focus rings |
| `--paper` | `#F7F4EE` | Page ground |
| `--paper-raised` | `#FFFCF8` | Cards, panels, inputs |
| `--stone` | `#D8C9B4` | Warm borders, structure |
| `--ink` | `#17232B` | Primary text |
| `--ink-muted` | `#556872` | Secondary text (≥4.5:1 on paper) |
| `--horizon` | `#B8935A` | Muted gold/brass — **timeline rail and date markers only** |
| `--caution-tint` | `#FFF4D8` | Warning cream backgrounds |

Status: `--urgent`, `--urgent-tint`, `--caution` for errors and warnings.

## Rules

- **No ad hoc hex colors** in component CSS — consume tokens only.
- **Brass/gold (`--horizon`)** is reserved for timeline horizon UI, not general accents.
- **Forest green is retired** — use slate blue primary system.
- Typography: `--font-display` (headings/UI), `--font-body` (prose), `--font-utility` (data, chips, mono labels).
- Spacing: `--sp-*` scale (4px base). Prefer `--sp-6`/`--sp-8` for section rhythm.
- Radius: `--radius-sm`, `--radius`, `--radius-lg`.
- Shadows: `--shadow-soft`, `--shadow-panel` only.

## Components

- **Buttons**: `.btn`, `.btn--primary`, `.btn--full`; slate fill, deep slate hover; never brightness-only hover.
- **Inputs**: stone border, slate focus ring (`box-shadow: 0 0 0 3px var(--field-tint)`).
- **Cards**: `.card`, `.intake-panel`, `.report-section-panel` — raised paper, stone border, panel shadow.
- **Chips**: `.chip`, `.chip--answer`, `.chip--records`, `.chip--estimate`, `.chip--assumed` — always dot + label; never color-only meaning.
- **Warnings**: `.warning`, `.field-error` — caution cream + left border + text label.
- **Status**: `.status`, `.status--urgent`, `.status--feasible`, etc. — dot + text label.
- **Focus**: `:focus-visible` with `--field` outline; inputs use border + tint ring.

## File map

- `app/static/css/tokens.css` — single source of truth
- `app/static/css/base.css` — reset, type, buttons, inputs
- `app/static/css/components.css` — chips, cards, status, warnings
- `app/static/css/intake.css` — intake layout
- `app/static/css/visual-system.css` — decorative product imagery
- `app/static/css/report.css` — report sections and horizon
