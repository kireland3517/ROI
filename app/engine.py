"""Deterministic recommendation engine v0 (Tech Spec V4 pipeline, first slice).

Steps implemented: input normalization, candidate generation from the seed
catalog, eligibility filtering, timeline feasibility, tier ordering, Do Not
Spend / Beyond Your Timeline classification, and output assembly with trace
IDs. No model artifacts are consumed (refusal is enforced by app.registry and
tests). No dependency sequencing yet — blocked on expert validation (B-SEQ-004).

Every line item must carry evidence citations and a seed-table trace ID;
output validation rejects anything uncited.
"""

from __future__ import annotations

from datetime import date, timedelta

from app.seeds import CatalogRow, issue_labels, load_catalog

ENGINE_VERSION = "v0"

# Rule IDs persisted in item traces.
RULE_ELIGIBILITY = "ENG-ELIGIBILITY-V0"
RULE_TIMELINE = "ENG-TIMELINE-V0"
RULE_TIER_ORDER = "ENG-TIER-ORDER-V0"
RULE_SPEND_COMFORT = "ENG-SPEND-COMFORT-V0"
RULE_DO_NOT_SPEND = "ENG-DO-NOT-SPEND-V0"

OBJECTIVES = {
    "sell_soon": {"label": "sell soon", "goal": "sell"},
    "highest_net": {"label": "sell for the highest net", "goal": "sell"},
    "evaluate_flip": {"label": "evaluate a flip", "goal": "flip"},
    "refinance": {"label": "refinance", "goal": "refinance"},
}

TIMING_BANDS = {
    "under_30": {"label": "within 30 days", "horizon_days": 30},
    "m1_3": {"label": "in 1\u20133 months", "horizon_days": 90},
    "m3_6": {"label": "in 3\u20136 months", "horizon_days": 180},
    "m6_plus": {"label": "in 6+ months", "horizon_days": 365},
    "unsure": {"label": "in 3\u20136 months (assumed)", "horizon_days": 180},
}

SPEND_BANDS = {
    "under_1k": {"label": "under $1,000", "cap": 1_000},
    "b1_5k": {"label": "$1,000\u2013$5,000", "cap": 5_000},
    "b5_15k": {"label": "$5,000\u2013$15,000", "cap": 15_000},
    "b15k_plus": {"label": "$15,000+", "cap": None},
    "unsure": {"label": "not set yet", "cap": None},
}

TIER_RANK = {
    "critical": 0,
    "deferred_maintenance": 1,
    "listing_readiness": 2,
    "cosmetic_value_add": 3,
}

TIER_BADGES = {
    "critical": "Fix first",
    "deferred_maintenance": "Buyers will flag it",
    "listing_readiness": "Get ready to list",
    "cosmetic_value_add": "Nice to have",
}

STATUS_LABELS = {
    "urgent": "Do now",
    "feasible": "Fits your timeline",
    "constrained": "Tight \u2014 start immediately",
    "beyond": "After your date",
    "not_recommended": "Skip this",
}

DIY_LABELS = {
    "yes": "DIY-friendly",
    "no": "Hire a pro",
    "conditional": "DIY with care",
}

DURATION_BAND_LABELS = {
    "hours": "A few hours of work",
    "days": "A few days",
    "week": "About a week",
    "weeks": "1\u20133 weeks",
    "month_plus": "A month or more",
}

COST_CONFIDENCE_LABELS = {
    "rough": "Rough estimate",
    "approved": "Reviewed estimate",
}

TOP_ACTIONS_LIMIT = 5


class EngineValidationError(RuntimeError):
    """An assembled plan failed the grounding contract (uncited item)."""


def money(value: int | float | None) -> str:
    if value is None:
        return ""
    return f"${value:,.0f}"


def _normalize(answers: dict) -> dict:
    objective_key = answers.get("objective") or "sell_soon"
    timing_key = answers.get("timing_band") or "unsure"
    spend_key = answers.get("spend_band") or "unsure"

    objective = OBJECTIVES.get(objective_key, OBJECTIVES["sell_soon"])
    timing = TIMING_BANDS.get(timing_key, TIMING_BANDS["unsure"])
    spend = SPEND_BANDS.get(spend_key, SPEND_BANDS["unsure"])

    today = date.today()
    target_date_raw = answers.get("target_date") or ""
    target_date = None
    if target_date_raw:
        try:
            parsed = date.fromisoformat(target_date_raw)
            if parsed > today:
                target_date = parsed
        except ValueError:
            target_date = None

    horizon_days = (
        (target_date - today).days if target_date else timing["horizon_days"]
    )

    return {
        "objective_key": objective_key,
        "objective_label": objective["label"],
        "goal": objective["goal"],
        "timing_key": timing_key,
        "timing_label": timing["label"],
        "timing_assumed": timing_key == "unsure",
        "spend_key": spend_key,
        "spend_label": spend["label"],
        "spend_cap": spend["cap"],
        "spend_unsure": spend_key == "unsure",
        "today": today,
        "target_date": target_date,
        "horizon_days": max(horizon_days, 1),
        "issues": [i for i in (answers.get("issues") or []) if i],
        "custom_issue": (answers.get("custom_issue") or "").strip(),
    }


