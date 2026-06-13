"""Runtime configuration. Environment variables only — no secrets in code.

Local development reads a .env file (loaded by app.main via python-dotenv,
which never overrides real process env). On Railway, service variables are
injected directly into the process environment.
"""

from __future__ import annotations

import os

_TRUTHY = {"1", "true", "yes", "on"}
_FALSY = {"0", "false", "no", "off"}


def app_env() -> str:
    """'development' (default) or 'production'."""
    value = os.getenv("APP_ENV", "development").strip().lower()
    return value if value in {"development", "production"} else "development"


def use_demo_fallback() -> bool:
    """Whether the app may run without API credentials.

    Default: true in development, false in production. When false, missing
    Smarty credentials are a configuration error (the validation gate must
    never silently run on the stub in production).
    """
    raw = os.getenv("USE_DEMO_FALLBACK", "").strip().lower()
    if raw in _TRUTHY:
        return True
    if raw in _FALSY:
        return False
    return app_env() == "development"


def smarty_credentials() -> tuple[str, str] | None:
    auth_id = (os.getenv("SMARTY_AUTH_ID") or "").strip()
    auth_token = (os.getenv("SMARTY_AUTH_TOKEN") or "").strip()
    if auth_id and auth_token:
        return auth_id, auth_token
    return None


def smarty_license() -> str | None:
    """Optional Smarty license slug for Autocomplete Pro (from Subscriptions page).

    Only needed when your account has multiple licenses that apply to the same
    API call. If omitted, Smarty picks the applicable subscription automatically.
    """
    value = (os.getenv("SMARTY_LICENSE") or "").strip()
    return value or None


def attom_api_key() -> str | None:
    key = (os.getenv("ATTOM_API_KEY") or "").strip()
    return key or None
