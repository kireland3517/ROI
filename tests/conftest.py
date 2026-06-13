"""Shared fixtures: no test ever touches a real external API."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.adapters import attom_property  # noqa: E402
from app.adapters.attom_property import PropertyFacts  # noqa: E402


@pytest.fixture(autouse=True)
def demo_environment(monkeypatch):
    """Tests run keyless in demo mode by default; individual tests override."""
    # app.main's load_dotenv() must run before the scrub, or the first import
    # (inside the client fixture) would re-inject real .env credentials and
    # tests would hit the live Smarty API.
    import app.main  # noqa: F401

    monkeypatch.delenv("SMARTY_AUTH_ID", raising=False)
    monkeypatch.delenv("SMARTY_AUTH_TOKEN", raising=False)
    monkeypatch.setenv("APP_ENV", "development")
    monkeypatch.setenv("USE_DEMO_FALLBACK", "true")


@pytest.fixture
def attom_down(monkeypatch):
    """Simulate ATTOM unavailable: the flow must fall back, not fail."""
    monkeypatch.setattr(
        attom_property, "fetch_property_facts", lambda line1, line2: None
    )


@pytest.fixture
def attom_facts(monkeypatch):
    """Simulate a healthy ATTOM property-facts response."""
    facts = PropertyFacts(
        beds=3, baths=2.0, sqft=1850, year_built=2001, lot_acres=0.3, source="attom"
    )
    monkeypatch.setattr(
        attom_property, "fetch_property_facts", lambda line1, line2: facts
    )


@pytest.fixture
def attom_partial(monkeypatch):
    """Simulate ATTOM returning a sparse county record (beds only)."""
    facts = PropertyFacts(beds=3, source="attom")
    monkeypatch.setattr(
        attom_property, "fetch_property_facts", lambda line1, line2: facts
    )


@pytest.fixture
def client():
    from fastapi.testclient import TestClient

    from app.main import app

    return TestClient(app)


def run_intake(client, *, objective="sell_soon", timing="m1_3", target_date="",
               spend="b1_5k", issues=(), skip_issues=False) -> str:
    """Drive the full intake flow; returns the session id."""
    response = client.post(
        "/intake/address",
        data={"address": "123 Maple Street, Springfield, IL 62704"},
        follow_redirects=False,
    )
    assert response.status_code == 303, response.text
    session_id = response.headers["location"].split("/")[2]

    client.post(f"/intake/{session_id}/confirm", follow_redirects=False)
    client.post(
        f"/intake/{session_id}/q/objective",
        data={"value": objective},
        follow_redirects=False,
    )
    client.post(
        f"/intake/{session_id}/q/timing",
        data={"value": timing, "target_date": target_date},
        follow_redirects=False,
    )
    client.post(
        f"/intake/{session_id}/q/spend",
        data={"value": spend},
        follow_redirects=False,
    )
    issue_data = {"skip": "1"} if skip_issues else {"issues": list(issues)}
    client.post(f"/intake/{session_id}/issues", data=issue_data, follow_redirects=False)
    return session_id
