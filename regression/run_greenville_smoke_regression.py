import json
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

PROJECT_ROOT = Path(__file__).resolve().parents[1]
INPUT_CSV = PROJECT_ROOT / "regression" / "data" / "Greenville-Anderson-Greer_SC.csv"
OUTPUT_DIR = PROJECT_ROOT / "regression" / "output"
MODELING_DATASET = OUTPUT_DIR / "greenville_modeling_dataset.csv"
DIAGNOSTICS_JSON = OUTPUT_DIR / "greenville_smoke_regression_diagnostics.json"
MODEL_REGISTRY_DIR = PROJECT_ROOT / "model_registry" / "greenville_sc"
MODEL_ARTIFACT = MODEL_REGISTRY_DIR / "hedonic_ppsf_v0_1.json"

MODEL_ID = "greenville_sc_hedonic_ppsf_v0_1"
MODEL_VERSION = "v0_1"
MARKET = "Greenville-Anderson-Greer, SC"
MODEL_TYPE = "ridge_regression"
TARGET = "log_price_per_sqft"

FILTER_START = "2024-01-01"
FILTER_END = "2026-06-03"
MIN_YEAR_BUILT = 1850
MAX_YEAR_BUILT = datetime.now().year
RANDOM_STATE = 42


def load_raw_data() -> pd.DataFrame:
    if not INPUT_CSV.exists():
        raise FileNotFoundError(
            f"Expected fixture not found: {INPUT_CSV}. "
            "Copy Greenville-Anderson-Greer_SC.csv into regression/data/."
        )
    return pd.read_csv(INPUT_CSV)


def apply_cleaning_filters(df: pd.DataFrame) -> pd.DataFrame:
    cleaned = df.copy()
    cleaned["sale_date"] = pd.to_datetime(cleaned["sale_date"], errors="coerce")

    cleaned = cleaned[cleaned["sale_date"].notna()]
    cleaned = cleaned[cleaned["sale_date"].between(FILTER_START, FILTER_END)]

    numeric_checks = {
        "sale_amount": (0, np.inf),
        "price_per_sqft": (0, np.inf),
        "sqft": (0, np.inf),
        "beds": (0, np.inf),
        "baths": (0, np.inf),
        "year_built": (MIN_YEAR_BUILT, MAX_YEAR_BUILT),
    }
    for column, (lower, upper) in numeric_checks.items():
        values = pd.to_numeric(cleaned[column], errors="coerce")
        cleaned = cleaned[values.notna() & values.between(lower, upper)]

    cleaned["sale_year"] = cleaned["sale_date"].dt.year
    cleaned["sale_month"] = cleaned["sale_date"].dt.month
    cleaned["property_age"] = cleaned["sale_year"] - cleaned["year_built"]
    cleaned = cleaned[cleaned["property_age"] >= 0]

    cleaned["log_price_per_sqft"] = np.log(cleaned["price_per_sqft"])
    cleaned = cleaned[np.isfinite(cleaned["log_price_per_sqft"])]

    cleaned["postal1"] = cleaned["postal1"].astype(str).str.strip()
    cleaned = cleaned[cleaned["postal1"].notna() & (cleaned["postal1"] != "")]

    return cleaned.reset_index(drop=True)


def train_smoke_model(df: pd.DataFrame) -> tuple[Pipeline, dict, pd.DataFrame, dict]:
    feature_columns = [
        "sqft",
        "beds",
        "baths",
        "property_age",
        "sale_year",
        "sale_month",
        "postal1",
    ]
    target_column = "log_price_per_sqft"

    X = df[feature_columns]
    y = df[target_column]

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.2,
        random_state=RANDOM_STATE,
    )

    numeric_features = ["sqft", "beds", "baths", "property_age", "sale_year", "sale_month"]
    categorical_features = ["postal1"]

    preprocessor = ColumnTransformer(
        transformers=[
            ("num", StandardScaler(), numeric_features),
            (
                "cat",
                OneHotEncoder(handle_unknown="ignore", sparse_output=False),
                categorical_features,
            ),
        ]
    )

    model = Pipeline(
        steps=[
            ("preprocessor", preprocessor),
            ("regressor", Ridge(alpha=1.0, random_state=RANDOM_STATE)),
        ]
    )
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    metrics = {
        "train_r2": float(r2_score(y_train, model.predict(X_train))),
        "test_r2": float(r2_score(y_test, y_pred)),
        "test_mae_log_price_per_sqft": float(mean_absolute_error(y_test, y_pred)),
        "test_rmse_log_price_per_sqft": float(np.sqrt(mean_squared_error(y_test, y_pred))),
        "test_mae_pct_price_per_sqft": float(
            np.mean(np.abs(np.exp(y_pred) - np.exp(y_test)) / np.exp(y_test)) * 100
        ),
    }

    feature_names = model.named_steps["preprocessor"].get_feature_names_out()
    coefficients = model.named_steps["regressor"].coef_
    intercept = float(model.named_steps["regressor"].intercept_)
    coefficient_map = {
        str(name): float(value) for name, value in zip(feature_names, coefficients)
    }
    coef_df = pd.DataFrame(
        {"feature": feature_names, "coefficient": coefficients}
    ).sort_values("coefficient", key=np.abs, ascending=False)

    diagnostics = {
        "input_file": str(INPUT_CSV),
        "filter_window": {"start": FILTER_START, "end": FILTER_END},
        "target": target_column,
        "features": feature_columns,
        "train_rows": int(len(X_train)),
        "test_rows": int(len(X_test)),
        "training_rows": int(len(df)),
        "metrics": metrics,
        "intercept": intercept,
        "top_coefficients": coef_df.head(15).to_dict(orient="records"),
    }

    registry_artifact = build_model_registry_artifact(
        diagnostics=diagnostics,
        feature_names=list(feature_names),
        coefficient_map=coefficient_map,
        intercept=intercept,
    )
    return model, diagnostics, df, registry_artifact


