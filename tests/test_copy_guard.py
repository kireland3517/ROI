"""Seller-facing output must contain no market literals or model internals."""

import re

from tests.conftest import run_intake

BANNED = (
    "simpsonville",
    "greenville",
    "kingfisher",
    "29680",
    "tier 1",
    "tier 2",
    "tier 3",
    "coefficient",
    "regression",
    "registry",
    "diagnostic_only",
)


def _strip_static_refs(html: str) -> str:
    # CSS/JS file paths aren't seller copy.
    return re.sub(r"/static/\S+", "", html)


def test_rendered_plan_contains_no_banned_vocabulary(client, attom_down):
    session_id = run_intake(
        client, issues=["roof_leak", "mold", "hvac_old", "gutters"]
    )
    response = client.get(f"/plan/{session_id}")
    assert response.status_code == 200
    text = _strip_static_refs(response.text).lower()
    for banned in BANNED:
        assert banned not in text, f"banned string {banned!r} in seller-facing output"


def test_intake_screens_contain_no_banned_vocabulary(client):
    pages = [client.get("/").text]
    response = client.post(
        "/intake/address",
        data={"address": "123 Maple Street, Springfield, IL 62704"},
        follow_redirects=True,
    )
    pages.append(response.text)
    for page in pages:
        text = _strip_static_refs(page).lower()
        for banned in BANNED:
            assert banned not in text, f"banned string {banned!r} in intake output"