def _timeline_status(row: CatalogRow, horizon_days: int) -> tuple[str, int]:
    total_days = row.max_days
    if total_days > horizon_days:
        return "beyond", total_days
    if row.tier == "critical":
        return "urgent", total_days
    if total_days >= horizon_days * 0.5:
        return "constrained", total_days
    return "feasible", total_days


def _citations(row: CatalogRow, ctx: dict, labels: dict[str, str]) -> list[dict]:
    citations = []
    matched_issues = [k for k in row.trigger_issues if k in ctx["issues"]]
    for key in matched_issues:
        citations.append(
            {"source": "issue_picker", "text": f"You told us: {labels.get(key, key).lower()}"}
        )
    if row.is_listing_readiness or not matched_issues:
        citations.append(
            {
                "source": "user_input",
                "text": (
                    f"Based on your goal (to {ctx['objective_label']}) "
                    f"and timeline ({ctx['timing_label']})"
                ),
            }
        )
    citations.append(
        {
            "source": "seed_table",
            "text": f"{row.cost_source_label} \u2014 a national range we maintain, not a quote",
        }
    )
    return citations


def _build_item(row: CatalogRow, ctx: dict, labels: dict[str, str]) -> dict:
    status, total_days = _timeline_status(row, ctx["horizon_days"])
    feasible_after = None
    if status == "beyond":
        feasible_after = (ctx["today"] + timedelta(days=total_days)).isoformat()

    return {
        "id": row.seed_row_id,
        "name": row.repair_type,
        "tier": row.tier,
        "tier_badge": TIER_BADGES[row.tier],
        "timeline_status": status,
        "timeline_label": STATUS_LABELS[status],
        "cost_low": row.cost_low_usd,
        "cost_high": row.cost_high_usd,
        "cost_band": f"{money(row.cost_low_usd)}\u2013{money(row.cost_high_usd)}",
        "cost_confidence": "approved" if row.is_approved else "rough",
        "cost_source_label": row.cost_source_label,
        "diy": {
            "flag": row.diy_flag,
            "label": DIY_LABELS[row.diy_flag],
            "reason": row.diy_reason,
        },
        "duration_band": row.duration_band,
        "duration_label": DURATION_BAND_LABELS.get(
            row.duration_band, row.duration_band
        ),
        "total_days": total_days,
        "cost_confidence_label": COST_CONFIDENCE_LABELS[
            "approved" if row.is_approved else "rough"
        ],
        "feasible_after": feasible_after,
        "next_step_template": row.next_step_template,
        "rationale": {
            "citations": _citations(row, ctx, labels),
            "seed_row_id": row.seed_row_id,
            "rule_ids": [RULE_ELIGIBILITY, RULE_TIMELINE, RULE_TIER_ORDER],
            "skip_risk": _skip_risk(row),
        },
        "sequence": None,  # assigned after ordering
    }


def _skip_risk(row: CatalogRow) -> str:
    if row.tier == "critical":
        return (
            "Skipping this risks inspection objections, buyer concessions, "
            "or a stalled closing."
        )
    if row.tier == "deferred_maintenance":
        return "Skipping this invites inspection notes and price-chipping at offer time."
    if row.tier == "listing_readiness":
        return "Skipping this weakens first impressions \u2014 online and in person."
    return "Optional \u2014 skip freely if budget or time is tight."


def _dns_item(row: CatalogRow, ctx: dict) -> dict:
    return {
        "id": row.seed_row_id,
        "name": row.repair_type,
        "cost_band": f"{money(row.cost_low_usd)}\u2013{money(row.cost_high_usd)}",
        "cost_low": row.cost_low_usd,
        "cost_high": row.cost_high_usd,
        "timeline_status": "not_recommended",
        "timeline_label": STATUS_LABELS["not_recommended"],
        "reason": row.do_not_spend_reason,
        "rationale": {
            "citations": [
                {
                    "source": "user_input",
                    "text": (
                        f"Based on your goal (to {ctx['objective_label']}) "
                        f"and timeline ({ctx['timing_label']})"
                    ),
                },
                {
                    "source": "seed_table",
                    "text": f"{row.cost_source_label} \u2014 a national range we maintain, not a quote",
                },
            ],
            "seed_row_id": row.seed_row_id,
            "rule_ids": [RULE_DO_NOT_SPEND],
        },
    }


