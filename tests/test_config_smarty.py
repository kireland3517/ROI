"""Config defaults, adapter selection, fail-fast, and the real Smarty adapter."""

import pytest
import requests

from app import config
from app.adapters import smarty
from app.adapters.smarty import (
    AddressValidationError,
    MissingCredentialsError,
    SmartyAdapter,
    StubSmartyAdapter,
    get_adapter,
)

# ---------------------------------------------------------------- config


def test_app_env_defaults_to_development(monkeypatch):
    monkeypatch.delenv("APP_ENV", raising=False)
    assert config.app_env() == "development"


def test_app_env_rejects_unknown_values(monkeypatch):
    monkeypatch.setenv("APP_ENV", "staging-ish")
    assert config.app_env() == "development"


def test_demo_fallback_defaults_by_environment(monkeypatch):
    monkeypatch.delenv("USE_DEMO_FALLBACK", raising=False)
    monkeypatch.setenv("APP_ENV", "development")
    assert config.use_demo_fallback() is True
    monkeypatch.setenv("APP_ENV", "production")
    assert config.use_demo_fallback() is False


def test_demo_fallback_explicit_overrides(monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("USE_DEMO_FALLBACK", "true")
    assert config.use_demo_fallback() is True
    monkeypatch.setenv("APP_ENV", "development")
    monkeypatch.setenv("USE_DEMO_FALLBACK", "false")
    assert config.use_demo_fallback() is False


def test_smarty_credentials_require_both(monkeypatch):
    monkeypatch.setenv("SMARTY_AUTH_ID", "id-only")
    monkeypatch.delenv("SMARTY_AUTH_TOKEN", raising=False)
    assert config.smarty_credentials() is None
    monkeypatch.setenv("SMARTY_AUTH_TOKEN", "tok")
    assert config.smarty_credentials() == ("id-only", "tok")


# ---------------------------------------------------------------- adapter selection


def test_demo_mode_without_keys_returns_stub():
    assert isinstance(get_adapter(), StubSmartyAdapter)


def test_credentials_select_real_adapter(monkeypatch):
    monkeypatch.setenv("SMARTY_AUTH_ID", "test-id")
    monkeypatch.setenv("SMARTY_AUTH_TOKEN", "test-token")
    adapter = get_adapter()
    assert isinstance(adapter, SmartyAdapter)
    assert adapter.provider == "smarty"


def test_production_without_keys_fails_clearly(monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("USE_DEMO_FALLBACK", "false")
    with pytest.raises(MissingCredentialsError) as excinfo:
        get_adapter()
    assert "SMARTY_AUTH_ID" in str(excinfo.value)


def test_demo_false_in_development_also_fails(monkeypatch):
    monkeypatch.setenv("USE_DEMO_FALLBACK", "false")
    with pytest.raises(MissingCredentialsError):
        get_adapter()


# ---------------------------------------------------------------- real adapter (mocked HTTP)


class FakeResponse:
    def __init__(self, status_code=200, payload=None):
        self.status_code = status_code
        self._payload = payload

    def json(self):
        if isinstance(self._payload, Exception):
            raise self._payload
        return self._payload


def test_smarty_adapter_maps_candidate(monkeypatch):
    payload = [
        {
            "delivery_line_1": "123 Maple St",
            "components": {
                "city_name": "Springfield",
                "state_abbreviation": "IL",
                "zipcode": "62704",
            },
        }
    ]
    captured = {}

    def fake_get(url, params=None, timeout=None):
        captured["params"] = params
        return FakeResponse(200, payload)

    monkeypatch.setattr(smarty.requests, "get", fake_get)
    adapter = SmartyAdapter("id", "tok")
    result = adapter.validate("123 maple street, springfield il 62704")
    assert result.line1 == "123 Maple St"
    assert result.city == "Springfield"
    assert result.state == "IL"
    assert result.zip_code == "62704"
    assert result.provider == "smarty"
    assert captured["params"]["candidates"] == 1
    assert captured["params"]["auth-id"] == "id"


def test_smarty_adapter_blocks_on_no_candidates(monkeypatch):
    monkeypatch.setattr(
        smarty.requests, "get", lambda *a, **k: FakeResponse(200, [])
    )
    with pytest.raises(AddressValidationError):
        SmartyAdapter("id", "tok").validate("1 Nowhere Rd, 00000")


def test_smarty_adapter_blocks_on_http_error(monkeypatch):
    monkeypatch.setattr(
        smarty.requests, "get", lambda *a, **k: FakeResponse(401, [])
    )
    with pytest.raises(AddressValidationError):
        SmartyAdapter("bad", "creds").validate("123 Maple St, Springfield, IL 62704")


def test_smarty_adapter_blocks_on_network_failure(monkeypatch):
    def boom(*args, **kwargs):
        raise requests.ConnectionError("down")

    monkeypatch.setattr(smarty.requests, "get", boom)
    with pytest.raises(AddressValidationError):
        SmartyAdapter("id", "tok").validate("123 Maple St, Springfield, IL 62704")


def test_smarty_adapter_blocks_on_empty_input():
    with pytest.raises(AddressValidationError):
        SmartyAdapter("id", "tok").validate("   ")


# ---------------------------------------------------------------- flow integration


def test_flow_uses_real_adapter_when_credentialed(client, monkeypatch):
    monkeypatch.setenv("SMARTY_AUTH_ID", "test-id")
    monkeypatch.setenv("SMARTY_AUTH_TOKEN", "test-token")
    payload = [
        {
            "delivery_line_1": "123 Maple St",
            "components": {
                "city_name": "Springfield",
                "state_abbreviation": "IL",
                "zipcode": "62704",
            },
        }
    ]
    monkeypatch.setattr(
        smarty.requests, "get", lambda *a, **k: FakeResponse(200, payload)
    )
    response = client.post(
        "/intake/address",
        data={"address": "123 maple street springfield il"},
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert "USPS-standardized" in response.text


def test_flow_keyless_still_renders_report(client, attom_down):
    """Requirement 3 + 6: no keys, demo mode — full report still generates."""
    from tests.conftest import run_intake

    session_id = run_intake(client, issues=["roof_leak"])
    response = client.get(f"/plan/{session_id}")
    assert response.status_code == 200
    assert "Your Seller Action Plan" in response.text
