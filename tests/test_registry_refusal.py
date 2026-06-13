"""The product must refuse unapproved model artifacts (D-V12-005)."""

from pathlib import Path

import pytest

from app.registry import (
    ModelArtifactInvalid,
    ModelArtifactNotApproved,
    load_approved_artifact,
)

GREENVILLE_ARTIFACT = (
    Path(__file__).resolve().parents[1]
    / "model_registry"
    / "greenville_sc"
    / "hedonic_ppsf_v0_1.json"
)


def test_greenville_diagnostic_artifact_is_refused():
    """The real diagnostic_only artifact must raise, exactly as governed."""
    assert GREENVILLE_ARTIFACT.exists(), "expected the Greenville artifact fixture"
    with pytest.raises(ModelArtifactNotApproved):
        load_approved_artifact(GREENVILLE_ARTIFACT)


def test_missing_artifact_is_invalid(tmp_path):
    with pytest.raises(ModelArtifactInvalid):
        load_approved_artifact(tmp_path / "nope.json")


def test_approved_artifact_loads(tmp_path):
    artifact = tmp_path / "approved.json"
    artifact.write_text(
        '{"model_id": "m", "version": "1", "market": "x", '
        '"status": "approved", "approved_for_recommendations": true}',
        encoding="utf-8",
    )
    assert load_approved_artifact(artifact)["model_id"] == "m"


def test_registry_not_imported_by_seller_facing_modules():
    """No seller-facing module may import the model registry loader.

    Static contract check: the registry stays unreachable from the report
    path until a model is explicitly approved (D-V12-005).
    """
    import re

    app_dir = Path(__file__).resolve().parents[1] / "app"
    seller_facing = ["main.py", "engine.py", "flow.py", "sessions.py"]
    import_pattern = re.compile(
        r"^\s*(?:import\s+app\.registry|from\s+app\.registry\s+import"
        r"|from\s+app\s+import\s+.*\bregistry\b)",
        re.MULTILINE,
    )
    for name in seller_facing:
        source = (app_dir / name).read_text(encoding="utf-8")
        assert not import_pattern.search(source), (
            f"app/{name} imports the model registry"
        )


def test_seller_flow_renders_without_registry(client, attom_down):
    from tests.conftest import run_intake

    session_id = run_intake(client, issues=["roof_leak"])
    response = client.get(f"/plan/{session_id}")
    assert response.status_code == 200
