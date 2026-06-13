"""Local market context from recorded comparable sales.

Presentation-layer only: this module is computed *after* the engine builds
the plan and never feeds recommendations, ordering, or ROI. It supports only
defensible claims — recorded sale ranges, counts, freshness, and support
labels. No ARV, no value estimates, no comp-derived returns.

Market scoping is data-driven: a subject qualifies only when its validated
state and ZIP fall inside the coverage of a market comp file. Nothing
market-specific is hardcoded into national code — adding a market means
adding a comp file, not editing logic.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import date, timedelta
from functools import lru_cache
from pathlib import Path
from statistics import median

ROOT = Path(__file__).resolve().parents[1]

# Markets with local comp coverage. Each entry is (display label, csv path).
MARKET_COMP_FILES = (
    (
        "Greenville–Anderson–Greer, SC metro",
        ROOT / "regression" / "data" / "Greenville-Anderson-Greer_SC.csv",
    ),
)

# Cleaning rules (documented in README of claims: recorded arm's-length
# residential sales only).
RESIDENTIAL_TYPES = {"SFR", "TOWNHOUSE/ROWHOUSE", "CONDOMINIUM", "DUPLEX"}
VALID_SALE_TYPES = {"Resale", "New Construction"}
MIN_SALE_AMOUNT = 30_000  # below this, transfers are rarely arm's-length
WINDOW_DAYS = 365 * 2  # comp freshness window
STRONG_MIN = 10  # same-ZIP comps for "strong" support
LIMITED_MIN = 3  # minimum comps to show any numbers at all


@dataclass(frozen=True)
class CompSale:
    zip_code: str
    state: str
    sale_amount: float
    sale_date: date
    price_per_sqft: float | None


@dataclass(frozen=True)
class Market:
    label: str
    states: frozenset[str]
    zip_codes: frozenset[str]
    comps: tuple[CompSale, ...]


def _parse_zip(raw: str | None) -> str:
    """postal1 arrives as '29680' or '29680.0'; normalize to 5 digits."""
    text = (raw or "").strip()
    if not text:
        return ""
    try:
        return f"{int(float(text)):05d}"
    except ValueError:
        return ""


def _parse_row(raw: dict) -> CompSale | None:
    if (raw.get("property_type") or "").strip() not in RESIDENTIAL_TYPES:
        return None
    if (raw.get("sale_type") or "").strip() not in VALID_SALE_TYPES:
        return None
    zip_code = _parse_zip(raw.get("postal1"))
    state = (raw.get("state") or "").strip().upper()
    if not zip_code or not state:
        return None
    try:
        sale_amount = float(raw.get("sale_amount") or "")
        sale_date = date.fromisoformat((raw.get("sale_date") or "").strip())
    except (TypeError, ValueError):
        return None
    if sale_amount < MIN_SALE_AMOUNT:
        return None
    try:
        ppsf = float(raw.get("price_per_sqft") or "")
        price_per_sqft = ppsf if ppsf > 0 else None
    except (TypeError, ValueError):
        price_per_sqft = None
    return CompSale(
        zip_code=zip_code,
        state=state,
        sale_amount=sale_amount,
        sale_date=sale_date,
        price_per_sqft=price_per_sqft,
    )


def _load_market_file(label: str, path: Path) -> Market | None:
    """Load one market's comps; None when missing/unreadable (degrade, not crash)."""
    try:
        with path.open(newline="", encoding="utf-8") as handle:
            rows = [_parse_row(raw) for raw in csv.DictReader(handle)]
    except (OSError, csv.Error, UnicodeDecodeError):
        return None
    comps = tuple(row for row in rows if row is not None)
    if len(comps) < LIMITED_MIN:
        return None
    return Market(
        label=label,
        states=frozenset(c.state for c in comps),
        zip_codes=frozenset(c.zip_code for c in comps),
        comps=comps,
    )


@lru_cache(maxsize=1)
def _load_markets() -> tuple[Market, ...]:
    markets = []
    for label, path in MARKET_COMP_FILES:
        market = _load_market_file(label, path)
        if market is not None:
            markets.append(market)
    return tuple(markets)


def unavailable(reason: str) -> dict:
    return {"available": False, "reason": reason}


def _money(value: float) -> str:
    return f"${value:,.0f}"


def build_market_context(
    state: str, zip_code: str, *, today: date | None = None
) -> dict:
    """Summarize local recorded sales for an in-market subject.

    Out-of-market subjects, missing data, and thin comp sets all return an
    unavailable result — Greenville data must never color another market.
    """
    state = (state or "").strip().upper()
    zip_code = _parse_zip(zip_code)
    if not state or not zip_code:
        return unavailable("no_validated_location")

    market = next(
        (
            m
            for m in _load_markets()
            if state in m.states and zip_code in m.zip_codes
        ),
        None,
    )
    if market is None:
        return unavailable("out_of_market")

    cutoff = (today or date.today()) - timedelta(days=WINDOW_DAYS)
    recent = [c for c in market.comps if c.sale_date >= cutoff]
    zip_comps = [c for c in recent if c.zip_code == zip_code]

    if len(zip_comps) >= LIMITED_MIN:
        sample, scope = zip_comps, "zip"
    elif len(recent) >= LIMITED_MIN:
        sample, scope = recent, "metro"
    else:
        return unavailable("insufficient_recent_comps")

    if len(zip_comps) >= STRONG_MIN:
        support, support_label = "strong", "Strong local comp support"
    else:
        support, support_label = "limited", "Limited local comp support"

    prices = sorted(c.sale_amount for c in sample)
    p25 = prices[len(prices) // 4]
    p75 = prices[(len(prices) * 3) // 4]
    ppsf_values = [c.price_per_sqft for c in sample if c.price_per_sqft]

    return {
        "available": True,
        "market_label": market.label,
        "scope": scope,  # "zip" | "metro"
        "zip_code": zip_code,
        "comp_count": len(sample),
        "price_band": f"{_money(p25)} – {_money(p75)}",
        "median_price": _money(median(prices)),
        "median_ppsf": (
            f"${median(ppsf_values):,.0f}" if len(ppsf_values) >= LIMITED_MIN else None
        ),
        "ppsf_count": len(ppsf_values),
        "data_through": max(c.sale_date for c in sample).isoformat(),
        "window_months": WINDOW_DAYS // 30,
        "support": support,
        "support_label": support_label,
    }
