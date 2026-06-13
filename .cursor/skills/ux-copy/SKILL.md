---
name: ux-copy
description: Guides seller-facing copy for the ROI Tool — plain language, sharp advisor tone, trust labels, and safe claims. Use when writing headlines, helper text, errors, chip explainers, or report prose.
---

# ROI Tool UX Copy

## Voice

Plain language. Sharp advisor — direct, helpful, never salesy. Trustworthy over clever.

## Do

- Explain **why** we ask each intake question
- Label every number with its source (Your answer, County records, Standard estimate v1.0)
- Use helper text under inputs (“Start typing a full street address including city and state”)
- Write useful validation errors (“Check the street number and ZIP — we couldn't validate that address”)
- Say “cost range” and “national estimate” — not “price” or “quote”
- Clarify assumptions (“Assumed timing — you can change this”)
- Market context: “context only, not an estimate of your home's value”

## Don't

- Fake precision (“$4,237 ROI”, “+12% resale value”)
- Overclaim (“guaranteed”, “maximize value”, “best investment”)
- Imply unsupported valuation or ROI certainty
- Use jargon: tier, coefficient, regression, diagnostic, hedonic
- Name specific markets in seller-facing copy (Greenville, Simpsonville, etc.)
- Dashboard-speak: “optimize”, “leverage”, “actionable insights”

## Chip explainers (`data-explainer`)

One sentence, concrete:

- **Standard estimate**: “A national cost range we maintain and version — not a contractor quote.”
- **Your answer**: tied to what they told us
- **County records**: “Public assessor/recorder data, via a property data provider.”
- **Assumed**: what we defaulted and how to change it

## Error messages

State what failed, what to try, never blame the user. No internal API names or credential hints.

## Report verdict

Engine-generated headlines only — template must not add value/ROI language around them.
