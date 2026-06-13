---
name: accessibility-review
description: Reviews ROI Tool UI for accessibility — focus, contrast, labels, ARIA, motion, and semantic structure. Use after intake or report UI changes in the ROI Tool repo.
---

# ROI Tool Accessibility Review

Run this checklist after UI changes.

## Keyboard & focus

- [ ] All interactive elements reachable by Tab
- [ ] `:focus-visible` clearly visible (slate outline + input tint ring)
- [ ] `details`/`summary` action cards operable by keyboard
- [ ] Skip/secondary actions don't trap focus

## Labels & semantics

- [ ] Every input has visible `<label>` or `aria-label` (not placeholder-only)
- [ ] One `h1` per page; section `h2` hierarchy in report
- [ ] Decorative visuals use `aria-hidden="true"`
- [ ] Errors use `role="alert"`; status warnings use `role="status"`

## Autocomplete / listbox

Address typeahead (`intake.js`):

- [ ] `role="combobox"` on input
- [ ] `aria-expanded`, `aria-controls`, `aria-autocomplete="list"`
- [ ] `role="listbox"` on suggestions; `role="option"` on items
- [ ] `aria-activedescendant` during arrow-key navigation
- [ ] Escape closes list; Enter selects active option

## Color & status

- [ ] Text contrast ≥ 4.5:1 on paper (ink-muted on paper is token-checked)
- [ ] Status never color-only — always dot + text label (`.status`, `.chip`)
- [ ] Urgent/feasible/constrained distinguishable without color alone

## Motion

- [ ] `prefers-reduced-motion: reduce` disables animations (fade-slide, reveal-stagger, building pulse)
- [ ] No essential information in animation-only reveals

## Mobile

- [ ] Readable type at 320px width
- [ ] Touch targets ≥ 44px for primary CTAs where possible
- [ ] No horizontal scroll on intake/report

## Report

- [ ] Section `aria-labelledby` on major `<section>` elements
- [ ] Chip explainers usable (click/tap for `data-explainer` popovers in `report.js`)

Fix issues in CSS/markup — do not remove ARIA to simplify tests.