def _verdict(
    ctx: dict,
    top: list[dict],
    dns: list[dict],
    beyond: list[dict],
    omitted_over_budget: int,
    facts_fallback: bool,
) -> dict[str, str]:
    """Executive verdict: headline outcome plus supporting detail."""
    urgent = [i for i in top if i["timeline_status"] == "urgent"]
    rest = len(top) - len(urgent)
    goal_timing = (
        f"you're aiming to {ctx['objective_label']} {ctx['timing_label']}"
    )

    if urgent:
        low = sum(i["cost_low"] for i in urgent)
        high = sum(i["cost_high"] for i in urgent)
        urgent_word = "fixes" if len(urgent) != 1 else "fix"
        if rest:
            headline = (
                f"Start with {len(urgent)} urgent {urgent_word} "
                f"({money(low)}\u2013{money(high)}), then {rest} prep "
                f"action{'s' if rest != 1 else ''} \u2014 {goal_timing}."
            )
        else:
            headline = (
                f"{len(urgent)} urgent {urgent_word} first "
                f"({money(low)}\u2013{money(high)}) \u2014 {goal_timing}."
            )
    elif top:
        headline = (
            f"{len(top)} prep action{'s' if len(top) != 1 else ''} ranked "
            f"for listing \u2014 {goal_timing}."
        )
    else:
        headline = f"No prep actions surfaced yet \u2014 {goal_timing}."

    body_parts: list[str] = []
    if not urgent and top:
        body_parts.append(
            "Nothing urgent stands out from what we know. "
            "Focus on presentation and listing-readiness."
        )
    if dns:
        body_parts.append(
            f"We'd skip {len(dns)} low-return project"
            f"{'s' if len(dns) != 1 else ''} \u2014 see Do Not Spend."
        )
    if beyond:
        body_parts.append(
            f"{len(beyond)} {'items' if len(beyond) != 1 else 'item'} "
            "won't fit before your date \u2014 see Beyond Your Timeline."
        )
    if omitted_over_budget:
        body_parts.append(
            f"We left {omitted_over_budget} "
            f"{'items' if omitted_over_budget != 1 else 'item'} off the list "
            "because they sit above your spend comfort."
        )
    if facts_fallback:
        body_parts.append(
            "County records were unavailable, so this plan leans on what you told us."
        )

    return {"headline": headline, "body": " ".join(body_parts)}


def _plan_summary(
    ctx: dict,
    top: list[dict],
    dns: list[dict],
    beyond: list[dict],
    additional: list[dict],
    omitted_over_budget: int,
    target_date: date,
) -> dict:
    top_low = sum(i["cost_low"] for i in top)
    top_high = sum(i["cost_high"] for i in top)
    dns_low = sum(d["cost_low"] for d in dns)
    dns_high = sum(d["cost_high"] for d in dns)
    urgent_count = sum(1 for i in top if i["timeline_status"] == "urgent")

    return {
        "urgent_count": urgent_count,
        "top_action_count": len(top),
        "top_cost_band": (
            f"{money(top_low)}\u2013{money(top_high)}" if top else ""
        ),
        "dns_count": len(dns),
        "dns_savings_band": (
            f"{money(dns_low)}\u2013{money(dns_high)}" if dns else ""
        ),
        "beyond_count": len(beyond),
        "additional_count": len(additional),
        "target_date": target_date.isoformat(),
        "timing_label": ctx["timing_label"],
        "spend_label": ctx["spend_label"],
        "spend_unsure": ctx["spend_unsure"],
        "omitted_over_budget": omitted_over_budget,
    }


def _next_steps(ctx: dict, top: list[dict]) -> list[str]:
    steps = []
    for item in top:
        template = item.get("next_step_template")
        if template:
            steps.append(template)
        if len(steps) == 4:
            break
    steps.append(
        "Walk the house like a buyer \u2014 front door first \u2014 and note "
        "anything you stopped seeing years ago."
    )
    return steps[:5]