def build_model_registry_artifact(
    diagnostics: dict,
    feature_names: list[str],
    coefficient_map: dict[str, float],
    intercept: float,
) -> dict:
    metrics = diagnostics["metrics"]
    return {
        "model_id": MODEL_ID,
        "model_version": MODEL_VERSION,
        "market": MARKET,
        "model_type": MODEL_TYPE,
        "target": TARGET,
        "training_window": {
            "start_date": FILTER_START,
            "end_date": FILTER_END,
        },
        "training_rows": diagnostics["training_rows"],
        "train_rows": diagnostics["train_rows"],
        "test_rows": diagnostics["test_rows"],
        "train_r2": metrics["train_r2"],
        "test_r2": metrics["test_r2"],
        "test_mae_log_price_per_sqft": metrics["test_mae_log_price_per_sqft"],
        "test_rmse_log_price_per_sqft": metrics["test_rmse_log_price_per_sqft"],
        "test_mae_pct_price_per_sqft": metrics["test_mae_pct_price_per_sqft"],
        "status": "diagnostic_only",
        "approved_for_recommendations": False,
        "intercept": intercept,
        "feature_names": feature_names,
        "input_features": diagnostics["features"],
        "coefficients": coefficient_map,
        "preprocessing": {
            "numeric_features_standardized": [
                "sqft",
                "beds",
                "baths",
                "property_age",
                "sale_year",
                "sale_month",
            ],
            "categorical_features_one_hot_encoded": ["postal1"],
        },
        "source_dataset_path": str(INPUT_CSV),
        "modeling_dataset_path": str(MODELING_DATASET),
        "created_at": datetime.now().date().isoformat(),
        "notes": (
            "Smoke-test model only. Not approved for seller-facing ROI recommendations. "
            "Numeric features were standardized before Ridge fitting; apply the same "
            "preprocessing before scoring with these coefficients."
        ),
    }


def save_model_registry_artifact(artifact: dict) -> Path:
    MODEL_REGISTRY_DIR.mkdir(parents=True, exist_ok=True)
    with MODEL_ARTIFACT.open("w", encoding="utf-8") as handle:
        json.dump(artifact, handle, indent=2)
    return MODEL_ARTIFACT


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    raw = load_raw_data()
    cleaned = apply_cleaning_filters(raw)

    print("=== Greenville Smoke Regression ===")
    print(f"Input: {INPUT_CSV}")
    print(f"Raw rows: {len(raw):,}")
    print(f"Clean rows after filtering: {len(cleaned):,}")
    print(f"Sale-date window: {FILTER_START} to {FILTER_END}")
    print(f"sale_date populated in raw file: {raw['sale_date'].notna().sum():,}/{len(raw):,}")

    if len(cleaned) < 100:
        raise RuntimeError(
            f"Only {len(cleaned)} clean rows found; expected several hundred for smoke test."
        )

    cleaned.to_csv(MODELING_DATASET, index=False)
    print(f"Saved modeling dataset: {MODELING_DATASET}")

    _, diagnostics, _, registry_artifact = train_smoke_model(cleaned)

    print()
    print("Model diagnostics:")
    print(f"  Train rows: {diagnostics['train_rows']:,}")
    print(f"  Test rows: {diagnostics['test_rows']:,}")
    print(f"  Train R²: {diagnostics['metrics']['train_r2']:.4f}")
    print(f"  Test R²: {diagnostics['metrics']['test_r2']:.4f}")
    print(f"  Test MAE (log ppsf): {diagnostics['metrics']['test_mae_log_price_per_sqft']:.4f}")
    print(f"  Test RMSE (log ppsf): {diagnostics['metrics']['test_rmse_log_price_per_sqft']:.4f}")
    print(
        "  Test MAE (% price_per_sqft): "
        f"{diagnostics['metrics']['test_mae_pct_price_per_sqft']:.2f}%"
    )
    print(f"  Intercept: {diagnostics['intercept']:.4f}")
    print()
    print("Top coefficients:")
    for row in diagnostics["top_coefficients"][:10]:
        print(f"  {row['feature']}: {row['coefficient']:.4f}")

    with DIAGNOSTICS_JSON.open("w", encoding="utf-8") as handle:
        json.dump(diagnostics, handle, indent=2)
    print()
    print(f"Saved diagnostics: {DIAGNOSTICS_JSON}")

    artifact_path = save_model_registry_artifact(registry_artifact)
    print(f"Saved model registry artifact: {artifact_path}")
    print(f"  status: {registry_artifact['status']}")
    print(f"  approved_for_recommendations: {registry_artifact['approved_for_recommendations']}")


if __name__ == "__main__":
    main()
