"""Intake flow configuration (D-V13-001 progressive intake).

One question per screen. Every question explains why it's asked and what
happens if it's skipped — sensitive or high-effort input is never demanded
before its value is explained (Intake Strategy V1 product rule).
"""

from __future__ import annotations

QUESTION_ORDER = ["objective", "timing", "spend"]

QUESTIONS = {
    "objective": {
        "step": 1,
        "field": "objective",
        "title": "What are you planning to do?",
        "why": "We ask because your goal changes what's worth doing.",
        "skippable": False,
        "options": [
            {
                "value": "sell_soon",
                "label": "Sell soon",
                "desc": "I want to list quickly and avoid surprises.",
            },
            {
                "value": "highest_net",
                "label": "Sell for the highest net",
                "desc": "I have some flexibility and want the best outcome.",
            },
            {
                "value": "evaluate_flip",
                "label": "Evaluate a flip",
                "desc": "I'm weighing this property as an investment.",
            },
            {
                "value": "refinance",
                "label": "Refinance",
                "desc": "I want the property to appraise well.",
            },
        ],
    },
    "timing": {
        "step": 2,
        "field": "timing_band",
        "title": "When do you want to list?",
        "why": "Your timeline decides what's realistic — and what we'll tell you to skip.",
        "skippable": True,
        "skip_value": "unsure",
        "skip_label": "I'm not sure yet",
        "skip_note": "We'll plan for 3–6 months — you can change this anytime.",
        "allow_date": True,
        "options": [
            {"value": "under_30", "label": "Within 30 days", "desc": "Time to triage, not renovate."},
            {"value": "m1_3", "label": "1–3 months", "desc": "Room for repairs and presentation."},
            {"value": "m3_6", "label": "3–6 months", "desc": "Room for a fuller plan."},
            {"value": "m6_plus", "label": "6+ months", "desc": "No rush — plan deliberately."},
        ],
    },
    "spend": {
        "step": 3,
        "field": "spend_band",
        "title": "How much are you comfortable spending?",
        "why": "This sizes your plan. We'll never push you past your comfort — and we'll tell you what not to spend on.",
        "skippable": True,
        "skip_value": "unsure",
        "skip_label": "I'm not sure yet",
        "skip_note": "No problem — we'll show costs for everything and you choose what fits.",
        "options": [
            {"value": "under_1k", "label": "Under $1,000", "desc": "Essentials only."},
            {"value": "b1_5k", "label": "$1,000–$5,000", "desc": "Essentials plus quick wins."},
            {"value": "b5_15k", "label": "$5,000–$15,000", "desc": "A fuller pre-listing budget."},
            {"value": "b15k_plus", "label": "$15,000+", "desc": "Open to bigger projects if they pay."},
        ],
    },
}


def next_step(current: str) -> str | None:
    idx = QUESTION_ORDER.index(current)
    if idx + 1 < len(QUESTION_ORDER):
        return QUESTION_ORDER[idx + 1]
    return None


def answer_label(step_key: str, value: str) -> str | None:
    """Human label for a stored answer value, or None if unset."""
    if not value:
        return None
    config = QUESTIONS.get(step_key)
    if config is None:
        return None
    if value == config.get("skip_value"):
        return "Not set yet"
    for opt in config["options"]:
        if opt["value"] == value:
            return opt["label"]
    return None