def build_plan(
    answers: dict,
    facts: dict | None,
    facts_fallback: bool,
    facts_partial: bool = False,
) -> dict:
    """Assemble the starter Seller Action Plan. Deterministic; seed-driven."""
    ctx = _normalize(answers)
    labels = issue_labels()
    catalog = load_catalog()

    plan_rows: list[CatalogRow] = []
    dns_rows: list[CatalogRow] = []
    for row in catalog:
        if row.do_not_spend_for(ctx["goal"]):
            dns_rows.append(row)
            continue
        if "never" in row.trigger_issues:
            continue
        if not row.applies_to_goal(ctx["goal"]):
            continue
        triggered = row.is_listing_readiness or any(
            key in ctx["issues"] for key in row.trigger_issues
        )
        if triggered:
            plan_rows.append(row)

    # Spend comfort: never drop critical items; non-critical items above the
    # cap are omitted and counted (we never push past comfort, we say so).
    omitted_over_budget = 0
    if ctx["spend_cap"] is not None:
        kept = []
        for row in plan_rows:
            if row.tier != "critical" and row.cost_low_usd > ctx["spend_cap"]:
                omitted_over_budget += 1
            else:
                kept.append(row)
        plan_rows = kept

    # Deterministic ordering: tier rank, then seed (curated severity) order.
    seed_order = {row.seed_row_id: idx for idx, row in enumerate(catalog)}
    plan_rows.sort(key=lambda r: (TIER_RANK[r.tier], seed_order[r.seed_row_id]))

    items = [_build_item(row, ctx, labels) for row in plan_rows]
    beyond = [i for i in items if i["timeline_status"] == "beyond"]
    in_plan = [i for i in items if i["timeline_status"] != "beyond"]

    top = in_plan[:TOP_ACTIONS_LIMIT]
    additional = in_plan[TOP_ACTIONS_LIMIT:]
    for sequence, item in enumerate(top, start=1):
        item["sequence"] = sequence

    dns = [_dns_item(row, ctx) for row in dns_rows]
    dns_low = sum(d["cost_low"] for d in dns)
    dns_high = sum(d["cost_high"] for d in dns)

    target_date = ctx["target_date"] or (
        ctx["today"] + timedelta(days=ctx["horizon_days"])
    )

    assumptions = []
    if ctx["timing_assumed"]:
        assumptions.append("timing_assumed")
    if ctx["spend_unsure"]:
        assumptions.append("spend_unsure")
    if not ctx["issues"]:
        assumptions.append("no_condition_input")
    if facts_fallback:
        assumptions.append("facts_fallback")

    plan = {
        "engine_version": ENGINE_VERSION,
        "generated_on": ctx["today"].isoformat(),
        "context": {
            "objective_key": ctx["objective_key"],
            "objective_label": ctx["objective_label"],
            "goal": ctx["goal"],
            "timing_label": ctx["timing_label"],
            "spend_label": ctx["spend_label"],
            "issues": ctx["issues"],
            "issue_labels": [labels.get(k, k) for k in ctx["issues"]],
            "custom_issue": ctx["custom_issue"],
        },
        "assumptions": assumptions,
        "verdict": _verdict(
            ctx, top, dns, beyond, omitted_over_budget, facts_fallback
        ),
        "plan_summary": _plan_summary(
            ctx, top, dns, beyond, additional, omitted_over_budget, target_date
        ),
        "property_summary": {
            "facts": facts or {},
            "fallback_warning": facts_fallback,
            "partial_warning": facts_partial,
        },
        "plan_items": top,
        "additional_items": additional,
        "beyond_timeline": beyond,
        "do_not_spend": dns,
        "do_not_spend_total_band": (
            f"{money(dns_low)}\u2013{money(dns_high)}" if dns else ""
        ),
        "omitted_over_budget": omitted_over_budget,
        "next_steps": _next_steps(ctx, top),
        "horizon": {
            "today": ctx["today"].isoformat(),
            "target_date": target_date.isoformat(),
            "band_label": ctx["timing_label"],
            "assumed": ctx["timing_assumed"],
            "horizon_days": ctx["horizon_days"],
        },
        "verdict_inputs": {
            "urgent_count": sum(1 for i in top if i["timeline_status"] == "urgent"),
            "top_cost_low": sum(i["cost_low"] for i in top),
            "top_cost_high": sum(i["cost_high"] for i in top),
        },
    }
    _validate_plan(plan)
    return plan


def _validate_plan(plan: dict) -> None:
    """Grounding contract: every item carries citations and a seed trace."""
    for bucket in ("plan_items", "additional_items", "beyond_timeline", "do_not_spend"):
        for item in plan[bucket]:
            rationale = item.get("rationale") or {}
            if not rationale.get("citations"):
                raise EngineValidationError(
                    f"item {item.get('id')!r} in {bucket} has no citations"
                )
            if not rationale.get("seed_row_id"):
                raise EngineValidationError(
                    f"item {item.get('id')!r} in {bucket} has no seed trace"
                )
