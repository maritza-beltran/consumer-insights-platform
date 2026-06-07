"""Model NPS promoters and revisit intent drivers."""

from __future__ import annotations

import json

import matplotlib.pyplot as plt
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from config import EXPERIENCE_COLS, OUTPUT_CHARTS, OUTPUT_TABLES, PROCESSED_DIR, RANDOM_SEED, THEME_KEYWORDS

THEME_COLUMNS = list(THEME_KEYWORDS.keys()) + ["general_experience"]


def _theme_matrix(df: pd.DataFrame) -> pd.DataFrame:
    exploded = df.explode("themes")[["survey_id", "themes"]].drop_duplicates()
    dummies = (
        exploded.assign(present=1)
        .pivot_table(index="survey_id", columns="themes", values="present", fill_value=0, aggfunc="max")
        .reindex(columns=THEME_COLUMNS, fill_value=0)
        .clip(upper=1)
    )
    context = df.set_index("survey_id")[["visit_channel", "guest_segment", "store_type", "region"]]
    return context.join(dummies).reset_index()


def train_nps_driver_model(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    features = _theme_matrix(df)
    target = (df.set_index("survey_id")["nps"] >= 9).astype(int).reindex(features["survey_id"]).reset_index(drop=True)
    x = features.drop(columns=["survey_id"])
    categorical = ["visit_channel", "guest_segment", "store_type", "region"]
    numeric = [c for c in x.columns if c not in categorical]

    model = Pipeline(
        steps=[
            ("prep", ColumnTransformer([
                ("cat", OneHotEncoder(handle_unknown="ignore"), categorical),
                ("num", StandardScaler(), numeric),
            ])),
            ("clf", LogisticRegression(max_iter=1000, random_state=RANDOM_SEED, class_weight="balanced")),
        ]
    )
    x_train, x_test, y_train, y_test = train_test_split(x, target, test_size=0.25, random_state=RANDOM_SEED, stratify=target)
    model.fit(x_train, y_train)
    names = model.named_steps["prep"].get_feature_names_out()
    coefs = model.named_steps["clf"].coef_[0]
    drivers = pd.DataFrame({"feature": names, "coefficient": coefs})
    drivers["abs_coefficient"] = drivers["coefficient"].abs()
    theme_drivers = drivers[drivers["feature"].str.startswith("num__")].copy()
    theme_drivers["theme"] = theme_drivers["feature"].str.replace("num__", "", regex=False)
    theme_drivers = theme_drivers.sort_values("abs_coefficient", ascending=False)
    metrics = {"model": "nps_promoter", "test_accuracy": round(float(model.score(x_test, y_test)), 4)}
    return theme_drivers, metrics


def train_revisit_driver_model(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    x = df[EXPERIENCE_COLS + ["visit_channel", "guest_segment"]].copy()
    y = df["revisit_intent"].astype(float)
    categorical = ["visit_channel", "guest_segment"]
    model = Pipeline(
        steps=[
            ("prep", ColumnTransformer([
                ("cat", OneHotEncoder(handle_unknown="ignore"), categorical),
                ("num", StandardScaler(), EXPERIENCE_COLS),
            ])),
            ("reg", LinearRegression()),
        ]
    )
    x_train, x_test, y_train, y_test = train_test_split(x, y, test_size=0.25, random_state=RANDOM_SEED)
    model.fit(x_train, y_train)
    names = model.named_steps["prep"].get_feature_names_out()
    coefs = model.named_steps["reg"].coef_
    drivers = pd.DataFrame({"feature": names, "coefficient": coefs})
    rating_drivers = drivers[drivers["feature"].str.startswith("num__")].copy()
    rating_drivers["rating"] = rating_drivers["feature"].str.replace("num__", "", regex=False)
    rating_drivers = rating_drivers.sort_values("coefficient", ascending=False)
    r2 = float(model.score(x_test, y_test))
    metrics = {"model": "revisit_intent", "test_r2": round(r2, 4)}
    return rating_drivers, metrics


def save_charts(theme_drivers: pd.DataFrame, revisit_drivers: pd.DataFrame) -> None:
    OUTPUT_CHARTS.mkdir(parents=True, exist_ok=True)
    top = theme_drivers.head(10).sort_values("coefficient")
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.barh(top["theme"], top["coefficient"], color=["#27AE60" if c > 0 else "#C0392B" for c in top["coefficient"]])
    ax.axvline(0, color="black", linewidth=0.8)
    ax.set_title("NPS Promoter Driver Model — Theme Coefficients")
    fig.tight_layout()
    fig.savefig(OUTPUT_CHARTS / "satisfaction_drivers.png", dpi=120)
    plt.close(fig)

    top_r = revisit_drivers.sort_values("coefficient")
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.barh(top_r["rating"], top_r["coefficient"], color="#6F4E37")
    ax.set_title("Revisit Intent Driver Model — Experience Rating Coefficients")
    fig.tight_layout()
    fig.savefig(OUTPUT_CHARTS / "revisit_intent_drivers.png", dpi=120)
    plt.close(fig)


def main() -> None:
    OUTPUT_TABLES.mkdir(parents=True, exist_ok=True)
    df = pd.read_parquet(PROCESSED_DIR / "guest_surveys_classified.parquet")

    theme_drivers, nps_metrics = train_nps_driver_model(df)
    revisit_drivers, revisit_metrics = train_revisit_driver_model(df)

    theme_drivers.to_csv(OUTPUT_TABLES / "satisfaction_drivers.csv", index=False)
    revisit_drivers.to_csv(OUTPUT_TABLES / "revisit_intent_drivers.csv", index=False)
    (OUTPUT_TABLES / "driver_model_metrics.json").write_text(json.dumps([nps_metrics, revisit_metrics], indent=2))
    save_charts(theme_drivers, revisit_drivers)

    print(f"NPS promoter model accuracy: {nps_metrics['test_accuracy']}")
    print(f"Revisit intent model R²: {revisit_metrics['test_r2']}")
    print(f"Top revisit driver: {revisit_drivers.iloc[0]['rating']}")


if __name__ == "__main__":
    main()
