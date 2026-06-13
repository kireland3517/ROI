"""ATTOM property facts adapter.

Pulls basic property facts for the confirmed address. On any failure the
caller falls back to user-entered values with a visible warning — material
API failures must not fail silently and must not block the flow (PRD error
and partial-failure UX).
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone

import requests

API_URL = "https://api.gateway.attomdata.com/propertyapi/v1.0.0/property/basicprofile"
TIMEOUT_SECONDS = 10

KEY_FACT_FIELDS = ("beds", "baths", "sqft", "year_built")

logger = logging.getLogger(__name__)


@dataclass
class PropertyFacts:
    beds: int | None = None
    baths: float | None = None
    sqft: int | None = None
    year_built: int | None = None
    lot_acres: float | None = None
    source: str = "user"  # "attom" | "user" | "user_confirmed"
    pulled_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).date().isoformat()
    )

    @property
    def has_any(self) -> bool:
        return any(v is not None for v in (self.beds, self.baths, self.sqft, self.year_built))


def _debug_property_facts(event: str, **fields) -> None:
    """Optional diagnostics — enable with DEBUG_PROPERTY_FACTS=true in .env."""
    if os.getenv("DEBUG_PROPERTY_FACTS", "").strip().lower() not in {
        "1", "true", "yes", "on",
    }:
        return
    logger.info("property_facts.%s %s", event, fields)


def _to_int(value) -> int | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return int(number) if number > 0 else None


def _to_float(value) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if number > 0 else None


def _get_field(section: dict | None, *names: str):
    """Return the first present value, matching keys case-insensitively."""
    if not section:
        return None
    lower_map = {
        key.lower(): value
        for key, value in section.items()
        if isinstance(key, str)
    }
    for name in names:
        if name in section:
            return section[name]
        hit = lower_map.get(name.lower())
        if hit is not None:
            return hit
    return None


def facts_from_attom_property(prop: dict) -> PropertyFacts:
    """Map an ATTOM property object to PropertyFacts (shared by fetch + tests)."""
    building = prop.get("building") or {}
    rooms = building.get("rooms") or {}
    size = building.get("size") or {}
    summary = prop.get("summary") or {}
    lot = prop.get("lot") or {}

    sqft_raw = _get_field(size, "universalsize", "universalSize", "livingsize", "livingSize")
    baths_raw = _get_field(
        rooms,
        "bathstotal",
        "bathsTotal",
        "bathsfull",
        "bathsFull",
    )

    facts = PropertyFacts(
        beds=_to_int(_get_field(rooms, "beds")),
        baths=_to_float(baths_raw),
        sqft=_to_int(sqft_raw),
        year_built=_to_int(_get_field(summary, "yearbuilt", "yearBuilt")),
        lot_acres=_to_float(_get_field(lot, "lotsize1", "lotSize1")),
        source="attom",
    )
    _debug_property_facts(
        "mapped",
        attom_baths_present=baths_raw is not None,
        attom_sqft_present=sqft_raw is not None,
        attom_year_present=_get_field(summary, "yearbuilt", "yearBuilt") is not None,
        mapped=facts,
    )
    return facts


def facts_are_partial(facts: PropertyFacts | dict) -> bool:
    """True when ATTOM returned a match but one or more key fields are missing."""
    if isinstance(facts, PropertyFacts):
        source = facts.source
        values = [getattr(facts, name) for name in KEY_FACT_FIELDS]
    else:
        source = facts.get("source")
        values = [facts.get(name) for name in KEY_FACT_FIELDS]

    if source != "attom":
        return False
    if not any(value is not None for value in values):
        return False
    return any(value is None for value in values)


def fetch_property_facts(line1: str, line2: str) -> PropertyFacts | None:
    """Fetch facts from ATTOM. Returns None on any failure (caller falls back)."""
    api_key = os.getenv("ATTOM_API_KEY")
    if not api_key or not line1:
        return None

    params = {"address1": line1, "address2": line2}
    headers = {"accept": "application/json", "apikey": api_key}

    response = None
    for attempt in range(2):  # one retry on transient server errors
        try:
            response = requests.get(
                API_URL, params=params, headers=headers, timeout=TIMEOUT_SECONDS
            )
        except requests.RequestException:
            _debug_property_facts("fetch_failed", line1=line1, line2=line2, reason="network")
            return None
        if response.status_code < 500:
            break
    if response is None or response.status_code != 200:
        _debug_property_facts(
            "fetch_failed",
            line1=line1,
            line2=line2,
            status=getattr(response, "status_code", None),
        )
        return None

    try:
        payload = response.json()
        prop = payload["property"][0]
    except (ValueError, KeyError, IndexError):
        _debug_property_facts("fetch_failed", line1=line1, line2=line2, reason="parse")
        return None

    facts = facts_from_attom_property(prop)
    result = facts if facts.has_any else None
    _debug_property_facts(
        "fetch_complete",
        line1=line1,
        line2=line2,
        result=result,
        partial=facts_are_partial(facts) if result else None,
    )
    return result
