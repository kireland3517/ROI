"""Flow smoke tests: gate, intake, fallback warning, report rendering."""

from tests.conftest import run_intake


def test_invalid_address_blocks_with_message(client):
    response = client.post("/intake/address", data={"address": "banana"})
    assert response.status_code == 200
    # Jinja autoescapes the apostrophe; match around it.
    assert "validate that address" in response.text
    assert "Check the street number and ZIP" in response.text


def test_full_flow_renders_plan_with_attom_fallback(client, attom_down):
    session_id = run_intake(client, issues=["roof_leak"])
    response = client.get(f"/plan/{session_id}")
    assert response.status_code == 200
    text = response.text
    assert "Your Seller Action Plan" in text
    assert "Executive verdict" in text
    assert "Plan at a glance" in text
    assert "Beyond your timeline" in text
    assert "County records were unavailable" in text
    assert "Active roof leak repair" in text
    assert "Don't spend money here" in text or "Don&#39;t spend money here" in text


def test_full_flow_with_attom_facts_shows_records_chip(client, attom_facts):
    session_id = run_intake(client, issues=[])
    response = client.get(f"/plan/{session_id}")
    assert response.status_code == 200
    assert "County records, pulled" in response.text
    assert "1,850" in response.text


def test_skipping_issues_lowers_confidence_not_fabricates(client, attom_down):
    session_id = run_intake(client, skip_issues=True)
    response = client.get(f"/plan/{session_id}")
    assert response.status_code == 200
    assert "No condition input yet" in response.text
    # No issue-triggered repair should appear.
    assert "Active roof leak repair" not in response.text


def test_facts_correction_rebuilds_plan(client, attom_down):
    session_id = run_intake(client, issues=[])
    client.get(f"/plan/{session_id}")
    response = client.post(
        f"/plan/{session_id}/facts",
        data={"beds": "4", "baths": "2.5", "sqft": "2200", "year_built": "1995"},
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert "Confirmed by you" in response.text
    assert "2,200" in response.text


def test_unknown_session_redirects_home(client):
    response = client.get("/plan/not-a-session", follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/"


def test_generate_endpoint_returns_ok(client, attom_down):
    session_id = run_intake(client)
    response = client.post(f"/plan/{session_id}/generate")
    assert response.status_code == 200
    assert response.json() == {"ok": True}
