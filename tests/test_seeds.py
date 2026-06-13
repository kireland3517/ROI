"""Seed validation: schema, statuses, costs, and no market literals."""

import csv

import pytest

from app.seeds import (
    CATALOG_FILE,
    DURATION_RULES_FILE,
    ISSUE_PICKER_FILE,
    SeedValidationError,
    load_catalog,
    load_duration_rules,
    load_issue_picker,
)

BANNED_STRINGS = ("simpsonville", "greenville", "kingfisher", "29680")


def test_catalog_loads_and_validates():
    rows = load_catalog()
    assert len(rows) >= 20
    ids = [row.seed_row_id for row in rows]
    assert len(ids) == len(set(ids))


def test_catalog_cost_ranges_nonempty():
    for row in load_catalog():
        assert row.cost_high_usd > 0, row.seed_row_id
        assert row.cost_low_usd <= row.cost_high_usd, row.seed_row_id
        assert row.cost_source_label, row.seed_row_id


def test_catalog_do_not_spend_rows_have_reasons():
    dns_rows = [row for row in load_catalog() if row.do_not_spend_goals]
    assert dns_rows, "expected Do Not Spend rows in the catalog"
    for row in dns_rows:
        assert row.do_not_spend_reason, row.seed_row_id


def test_catalog_has_listing_readiness_floor():
    """The Top 5 can never be empty: listing-readiness rows apply to every goal."""
    always = [
        row
        for row in load_catalog()
        if row.is_listing_readiness and "all" in row.goal_filter
    ]
    assert len(always) >= 3


def test_issue_picker_keys_match_catalog_triggers():
    options = load_issue_picker()
    assert len(options) >= 10
    triggered = {
        key
        for row in load_catalog()
        for key in row.trigger_issues
        if key not in ("always", "never")
    }
    for option in options:
        assert option.issue_key in triggered


def test_duration_rules_load_with_valid_statuses():
    rows = load_duration_rules()
    assert len(rows) >= 30


def test_no_market_literals_in_seed_files():
    for path in (CATALOG_FILE, ISSUE_PICKER_FILE):
        text = path.read_text(encoding="utf-8").lower()
        for banned in BANNED_STRINGS:
            assert banned not in text, f"{banned!r} found in {path.name}"


def test_invalid_review_status_rejected(tmp_path, monkeypatch):
    import app.seeds as seeds

    bad = tmp_path / "catalog_v0.csv"
    with CATALOG_FILE.open(encoding="utf-8") as src:
        rows = list(csv.DictReader(src))
    rows[0]["review_status"] = "totally_fine_trust_me"
    with bad.open("w", newline="", encoding="utf-8") as out:
        writer = csv.DictWriter(out, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

    monkeypatch.setattr(seeds, "CATALOG_FILE", bad)
    seeds.load_catalog.cache_clear()
    try:
        with pytest.raises(SeedValidationError):
            seeds.load_catalog()
    finally:
        seeds.load_catalog.cache_clear()
