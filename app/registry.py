"""Model artifact loader. v0 behavior: refusal.

Governing rule (Decisions Log V12 / Model Registry and Promotion Governance v1):
the product may consume a coefficient artifact only when it is versioned,
structurally valid, status == "approved", and approved_for_recommendations is
true via an explicit decision record.

This module is intentionally NOT imported by the engine or any seller-facing
route in the first build slice. Its presence (with tests) enforces the refusal
contract before any coefficient integration is attempted.
"""

from __future__ import annotations

import json
from pathlib import Path


class ModelArtifactNotApproved(RuntimeError):
    """Raised when an artifact is not approved for seller-facing recommendations."""


class ModelArtifactInvalid(RuntimeError):
    """Raised when an artifact is structurally unusable."""


REQUIRED_FIELDS = ("model_id", "market", "status", "approved_for_recommendations")
VERSION_FIELDS = ("version", "model_version")


def load_approved_artifact(path: str | Path) -> dict:
    """Load a model registry artifact, refusing anything not explicitly approved.

    Raises ModelArtifactNotApproved for diagnostic/candidate/retired artifacts.
    """
    path = Path(path)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ModelArtifactInvalid(f"artifact not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ModelArtifactInvalid(f"artifact is not valid JSON: {path}") from exc

    # Refusal comes first: unapproved artifacts must never load, regardless
    # of structural completeness (D-V12-005).
    status = data.get("status")
    approved = data.get("approved_for_recommendations")
    if status != "approved" or approved is not True:
        raise ModelArtifactNotApproved(
            f"artifact {data.get('model_id')!r} has status={status!r}, "
            f"approved_for_recommendations={approved!r}; "
            "recommendation use is prohibited (D-V12-005)."
        )

    missing = [field for field in REQUIRED_FIELDS if field not in data]
    if not any(field in data for field in VERSION_FIELDS):
        missing.append("version")
    if missing:
        raise ModelArtifactInvalid(
            f"artifact missing required fields {missing}: {path}"
        )
    return data
