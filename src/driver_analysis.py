"""Logistic regression model for high revisit intent drivers."""

from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, precision_score, recall_score, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from config import EXPERIENCE_COLS, OUTPUT_CHARTS, OUTPUT_TABLES, PROCESSED_DIR, RANDOM_SEED

DRIVER_LABELS = {
    "wait_time_rating": "wait time",
    "drink_quality_rating": "drink quality",
    "order_accuracy_rating": "order accuracy",
    "staff_friendliness_rating": "staff friendliness",
    "cleanliness_rating": "cleanliness",
    "mobile_app_experience_rating": "mobile app experience",
    "rewards_satisfaction": "rewards satisfaction",
    "price_value_perception": "price-value perception",
}


def _interpret(driver: str, coefficient: float, odds_ratio: float) -> str:
    label = DRIVER_LABELS.get(driver, driver.replace("_", " "))
    direction = "increases" if coefficient > 0 else "decreases"
    return (
        f"A one standard-deviation increase in {label} {direction} the odds of "
        f"high revisit intent (revisit_intent >= 4) by a factor of {odds_ratio:.2f}."
    )


def train_high_revisit_model(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Logistic regression predicting high_revisit_intent from experience ratings.

    high_revisit_intent = 1 if revisit_intent >= 4 else 0.
    """
    x = df[EXPERIENCE_COLS].astype(float)
    y = (df["revisit_intent"] >= 4).astype(int)

    model = Pipeline(
        steps=[
            ("scaler", StandardScaler()),
            ("clf", LogisticRegression(max_iter=1000, random_state=RANDOM_SEED, class_weight="balanced")),
        ]
    )
    x_train, x_test, y_train, y_test = train_test_split(
        x, y, test_size=0.25, random_state=RANDOM_SEED, stratify=y
    )
    model.fit(x_train, y_train)
    y_pred = model.predict(x_test)
    y_prob = model.predict_proba(x_test)[:, 1]

    coefs = model.named_steps["clf"].coef_[0]
    drivers = pd.DataFrame({"driver": EXPERIENCE_COLS, "model_coefficient": coefs})
    drivers["odds_ratio"] = np.exp(drivers["model_coefficient"])
    drivers["absolute_importance"] = drivers["model_coefficient"].abs()
    drivers = drivers.sort_values("absolute_importance", ascending=False).reset_index(drop=True)
    drivers["rank"] = range(1, len(drivers) + 1)
    drivers["plain_english_interpretation"] = drivers.apply(
        lambda row: _interpret(row["driver"], row["model_coefficient"], row["odds_ratio"]),
        axis=1,
    )

    metrics = pd.DataFrame(
        [
            {
                "accuracy": round(float(accuracy_score(y_test, y_pred)), 4),
                "precision": round(float(precision_score(y_test, y_pred, zero_division=0)), 4),
                "recall": round(float(recall_score(y_test, y_pred, zero_division=0)), 4),
                "roc_auc": round(float(roc_auc_score(y_test, y_prob)), 4),
            }
        ]
    )
    return drivers.round(4), metrics


def save_charts(drivers: pd.DataFrame) -> None:
    OUTPUT_CHARTS.mkdir(parents=True, exist_ok=True)
    top = drivers.sort_values("model_coefficient")
    fig, ax = plt.subplots(figsize=(10, 6))
    colors = ["#27AE60" if c > 0 else "#C0392B" for c in top["model_coefficient"]]
    labels = [DRIVER_LABELS.get(d, d) for d in top["driver"]]
    ax.barh(labels, top["model_coefficient"], color=colors)
    ax.axvline(0, color="black", linewidth=0.8)
    ax.set_title("High Revisit Intent Driver Model — Logistic Coefficients")
    fig.tight_layout()
    fig.savefig(OUTPUT_CHARTS / "revisit_intent_drivers.png", dpi=120)
    plt.close(fig)


def main() -> None:
    OUTPUT_TABLES.mkdir(parents=True, exist_ok=True)
    df = pd.read_parquet(PROCESSED_DIR / "guest_surveys_classified.parquet")

    drivers, metrics = train_high_revisit_model(df)
    drivers.to_csv(OUTPUT_TABLES / "driver_importance.csv", index=False)
    metrics.to_csv(OUTPUT_TABLES / "model_metrics.csv", index=False)
    save_charts(drivers)

    print(f"High revisit intent model ROC-AUC: {metrics.iloc[0]['roc_auc']}")
    print(f"Top driver: {drivers.iloc[0]['driver']} (rank {drivers.iloc[0]['rank']})")


if __name__ == "__main__":
    main()
