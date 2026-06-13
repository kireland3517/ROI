"""Review-status-aware loaders for versioned CSV seed tables (D-V13-003).

Seed CSVs in this package are the executable handoff of the governed
workbooks under docs/product/raw/. Rows that are not owner-approved or
expert-validated are surfaced as static assumptions in output provenance.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

SEEDS_DIR = Path(__file__).resolve().parent

CATALOG_FILE = SEEDS_DIR / "catalog_v0.csv"
ISSUE_PICKER_FILE = SEEDS_DIR / "issue_picker_v0.csv"
ISSUE_PICKER_GROUPS_FILE = SEEDS_DIR / "issue_picker_groups_v0.csv"
DURATION_RULES_FILE = SEEDS_DIR / "duration_lead_time_rules_v1.csv"

VALID_REVIEW_STATUSES = {
    "pending",
    "estimated",
    "proposed_pending_source_QA",
    "replaced_by_subtypes",
    "approved_by_owner",
    "expert_validated",
}

APPROVED_REVIEW_STATUSES = {"approved_by_owner", "expert_validated"}

VALID_TIERS = {
    "critical",
    "deferred_maintenance",
    "listing_readiness",
    "cosmetic_value_add",
}

# Duration band -> conservative max calendar days for timeline feasibility.
DURATION_BAND_MAX_DAYS = {
    "hours": 1,
    "days": 3,
    "week": 7,
    "weeks": 21,
    "month_plus": 45,
}

VALID_DIY_FLAGS = {"yes", "no", "conditional"}


class SeedValidationError(ValueError):
    """A seed file failed structural validation and must not be served."""


def _split_multi(value: str) -> tuple[str, ...]:
    return tuple(part.strip() for part in value.split(";") if part.strip())


@dataclass(frozen=True)
class CatalogRow:
    seed_row_id: str
    repair_type: str
    tier: str
    trigger_issues: tuple[str, ...]  # issue keys, or ("always",) / ("never",)
    goal_filter: tuple[str, ...]  # goal keys, or ("all",)
    cost_low_usd: int
    cost_high_usd: int
    cost_source_label: str
    duration_band: str
    lead_time_days: int
    diy_flag: str
    diy_reason: str
    do_not_spend_goals: tuple[str, ...]
    do_not_spend_reason: str
    next_step_template: str
    review_status: str
    version: str

    @property
    def max_days(self) -> int:
        return self.lead_time_days + DURATION_BAND_MAX_DAYS[self.duration_band]

    @property
    def is_listing_readiness(self) -> bool:
        return self.trigger_issues == ("always",)

    @property
    def is_approved(self) -> bool:
        return self.review_status in APPROVED_REVIEW_STATUSES

    def applies_to_goal(self, goal: str) -> bool:
        return "all" in self.goal_filter or goal in self.goal_filter

    def do_not_spend_for(self, goal: str) -> bool:
        return goal in self.do_not_spend_goals or (
            bool(self.do_not_spend_goals) and "all" in self.do_not_spend_goals
        )


@dataclass(frozen=True)
class IssueOption:
    issue_key: str
    label: str
    sort_order: int


@dataclass(frozen=True)
class IssueGroup:
    """UI grouping for the issue picker — must cover every issue_picker row."""

    group_id: str
    label: str
    sort_order: int
    options: tuple[IssueOption, ...]


def _validate_catalog_row(raw: dict, line_no: int) -> CatalogRow:
    def fail(msg: str) -> SeedValidationError:
        return SeedValidationError(
            f"{CATALOG_FILE.name} line {line_no}: {msg} (row {raw.get('seed_row_id', '?')})"
        )

    if not raw.get("seed_row_id"):
        raise fail("missing seed_row_id")
    if raw.get("tier") not in VALID_TIERS:
        raise fail(f"invalid tier {raw.get('tier')!r}")
    if raw.get("review_status") not in VALID_REVIEW_STATUSES:
        raise fail(f"invalid review_status {raw.get('review_status')!r}")
    if raw.get("duration_band") not in DURATION_BAND_MAX_DAYS:
        raise fail(f"invalid duration_band {raw.get('duration_band')!r}")
    if raw.get("diy_flag") not in VALID_DIY_FLAGS:
        raise fail(f"invalid diy_flag {raw.get('diy_flag')!r}")
    if not raw.get("cost_source_label"):
        raise fail("missing cost_source_label")

    try:
        cost_low = int(raw["cost_low_usd"])
        cost_high = int(raw["cost_high_usd"])
        lead_time = int(raw["lead_time_days"])
    except (KeyError, ValueError) as exc:
        raise fail(f"non-numeric cost or lead time: {exc}") from exc

    if cost_high <= 0 or cost_low < 0 or cost_low > cost_high:
        raise fail(f"empty or inverted cost range {cost_low}..{cost_high}")
    if lead_time < 0:
        raise fail("negative lead_time_days")

    trigger = _split_multi(raw.get("trigger_issues", ""))
    if not trigger:
        raise fail("missing trigger_issues (use 'always' or 'never')")

    row = CatalogRow(
        seed_row_id=raw["seed_row_id"].strip(),
        repair_type=raw["repair_type"].strip(),
        tier=raw["tier"].strip(),
        trigger_issues=trigger,
        goal_filter=_split_multi(raw.get("goal_filter", "")) or ("all",),
        cost_low_usd=cost_low,
        cost_high_usd=cost_high,
        cost_source_label=raw["cost_source_label"].strip(),
        duration_band=raw["duration_band"].strip(),
        lead_time_days=lead_time,
        diy_flag=raw["diy_flag"].strip(),
        diy_reason=(raw.get("diy_reason") or "").strip(),
        do_not_spend_goals=_split_multi(raw.get("do_not_spend_goals", "")),
        do_not_spend_reason=(raw.get("do_not_spend_reason") or "").strip(),
        next_step_template=(raw.get("next_step_template") or "").strip(),
        review_status=raw["review_status"].strip(),
        version=(raw.get("version") or "").strip(),
    )

    if row.do_not_spend_goals and not row.do_not_spend_reason:
        raise fail("do_not_spend_goals set without do_not_spend_reason")
    return row


def _read_csv(path: Path) -> list[dict]:
    if not path.exists():
        raise SeedValidationError(f"seed file missing: {path}")
    with path.open(newline="", encoding="utf-8-sig") as handle:
        rows = list(csv.DictReader(handle))
    if not rows:
        raise SeedValidationError(f"seed file empty: {path}")
    return rows


@lru_cache(maxsize=1)
def load_catalog() -> tuple[CatalogRow, ...]:
    rows = tuple(
        _validate_catalog_row(raw, line_no)
        for line_no, raw in enumerate(_read_csv(CATALOG_FILE), start=2)
    )
    seen: set[str] = set()
    for row in rows:
        if row.seed_row_id in seen:
            raise SeedValidationError(f"duplicate seed_row_id {row.seed_row_id}")
        seen.add(row.seed_row_id)
    return rows


@lru_cache(maxsize=1)
def load_issue_picker() -> tuple[IssueOption, ...]:
    options = []
    known_triggers = {
        key for row in load_catalog() for key in row.trigger_issues
    }
    for line_no, raw in enumerate(_read_csv(ISSUE_PICKER_FILE), start=2):
        key = (raw.get("issue_key") or "").strip()
        label = (raw.get("label") or "").strip()
        if not key or not label:
            raise SeedValidationError(
                f"{ISSUE_PICKER_FILE.name} line {line_no}: missing issue_key or label"
            )
        if key not in known_triggers:
            raise SeedValidationError(
                f"{ISSUE_PICKER_FILE.name} line {line_no}: issue_key {key!r} "
                "has no matching catalog trigger"
            )
        options.append(
            IssueOption(issue_key=key, label=label, sort_order=int(raw.get("sort_order") or 0))
        )
    return tuple(sorted(options, key=lambda opt: opt.sort_order))


@lru_cache(maxsize=1)
def load_issue_picker_groups() -> tuple[IssueGroup, ...]:
    """Load issue picker UI groups. Every picker key must appear exactly once.

    When adding rows to issue_picker_v0.csv, update issue_picker_groups_v0.csv
    in the same change — load fails loudly if they drift apart.
    """
    options = load_issue_picker()
    by_key = {opt.issue_key: opt for opt in options}
    rows = _read_csv(ISSUE_PICKER_GROUPS_FILE)
    grouped: dict[str, dict] = {}
    seen_keys: set[str] = set()

    for line_no, raw in enumerate(rows, start=2):
        group_id = (raw.get("group_id") or "").strip()
        group_label = (raw.get("group_label") or "").strip()
        issue_key = (raw.get("issue_key") or "").strip()
        if not group_id or not group_label or not issue_key:
            raise SeedValidationError(
                f"{ISSUE_PICKER_GROUPS_FILE.name} line {line_no}: "
                "missing group_id, group_label, or issue_key"
            )
        if issue_key not in by_key:
            raise SeedValidationError(
                f"{ISSUE_PICKER_GROUPS_FILE.name} line {line_no}: "
                f"issue_key {issue_key!r} not in issue picker seed"
            )
        if issue_key in seen_keys:
            raise SeedValidationError(
                f"{ISSUE_PICKER_GROUPS_FILE.name} line {line_no}: "
                f"duplicate issue_key {issue_key!r}"
            )
        seen_keys.add(issue_key)
        try:
            group_sort = int(raw.get("group_sort") or 0)
        except ValueError as exc:
            raise SeedValidationError(
                f"{ISSUE_PICKER_GROUPS_FILE.name} line {line_no}: invalid group_sort"
            ) from exc

        bucket = grouped.setdefault(
            group_id,
            {"label": group_label, "sort_order": group_sort, "options": []},
        )
        if bucket["label"] != group_label or bucket["sort_order"] != group_sort:
            raise SeedValidationError(
                f"{ISSUE_PICKER_GROUPS_FILE.name} line {line_no}: "
                f"group_id {group_id!r} has inconsistent label or sort"
            )
        bucket["options"].append(by_key[issue_key])

    missing = set(by_key) - seen_keys
    if missing:
        raise SeedValidationError(
            f"{ISSUE_PICKER_GROUPS_FILE.name} missing picker keys: "
            f"{', '.join(sorted(missing))}"
        )

    groups = []
    for group_id, data in grouped.items():
        opts = tuple(sorted(data["options"], key=lambda opt: opt.sort_order))
        groups.append(
            IssueGroup(
                group_id=group_id,
                label=data["label"],
                sort_order=data["sort_order"],
                options=opts,
            )
        )
    return tuple(sorted(groups, key=lambda g: g.sort_order))


@lru_cache(maxsize=1)
def load_duration_rules() -> tuple[dict, ...]:
    """Governed duration/lead-time rows (not consumed by engine v0; loaded for QA)."""
    rows = _read_csv(DURATION_RULES_FILE)
    for line_no, raw in enumerate(rows, start=2):
        status = (raw.get("review_status") or "").strip()
        if status not in VALID_REVIEW_STATUSES:
            raise SeedValidationError(
                f"{DURATION_RULES_FILE.name} line {line_no}: invalid review_status {status!r}"
            )
    return tuple(rows)


def issue_labels() -> dict[str, str]:
    return {opt.issue_key: opt.label for opt in load_issue_picker()}
