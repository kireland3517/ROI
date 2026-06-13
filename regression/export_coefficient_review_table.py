import json
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ARTIFACT = (
    PROJECT_ROOT / "model_registry" / "greenville_sc" / "hedonic_ppsf_v0_1.json"
)
DEFAULT_OUTPUT = (
    PROJECT_ROOT / "regression" / "output" / "greenville_coefficient_review_table.xlsx"
)


def load_model_artifact(artifact_path: Path) -> dict:
    if not artifact_path.exists():
        raise FileNotFoundError(f"Model artifact not found: {artifact_path}")
    with artifact_path.open(encoding="utf-8") as handle:
        return json.load(handle)


def parse_feature_parts(model_feature_name: str) -> tuple[str, str, str]:
    if model_feature_name == "(intercept)":
        return "intercept", "intercept", "(intercept)"

    if model_feature_name.startswith("num__"):
        input_feature = model_feature_name.removeprefix("num__")
        return "numeric", input_feature, model_feature_name

    if model_feature_name.startswith("cat__"):
        raw = model_feature_name.removeprefix("cat__")
        if raw.startswith("postal1_"):
            return "categorical", "postal1", model_feature_name
        input_feature = raw.split("_", 1)[0]
        return "categorical", input_feature, model_feature_name

    return "other", model_feature_name, model_feature_name


def build_model_metadata_rows(artifact: dict) -> pd.DataFrame:
    training_window = artifact.get("training_window", {})
    rows = [
        ("model_id", artifact.get("model_id")),
        ("model_version", artifact.get("model_version")),
        ("market", artifact.get("market")),
        ("model_type", artifact.get("model_type")),
        ("target", artifact.get("target")),
        ("status", artifact.get("status")),
        ("approved_for_recommendations", artifact.get("approved_for_recommendations")),
        ("training_window_start", training_window.get("start_date")),
        ("training_window_end", training_window.get("end_date")),
        ("training_rows", artifact.get("training_rows")),
        ("train_rows", artifact.get("train_rows")),
        ("test_rows", artifact.get("test_rows")),
        ("train_r2", artifact.get("train_r2")),
        ("test_r2", artifact.get("test_r2")),
        ("test_mae_log_price_per_sqft", artifact.get("test_mae_log_price_per_sqft")),
        ("test_rmse_log_price_per_sqft", artifact.get("test_rmse_log_price_per_sqft")),
        ("test_mae_pct_price_per_sqft", artifact.get("test_mae_pct_price_per_sqft")),
        ("intercept", artifact.get("intercept")),
        ("source_dataset_path", artifact.get("source_dataset_path")),
        ("modeling_dataset_path", artifact.get("modeling_dataset_path")),
        ("created_at", artifact.get("created_at")),
        ("notes", artifact.get("notes")),
        ("json_source_of_truth", str(DEFAULT_ARTIFACT)),
    ]
    return pd.DataFrame(rows, columns=["field", "value"])


def build_preprocessing_rows(artifact: dict) -> pd.DataFrame:
    preprocessing = artifact.get("preprocessing", {})
    numeric_features = preprocessing.get("numeric_features_standardized", [])
    categorical_features = preprocessing.get(
        "categorical_features_one_hot_encoded", []
    )

    rows = [
        (
            "numeric_features_standardized",
            ", ".join(numeric_features),
            "StandardScaler applied before Ridge fit",
        ),
        (
            "categorical_features_one_hot_encoded",
            ", ".join(categorical_features),
            "OneHotEncoder(handle_unknown='ignore') applied before Ridge fit",
        ),
        ("review_note", artifact.get("notes", ""), "Model-level preprocessing note"),
    ]
    return pd.DataFrame(
        rows,
        columns=["preprocessing_item", "features", "notes"],
    )


