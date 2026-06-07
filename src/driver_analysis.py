"""Model satisfaction drivers using logistic regression on promoter/detractor outcomes."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

ROOT = Path(__file__).resolve().parent.parent
PROCESSED_DIR = ROOT / "data" / "processed"
OUTPUT_TABLES = ROOT / "outputs" / "tables"
OUTPUT_CHARTS = ROOT / "outputs" / "charts"
RANDOM_SEED = 42

THEME_COLUMNS = [
    "speed_of_service",
    "product_quality",
    "cleanliness",
    "staff_friendliness",
    "value_for_money",
    "ambiance",
    "mobile_app",
    "loyalty_program",
    "menu_variety",
    "wait_time",
    "general_experience",
]


def _build_feature_matrix(df: pd.DataFrame) -> pd.DataFrame:
    exploded = df.explode("themes")[["survey_id", "themes"]].drop_duplicates()
    theme_dummies = (
        exploded.assign(present=1)
        .pivot_table(index="survey_id", columns="themes", values="present", fill_value=0, aggfunc="max")
        .reindex(columns=THEME_COLUMNS, fill_value=0)
    )
    theme_dummies = theme_dummies.clip(upper=1)

    features = df.set_index("survey_id")[
        ["channel", "segment", "store_type", "region"]
    ].join(theme_dummies)
    return features.reset_index()


def train_driver_model(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    features = _build_feature_matrix(df)
    target = (df.set_index("survey_id")["nps_score"] >= 9).astype(int)
    target = target.reindex(features["survey_id"]).reset_index(drop=True)

    x = features.drop(columns=["survey_id"])
    y = target

    categorical = ["channel", "segment", "store_type", "region"]
    numeric = [c for c in x.columns if c not in categorical]

    preprocessor = ColumnTransformer(
        transformers=[
            ("cat", OneHotEncoder(handle_unknown="ignore"), categorical),
            ("num", StandardScaler(), numeric),
        ]
    )

    model = Pipeline(
        steps=[
            ("prep", preprocessor),
            (
                "clf",
                LogisticRegression(max_iter=1000, random_state=RANDOM_SEED, class_weight="balanced"),
            ),
        ]
    )

    x_train, x_test, y_train, y_test = train_test_split(
        x, y, test_size=0.25, random_state=RANDOM_SEED, stratify=y
    )
    model.fit(x_train, y_train)
    accuracy = model.score(x_test, y_test)

    feature_names = model.named_steps["prep"].get_feature_names_out()
    coefficients = model.named_steps["clf"].coef_[0]
    driver_df = pd.DataFrame({"feature": feature_names, "coefficient": coefficients})
    driver_df["abs_coefficient"] = driver_df["coefficient"].abs()
    driver_df = driver_df.sort_values("abs_coefficient", ascending=False)

    theme_drivers = driver_df[driver_df["feature"].str.startswith("num__")].copy()
    theme_drivers["theme"] = theme_drivers["feature"].str.replace("num__", "", regex=False)

    metrics = {"test_accuracy": round(float(accuracy), 4), "n_train": len(x_train), "n_test": len(x_test)}
    return theme_drivers, metrics


def save_driver_chart(drivers: pd.DataFrame) -> None:
    OUTPUT_CHARTS.mkdir(parents=True, exist_ok=True)
    top = drivers.head(10).sort_values("coefficient")

    fig, ax = plt.subplots(figsize=(10, 6))
    colors = ["#27AE60" if c > 0 else "#C0392B" for c in top["coefficient"]]
    ax.barh(top["theme"], top["coefficient"], color=colors)
    ax.axvline(0, color="black", linewidth=0.8)
    ax.set_title("NPS Promoter Driver Model — Theme Coefficients")
    ax.set_xlabel("Logistic regression coefficient")
    fig.tight_layout()
    fig.savefig(OUTPUT_CHARTS / "satisfaction_drivers.png", dpi=120)
    plt.close(fig)


def main() -> None:
    OUTPUT_TABLES.mkdir(parents=True, exist_ok=True)
    df = pd.read_parquet(PROCESSED_DIR / "guest_surveys_classified.parquet")

    drivers, metrics = train_driver_model(df)
    drivers.to_csv(OUTPUT_TABLES / "satisfaction_drivers.csv", index=False)

    metrics_path = OUTPUT_TABLES / "driver_model_metrics.json"
    import json

    metrics_path.write_text(json.dumps(metrics, indent=2))
    save_driver_chart(drivers)

    print(f"Driver model accuracy: {metrics['test_accuracy']}")
    print(f"Top negative driver: {drivers.iloc[0]['theme']}")


if __name__ == "__main__":
    main()
