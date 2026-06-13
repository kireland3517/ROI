"""ATTOM property facts mapping, partial detection, and route integration."""

from __future__ import annotations

from app.adapters import attom_property
from app.adapters.attom_property import (
    PropertyFacts,
    facts_are_partial,
    facts_from_attom_property,
)
from tests.conftest import run_intake

KINGFISHER_BASICPROFILE = {
    "building": {
        "rooms": {"beds": 3, "bathsFull": 2, "bathsTotal": 2.0},
        "size": {
            "bldgSize": 2019.0,
            "grossSizeAdjusted": 2019.0,
            "livingSize": 2019.0,
            "sizeInd": "LIVING SQFT",
            "universalSize": 2019.0,
        },
    },
    "summary": {"yearBuilt": 1999, "propType": "SFR"},
}

KINGFISHER_LOWERCASE = {
    "building": {
        "rooms": {"beds": 3, "bathstotal": 2.0, "bathsfull": 2},
        "size": {"universalsize": 2019, "livingsize": 2019},
    },
    "summary": {"yearbuilt": 1999},
}

PARTIAL_BASICPROFILE = {
    "building": {"rooms": {"beds": 3}},
    "summary": {},
}


def test_camelcase_basicprofile_maps_all_fields():
    facts = facts_from_attom_property(KINGFISHER_BASICPROFILE)
    assert facts.beds == 3
    assert facts.baths == 2.0
    assert facts.sqft == 2019
    assert facts.year_built == 1999
    assert facts.source == "attom"


def test_lowercase_basicprofile_maps_all_fields():
    facts = facts_from_attom_property(KINGFISHER_LOWERCASE)
    assert facts.beds == 3
    assert facts.baths == 2.0
    assert facts.sqft == 2019
    assert facts.year_built == 1999


def test_kingfisher_mocked_response_resolves_expected_fields():
    facts = facts_from_attom_property(KINGFISHER_BASICPROFILE)
    assert (facts.beds, facts.baths, facts.sqft, facts.year_built) == (3, 2.0, 2019, 1999)


def test_facts_are_partial_when_key_fields_missing():
    facts = facts_from_attom_property(PARTIAL_BASICPROFILE)
    assert facts.has_any
    assert facts_are_partial(facts)


def test_facts_are_not_partial_when_all_key_fields_present():
    facts = facts_from_attom_property(KINGFISHER_BASICPROFILE)
    assert not facts_are_partial(facts)


def test_facts_are_not_partial_for_user_confirmed():
    assert not facts_are_partial(
        {"source": "user_confirmed", "beds": 3, "baths": None, "sqft": None, "year_built": None}
    )


def test_fetch_property_facts_parses_mocked_http_response(monkeypatch):
    class FakeResponse:
        status_code = 200

        @staticmethod
        def json():
            return {"property": [KINGFISHER_BASICPROFILE]}

    monkeypatch.setenv("ATTOM_API_KEY", "test-key")
    monkeypatch.setattr(
        attom_property.requests, "get", lambda *args, **kwargs: FakeResponse()
    )
    facts = attom_property.fetch_property_facts(
        "130 Kingfisher Dr", "Simpsonville, SC 29680"
    )
    assert facts is not None
    assert (facts.beds, facts.baths, facts.sqft, facts.year_built) == (3, 2.0, 2019, 1999)


def test_partial_attom_data_shows_incomplete_warning(client, attom_partial):
    session_id = run_intake(client, issues=[])
    response = client.get(f"/plan/{session_id}")
    text = response.text
    assert response.status_code == 200
    assert "County records were incomplete" in text
    assert "County records (partial), pulled" in text
    assert "County records were unavailable" not in text


def test_total_attom_failure_still_shows_fallback_warning(client, attom_down):
    session_id = run_intake(client, issues=[])
    response = client.get(f"/plan/{session_id}")
    text = response.text
    assert response.status_code == 200
    assert "County records were unavailable" in text
    assert "County records were incomplete" not in text


def test_full_attom_facts_show_records_chip_without_partial_warning(client, attom_facts):
    session_id = run_intake(client, issues=[])
    response = client.get(f"/plan/{session_id}")
    text = response.text
    assert response.status_code == 200
    assert "County records, pulled" in text
    assert "County records (partial)" not in text
    assert "County records were incomplete" not in text
    assert "1,850" in text


def test_user_corrected_fields_after_partial_attom(client, attom_partial):
    session_id = run_intake(client, issues=[])
    client.get(f"/plan/{session_id}")
    response = client.post(
        f"/plan/{session_id}/facts",
        data={"beds": "3", "baths": "2", "sqft": "2019", "year_built": "1999"},
        follow_redirects=True,
    )
    text = response.text
    assert response.status_code == 200
    assert "Confirmed by you" in text
    assert "County records were incomplete" not in text
    assert "2,019" in text
