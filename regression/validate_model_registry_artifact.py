import json
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ARTIFACT = (
    PROJECT_ROOT / "model_registry" / "greenville_sc" / "hedonic_ppsf_v0_1.json"
)
REPORT_PATH = PROJECT_ROOT / "regression" / "output" / "model_registry_validation_report.json"

REQUIRED_FIELDS = [
    "model_id",
    "model_version",
    "market",
    "model_type",
    "target",
    "training_window",
    "training_rows",
    "train_rows",
    "test_rows",
    "status",
    "approved_for_recommendations",
    "intercept",
    "feature_names",
    "input_features",
    "coefficients",
    "source_dataset_path",
    "modeling_dataset_path",
    "created_at",
]

REQUIRED_METRICS = [
    "train_r2",
    "test_r2",
    "test_mae_log_price_per_sqft",
    "test_rmse_log_price_per_sqft",
]


def resolve_local_path(path_value: str) -> Path:
    path = Path(path_value)
    if path.exists():
        return path

    relative = PROJECT_ROOT / path.name
    if relative.exists():
        return relative

    if path.is_absolute():
        project_relative = PROJECT_ROOT / path.relative_to(path.anchor).parts[-1]
        if len(path.parts) >= 2:
            candidate = PROJECT_ROOT.joinpath(*path.parts[-3:])
            if candidate.exists():
                return candidate

    return path


def add_check(checks: list[dict], name: str, passed: bool, message: str) -> None:
    checks.append(
        {
            "name": name,
            "status": "PASS" if passed else "FAIL",
            "message": message,
        }
    )


def validate_artifact(artifact_path: Path) -> dict:
    checks: list[dict] = []

    if not artifact_path.exists():
        add_check(checks, "artifact_exists", False, f"Artifact not found: {artifact_path}")
        return build_report(artifact_path, checks)

    add_check(checks, "artifact_exists", True, f"Found artifact: {artifact_path}")

    with artifact_path.open(encoding="utf-8") as handle:
        artifact = json.load(handle)

    missing_fields = [field for field in REQUIRED_FIELDS if field not in artifact]
    add_check(
        checks,
        "required_fields_present",
        not missing_fields,
        "All required fields present"
        if not missing_fields
        else f"Missing required fields: {', '.join(missing_fields)}",
    )

    training_window = artifact.get("training_window", {})
    window_ok = bool(training_window.get("start_date")) and bool(
        training_window.get("end_date")
    )
    add_check(
        checks,
        "training_window_present",
        window_ok,
        "training_window includes start_date and end_date"
        if window_ok
        else "training_window must include start_date and end_date",
    )

    missing_metrics = [metric for metric in REQUIRED_METRICS if metric not in artifact]
    add_check(
        checks,
        "required_metrics_present",
        not missing_metrics,
        "All required metrics present"
        if not missing_metrics
        else f"Missing required metrics: {', '.join(missing_metrics)}",
    )

    coefficients = artifact.get("coefficients", {})
    coefficients_ok = isinstance(coefficients, dict) and len(coefficients) > 0
    add_check(
        checks,
        "coefficients_non_empty",
        coefficients_ok,
        f"Found {len(coefficients)} coefficients"
        if coefficients_ok
        else "coefficients must be a non-empty object",
    )

    feature_names = artifact.get("feature_names", [])
    feature_names_ok = isinstance(feature_names, list) and len(feature_names) > 0
    add_check(
        checks,
        "feature_names_non_empty",
        feature_names_ok,
        f"Found {len(feature_names)} feature names"
        if feature_names_ok
        else "feature_names must be a non-empty list",
    )

    if coefficients_ok and feature_names_ok:
        coeff_keys = set(coefficients.keys())
        feature_set = set(feature_names)
        keys_match = coeff_keys == feature_set
        add_check(
            checks,
            "coefficients_match_feature_names",
            keys_match,
            "coefficients keys match feature_names"
            if keys_match
            else (
                f"Key mismatch: {len(coeff_keys - feature_set)} extra coefficient keys, "
                f"{len(feature_set - coeff_keys)} missing coefficient keys"
            ),
        )

    status = artifact.get("status")
    approved = artifact.get("approved_for_recommendations")
    diagnostic_not_approved = not (
        status == "diagnostic_only" and approved is True
    )
    add_check(
        checks,
        "diagnostic_only_not_approved",
        diagnostic_not_approved,
        "diagnostic_only model is not approved for recommendations"
        if diagnostic_not_approved
        else "diagnostic_only models must have approved_for_recommendations=false",
    )

    if status == "diagnostic_only":
        add_check(
            checks,
            "diagnostic_only_flag_false",
            approved is False,
            "approved_for_recommendations is false"
            if approved is False
            else "approved_for_recommendations must be false for diagnostic_only models",
        )

    source_path = resolve_local_path(str(artifact.get("source_dataset_path", "")))
    modeling_path = resolve_local_path(str(artifact.get("modeling_dataset_path", "")))

    add_check(
        checks,
        "source_dataset_exists",
        source_path.exists(),
        f"Source dataset found: {source_path}"
        if source_path.exists()
        else f"Source dataset missing: {artifact.get('source_dataset_path')}",
    )
    add_check(
        checks,
        "modeling_dataset_exists",
        modeling_path.exists(),
        f"Modeling dataset found: {modeling_path}"
        if modeling_path.exists()
        else f"Modeling dataset missing: {artifact.get('modeling_dataset_path')}",
    )

    return build_report(artifact_path, checks, artifact.get("model_id"))


def build_report(
    artifact_path: Path,
    checks: list[dict],
    model_id: str | None = None,
) -> dict:
    overall_pass = all(check["status"] == "PASS" for check in checks)
    return {
        "artifact_path": str(artifact_path),
        "model_id": model_id,
        "validated_at": datetime.now().isoformat(timespec="seconds"),
        "overall_status": "PASS" if overall_pass else "FAIL",
        "checks": checks,
    }


def print_report(report: dict) -> None:
    print("=== Model Registry Artifact Validation ===")
    print(f"Artifact: {report['artifact_path']}")
    if report.get("model_id"):
        print(f"Model ID: {report['model_id']}")
    print(f"Overall: {report['overall_status']}")
    print()
    for check in report["checks"]:
        print(f"[{check['status']}] {check['name']}: {check['message']}")


def main() -> None:
    report = validate_artifact(DEFAULT_ARTIFACT)
    print_report(report)

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with REPORT_PATH.open("w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2)
    print()
    print(f"Saved validation report: {REPORT_PATH}")

    if report["overall_status"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
