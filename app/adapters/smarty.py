"""Address validation gate (PRD §2.1).

The user must confirm a standardized address before any ATTOM or downstream
query. With SMARTY_AUTH_ID / SMARTY_AUTH_TOKEN present, the real Smarty US
Street API standardizes the address. Without credentials, a stub adapter
runs behind the same interface — but only when USE_DEMO_FALLBACK allows it;
in production the gate must never silently run on the stub.

Credentials come from environment variables only. No secrets in code.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

import requests

from app import config


class AddressValidationError(Exception):
    """The address could not be validated. The flow must block (PRD §2.1)."""

    user_message = (
        "We couldn't validate that address. "
        "Check the street number and ZIP, then try again."
    )


class MissingCredentialsError(RuntimeError):
    """Raised when production configuration forbids running without Smarty."""


@dataclass(frozen=True)
class AddressSuggestion:
    """A typeahead suggestion. Convenience only — never a validation result."""

    street_line: str
    secondary: str
    city: str
    state: str
    zip_code: str

    @property
    def display(self) -> str:
        street = " ".join(p for p in (self.street_line, self.secondary) if p)
        locality = " ".join(p for p in (self.state, self.zip_code) if p)
        return ", ".join(p for p in (street, self.city, locality) if p)


@dataclass(frozen=True)
class StandardizedAddress:
    line1: str
    city: str
    state: str
    zip_code: str
    provider: str  # "smarty" | "stub"

    @property
    def line2(self) -> str:
        locality = " ".join(p for p in (self.state, self.zip_code) if p)
        return ", ".join(p for p in (self.city, locality) if p)

    @property
    def display(self) -> str:
        return ", ".join(p for p in (self.line1, self.line2) if p)


_STREET_SUFFIXES = {
    "street": "St",
    "avenue": "Ave",
    "drive": "Dr",
    "road": "Rd",
    "lane": "Ln",
    "court": "Ct",
    "boulevard": "Blvd",
    "circle": "Cir",
    "place": "Pl",
    "trail": "Trl",
    "parkway": "Pkwy",
    "highway": "Hwy",
    "terrace": "Ter",
    "way": "Way",
}

_DIRECTIONS = {"n", "s", "e", "w", "ne", "nw", "se", "sw"}
_ZIP_RE = re.compile(r"\b(\d{5})(?:-\d{4})?\b")
_STREET_RE = re.compile(r"^\d+[\w-]*\s+\S+")


def _title_street(line: str) -> str:
    words = []
    for word in line.split():
        bare = word.rstrip(".").lower()
        if bare in _STREET_SUFFIXES:
            words.append(_STREET_SUFFIXES[bare])
        elif bare in _DIRECTIONS:
            words.append(bare.upper())
        elif re.fullmatch(r"\d+[\w-]*", word):
            words.append(word)
        else:
            words.append(word.capitalize())
    return " ".join(words)


class StubSmartyAdapter:
    """Heuristic standardization behind the Smarty interface.

    Accepts addresses with a street number + name and either a 5-digit ZIP
    or a city + 2-letter state. Anything else blocks, exactly as a failed
    Smarty lookup would.
    """

    provider = "stub"

    def validate(self, raw_address: str) -> StandardizedAddress:
        raw = (raw_address or "").strip()
        parts = [p.strip() for p in raw.split(",") if p.strip()]
        if not parts or not _STREET_RE.match(parts[0]):
            raise AddressValidationError()

        street = _title_street(parts[0])
        remainder = " ".join(parts[1:])

        zip_match = _ZIP_RE.search(remainder)
        zip_code = zip_match.group(1) if zip_match else ""
        remainder = _ZIP_RE.sub("", remainder).strip().strip(",").strip()

        state = ""
        tokens = remainder.split()
        if tokens and re.fullmatch(r"[A-Za-z]{2}", tokens[-1]):
            state = tokens[-1].upper()
            tokens = tokens[:-1]
        city = " ".join(tokens).title()

        if not zip_code and not (city and state):
            raise AddressValidationError()

        return StandardizedAddress(
            line1=street,
            city=city,
            state=state,
            zip_code=zip_code,
            provider=self.provider,
        )

    def suggest(self, text: str) -> list[AddressSuggestion]:
        """Demo mode shows no suggestions — never fake USPS data (D: approved)."""
        return []


class SmartyAdapter:
    """Real USPS standardization via the Smarty US Street Address API."""

    provider = "smarty"
    API_URL = "https://us-street.api.smarty.com/street-address"
    AUTOCOMPLETE_URL = "https://us-autocomplete-pro.api.smarty.com/lookup"
    TIMEOUT_SECONDS = 10
    SUGGEST_TIMEOUT_SECONDS = 5
    MIN_SUGGEST_CHARS = 4
    MAX_SUGGESTIONS = 5

    def __init__(self, auth_id: str, auth_token: str):
        self._auth_id = auth_id
        self._auth_token = auth_token

    def validate(self, raw_address: str) -> StandardizedAddress:
        raw = (raw_address or "").strip()
        if not raw:
            raise AddressValidationError()

        params = {
            "auth-id": self._auth_id,
            "auth-token": self._auth_token,
            "street": raw,  # freeform single-line input
            "candidates": 1,
            "match": "strict",
        }
        try:
            response = requests.get(
                self.API_URL, params=params, timeout=self.TIMEOUT_SECONDS
            )
        except requests.RequestException as exc:
            # A Smarty outage blocks the gate (PRD §2.1) — never invent data.
            raise AddressValidationError() from exc
        if response.status_code != 200:
            raise AddressValidationError()

        try:
            candidates = response.json()
        except ValueError as exc:
            raise AddressValidationError() from exc
        if not isinstance(candidates, list) or not candidates:
            raise AddressValidationError()

        candidate = candidates[0]
        components = candidate.get("components", {})
        line1 = (candidate.get("delivery_line_1") or "").strip()
        if not line1:
            raise AddressValidationError()

        return StandardizedAddress(
            line1=line1,
            city=(components.get("city_name") or "").strip(),
            state=(components.get("state_abbreviation") or "").strip(),
            zip_code=(components.get("zipcode") or "").strip(),
            provider=self.provider,
        )

    def suggest(self, text: str) -> list[AddressSuggestion]:
        """Typeahead via the Smarty US Autocomplete Pro API.

        Best-effort only: any failure (no subscription, outage, bad payload)
        returns an empty list so typing is never blocked. The strict
        validation gate at submit time is unaffected.
        """
        query = (text or "").strip()
        if len(query) < self.MIN_SUGGEST_CHARS:
            return []

        params = {
            "auth-id": self._auth_id,
            "auth-token": self._auth_token,
            "search": query,
            "max_results": self.MAX_SUGGESTIONS,
        }
        license_value = config.smarty_license()
        if license_value:
            params["license"] = license_value
        try:
            response = requests.get(
                self.AUTOCOMPLETE_URL, params=params,
                timeout=self.SUGGEST_TIMEOUT_SECONDS,
            )
        except requests.RequestException:
            return []
        if response.status_code != 200:
            return []
        try:
            payload = response.json()
        except ValueError:
            return []

        suggestions = []
        for raw in (payload.get("suggestions") or [])[: self.MAX_SUGGESTIONS]:
            if not isinstance(raw, dict):
                continue
            street = (raw.get("street_line") or "").strip()
            if not street:
                continue
            suggestions.append(
                AddressSuggestion(
                    street_line=street,
                    secondary=(raw.get("secondary") or "").strip(),
                    city=(raw.get("city") or "").strip(),
                    state=(raw.get("state") or "").strip(),
                    zip_code=(raw.get("zipcode") or "").strip(),
                )
            )
        return suggestions


def get_adapter() -> SmartyAdapter | StubSmartyAdapter:
    """Return the configured address validation adapter.

    - Credentials present: real Smarty adapter.
    - Credentials missing + demo fallback allowed: stub (development only).
    - Credentials missing + demo fallback forbidden: fail clearly — the
      production validation gate must never run on the stub.
    """
    credentials = config.smarty_credentials()
    if credentials:
        return SmartyAdapter(*credentials)
    if config.use_demo_fallback():
        return StubSmartyAdapter()
    raise MissingCredentialsError(
        "SMARTY_AUTH_ID and SMARTY_AUTH_TOKEN are required when "
        "USE_DEMO_FALLBACK is false (APP_ENV="
        f"{config.app_env()}). Set the credentials in the environment, "
        "or set USE_DEMO_FALLBACK=true for demo mode."
    )
