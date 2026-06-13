"""Address typeahead: server-side proxy, graceful degradation, no secrets."""

import requests

from app.adapters import smarty
from app.adapters.smarty import SmartyAdapter


class FakeResponse:
    def __init__(self, status_code=200, payload=None):
        self.status_code = status_code
        self._payload = payload

    def json(self):
        return self._payload


SUGGESTION_PAYLOAD = {
    "suggestions": [
        {
            "street_line": "130 Kingfisher Dr",
            "secondary": "",
            "city": "Simpsonville",
            "state": "SC",
            "zipcode": "29680",
        },
        {
            "street_line": "130 Kingfisher Way",
            "secondary": "Apt 2",
            "city": "Greenville",
            "state": "SC",
            "zipcode": "29607",
        },
    ]
}


# ---------------------------------------------------------------- adapter


def test_suggest_maps_payload(monkeypatch):
    monkeypatch.setattr(
        smarty.requests, "get", lambda *a, **k: FakeResponse(200, SUGGESTION_PAYLOAD)
    )
    suggestions = SmartyAdapter("id", "tok").suggest("130 kingfisher")
    assert [s.display for s in suggestions] == [
        "130 Kingfisher Dr, Simpsonville, SC 29680",
        "130 Kingfisher Way Apt 2, Greenville, SC 29607",
    ]


def test_suggest_empty_on_missing_subscription(monkeypatch):
    monkeypatch.setattr(
        smarty.requests, "get", lambda *a, **k: FakeResponse(402, {"errors": []})
    )
    assert SmartyAdapter("id", "tok").suggest("130 kingfisher") == []


def test_suggest_empty_on_network_failure(monkeypatch):
    def boom(*args, **kwargs):
        raise requests.ConnectionError("down")

    monkeypatch.setattr(smarty.requests, "get", boom)
    assert SmartyAdapter("id", "tok").suggest("130 kingfisher") == []


def test_suggest_skips_short_input_without_calling_api(monkeypatch):
    def fail(*args, **kwargs):
        raise AssertionError("API must not be called for short input")

    monkeypatch.setattr(smarty.requests, "get", fail)
    assert SmartyAdapter("id", "tok").suggest("13") == []


def test_stub_adapter_never_suggests():
    assert smarty.StubSmartyAdapter().suggest("130 kingfisher drive") == []


# ---------------------------------------------------------------- proxy route


def test_suggest_includes_license_when_configured(monkeypatch):
    captured = {}

    def fake_get(url, params=None, timeout=None):
        captured["params"] = params
        return FakeResponse(200, SUGGESTION_PAYLOAD)

    monkeypatch.setenv("SMARTY_LICENSE", "us-autocomplete-pro-cloud")
    monkeypatch.setattr(smarty.requests, "get", fake_get)
    SmartyAdapter("id", "tok").suggest("130 kingfisher")
    assert captured["params"]["license"] == "us-autocomplete-pro-cloud"


def test_route_returns_suggestions_with_credentials(client, monkeypatch):
    monkeypatch.setenv("SMARTY_AUTH_ID", "test-id")
    monkeypatch.setenv("SMARTY_AUTH_TOKEN", "test-secret-token")
    monkeypatch.setattr(
        smarty.requests, "get", lambda *a, **k: FakeResponse(200, SUGGESTION_PAYLOAD)
    )
    response = client.get("/api/address-suggestions", params={"q": "130 kingfisher"})
    assert response.status_code == 200
    data = response.json()
    assert data["suggestions"][0]["display"] == "130 Kingfisher Dr, Simpsonville, SC 29680"
    # Requirement: no secrets ever reach the browser.
    assert "test-secret-token" not in response.text
    assert "test-id" not in response.text


def test_route_empty_in_demo_mode(client):
    response = client.get("/api/address-suggestions", params={"q": "130 kingfisher"})
    assert response.status_code == 200
    assert response.json() == {"suggestions": []}


def test_route_empty_for_short_query(client):
    response = client.get("/api/address-suggestions", params={"q": "13"})
    assert response.status_code == 200
    assert response.json() == {"suggestions": []}


def test_route_never_500s_when_production_misconfigured(client, monkeypatch):
    """Typeahead degrades; the strict submit path still fails clearly."""
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("USE_DEMO_FALLBACK", "false")
    response = client.get("/api/address-suggestions", params={"q": "130 kingfisher"})
    assert response.status_code == 200
    assert response.json() == {"suggestions": []}


def test_address_page_contains_no_credentials(client, monkeypatch):
    monkeypatch.setenv("SMARTY_AUTH_ID", "test-id")
    monkeypatch.setenv("SMARTY_AUTH_TOKEN", "test-secret-token")
    page = client.get("/").text
    assert "test-secret-token" not in page
    assert "auth-token" not in page