def build_coefficient_review_table(artifact: dict) -> pd.DataFrame:
    training_window = artifact.get("training_window", {})
    preprocessing = artifact.get("preprocessing", {})
    numeric_features = set(preprocessing.get("numeric_features_standardized", []))
    preprocessing_notes = artifact.get("notes", "")

    shared_metadata = {
        "model_id": artifact.get("model_id"),
        "model_version": artifact.get("model_version"),
        "market": artifact.get("market"),
        "model_type": artifact.get("model_type"),
        "target": artifact.get("target"),
        "status": artifact.get("status"),
        "approved_for_recommendations": artifact.get("approved_for_recommendations"),
        "training_window_start": training_window.get("start_date"),
        "training_window_end": training_window.get("end_date"),
        "training_rows": artifact.get("training_rows"),
        "train_r2": artifact.get("train_r2"),
        "test_r2": artifact.get("test_r2"),
        "created_at": artifact.get("created_at"),
        "preprocessing_notes": preprocessing_notes,
    }

    coefficient_rows: list[dict] = []
    coefficients = artifact.get("coefficients", {})

    intercept_row = {
        **shared_metadata,
        "row_type": "intercept",
        "feature_group": "intercept",
        "input_feature": "(intercept)",
        "model_feature_name": "(intercept)",
        "coefficient_value": artifact.get("intercept"),
        "abs_coefficient_value": abs(float(artifact.get("intercept", 0) or 0)),
        "is_standardized_input": False,
        "is_one_hot_category": False,
    }
    coefficient_rows.append(intercept_row)

    for model_feature_name in artifact.get("feature_names", coefficients.keys()):
        feature_group, input_feature, parsed_name = parse_feature_parts(
            model_feature_name
        )
        value = coefficients.get(model_feature_name)
        coefficient_rows.append(
            {
                **shared_metadata,
                "row_type": "coefficient",
                "feature_group": feature_group,
                "input_feature": input_feature,
                "model_feature_name": parsed_name,
                "coefficient_value": value,
                "abs_coefficient_value": abs(float(value or 0)),
                "is_standardized_input": input_feature in numeric_features,
                "is_one_hot_category": feature_group == "categorical",
            }
        )

    review_df = pd.DataFrame(coefficient_rows)
    review_df["_sort_rank"] = review_df["row_type"].map(
        {"intercept": 0, "coefficient": 1}
    ).fillna(2)
    review_df = review_df.sort_values(
        ["_sort_rank", "abs_coefficient_value"],
        ascending=[True, False],
    ).drop(columns="_sort_rank").reset_index(drop=True)
    return review_df


def export_coefficient_review_workbook(
    artifact_path: Path = DEFAULT_ARTIFACT,
    output_path: Path = DEFAULT_OUTPUT,
) -> Path:
    artifact = load_model_artifact(artifact_path)
    metadata_df = build_model_metadata_rows(artifact)
    preprocessing_df = build_preprocessing_rows(artifact)
    coefficients_df = build_coefficient_review_table(artifact)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        metadata_df.to_excel(writer, sheet_name="Model Metadata", index=False)
        preprocessing_df.to_excel(writer, sheet_name="Preprocessing", index=False)
        coefficients_df.to_excel(writer, sheet_name="Coefficient Review", index=False)

        for sheet_name in writer.sheets:
            worksheet = writer.sheets[sheet_name]
            worksheet.freeze_panes = "A2"
            worksheet.auto_filter.ref = worksheet.dimensions

    return output_path


def main() -> None:
    output_path = export_coefficient_review_workbook()
    artifact = load_model_artifact(DEFAULT_ARTIFACT)
    coefficient_count = len(artifact.get("coefficients", {}))

    print("=== Coefficient Review Table Export ===")
    print(f"JSON source of truth: {DEFAULT_ARTIFACT}")
    print(f"Workbook output: {output_path}")
    print(f"Model: {artifact.get('model_id')}")
    print(f"Status: {artifact.get('status')}")
    print(f"Approved for recommendations: {artifact.get('approved_for_recommendations')}")
    print(f"Coefficient rows exported: {coefficient_count + 1} (includes intercept)")
    print()
    print("Sheets:")
    print("  - Model Metadata")
    print("  - Preprocessing")
    print("  - Coefficient Review")


if __name__ == "__main__":
    main()
