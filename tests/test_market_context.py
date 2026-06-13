"""Local market context: market gating, graceful degradation, honest labels."""

from datetime import date
from pathlib import Path

import pytest

from app import market_context
from tests.conftest import run_intake

TODAY = date(2026, 6, 11)  # comp file holds sales through 2026-05


@pytest.fixture(autouse=True)
def fresh_cache():
    market_context._load_markets.cache_clear()
    yield
    market_context._load_markets.cache_clear()


# ---------------------------------------------------------------- gating


def test_greenville_zip_gets_context():
    result = market_context.build_market_context("SC", "29680", today=TODAY)
    assert result["available"] is True
    assert result["comp_count"] >= 3
    assert result["price_band"].startswith("$")
    assert result["median_price"].startswith("$")
    assert result["data_through"] >= "2025-01-01"
    assert result["support"] in {"strong", "limited"}


def test_non_sc_subject_gets_nothing():
    result = market_context.build_market_context("IL", "62704", today=TODAY)
    assert result["available"] is False
    assert result["reason"] == "out_of_market"


def test_sc_zip_outside_metro_gets_nothing():
    # Charleston is SC but not in the Greenville metro comp coverage.
    result = market_context.build_market_context("SC", "29401", today=TODAY)
    assert result["available"] is False
    assert result["reason"] == "out_of_market"


def test_blank_location_gets_nothing():
    result = market_context.build_market_context("", "", today=TODAY)
    assert result["available"] is False


# ---------------------------------------------------------------- degradation


def test_missing_comp_file_degrades(monkeypatch):
    monkeypatch.setattr(
        market_context,
        "MARKET_COMP_FILES",
        (("Test market", Path("does/not/exist.csv")),),
    )
    result = market_context.build_market_context("SC", "29680", today=TODAY)
    assert result["available"] is False


def test_dirty_comp_file_degrades(monkeypatch, tmp_path):
    dirty = tmp_path / "dirty.csv"
    dirty.write_text(
        "postal1,state,property_type,sale_type,sale_amount,sale_date,price_per_sqft\n"
        "29680,SC,SFR,Resale,not_a_number,2026-01-15,\n"
        "29680,SC,SFR,Resale,250000,garbage-date,\n"
        ",SC,SFR,Resale,250000,2026-01-15,\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(
        market_context, "MARKET_COMP_FILES", (("Test market", dirty),)
    )
    result = market_context.build_market_context("SC", "29680", today=TODAY)
    assert result["available"] is False  # all rows invalid -> no market loads


def test_stale_comps_outside_window_degrade(monkeypatch, tmp_path):
    stale = tmp_path / "stale.csv"
    rows = "\n".join(
        "29680,SC,SFR,Resale,250000,2018-01-15,140" for _ in range(20)
    )
    stale.write_text(
        "postal1,state,property_type,sale_type,sale_amount,sale_date,price_per_sqft\n"
        + rows + "\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(
        market_context, "MARKET_COMP_FILES", (("Test market", stale),)
    )
    result = market_context.build_market_context("SC", "29680", today=TODAY)
    assert result["available"] is False
    assert result["reason"] == "insufficient_recent_comps"


# ---------------------------------------------------------------- report rendering

GREENVILLE_ADDRESS = "130 Kingfisher Dr, Simpsonville, SC 29680"


def _run_intake_with_address(client, address):
    response = client.post(
        "/intake/address", data={"address": address}, follow_redirects=False
    )
    assert response.status_code == 303
    session_id = response.headers["location"].split("/")[2]
    client.post(f"/intake/{session_id}/confirm", follow_redirects=False)
    for step, value in (("objective", "sell_soon"), ("timing", "m1_3"), ("spend", "b1_5k")):
        client.post(
            f"/intake/{session_id}/q/{step}", data={"value": value},
            follow_redirects=False,
        )
    client.post(f"/intake/{session_id}/issues", data={"skip": "1"}, follow_redirects=False)
    return session_id


def test_greenville_report_shows_market_section(client, attom_down):
    session_id = _run_intake_with_address(client, GREENVILLE_ADDRESS)
    html = client.get(f"/plan/{session_id}").text
    assert "Local market context" in html
    assert "Recorded sales" in html
    assert "County sale records" in html
    assert "Data through" in html
    assert "comp support" in html
    assert "not an estimate of your home" in html


def test_non_greenville_report_shows_unavailable(client, attom_down):
    session_id = run_intake(client, skip_issues=True)  # IL address
    html = client.get(f"/plan/{session_id}").text
    assert "Local market context" in html
    assert "Local sale-price calibration" in html  # the "unavailable" line
    assert "Middle 50% of sales" not in html
    assert "County sale records" not in html


def test_no_unsupported_value_claims(client, attom_down):
    """The section makes no ARV/ROI/home-value claims (governance rule)."""
    session_id = _run_intake_with_address(client, GREENVILLE_ADDRESS)
    html = client.get(f"/plan/{session_id}").text.lower()
    for banned in (
        "arv",
        "after repair value",
        "after-repair value",
        "your home is worth",
        "estimated value",
        "expected return",
        "resale value",
    ):
        assert banned not in html, f"unsupported claim {banned!r} in report"
