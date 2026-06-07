"""Product-level feedback insights from guest product trials."""

from __future__ import annotations

import pandas as pd

from config import OUTPUT_TABLES, PROCESSED_DIR


def _product_recommendation(row: pd.Series) -> str:
    if row["price_value_complaint_rate"] >= 0.35:
        return "Test bundled offers or size-value messaging for this item."
    if row["sweetness_complaint_rate"] >= 0.30:
        return "Rebalance sweetness profile and clarify customization options on menu."
    if row["avg_product_rating"] < 3.0:
        return "Audit recipe execution and retrain baristas on preparation standards."
    if row["avg_repeat_purchase_intent"] < 2.5:
        return "Pair with sampling or loyalty bonus to drive repeat trial among target guests."
    if row["seasonal_flag"] == 1 and row["trial_rate"] < 0.05:
        return "Improve seasonal product positioning and in-store sampling."
    return "Maintain quality and promote to high-intent guest segments."


def build_product_insights(
    product_feedback: pd.DataFrame,
    surveys: pd.DataFrame,
) -> pd.DataFrame:
    """Aggregate product feedback metrics and recommendations."""
    total_surveys = len(surveys)

    grouped = (
        product_feedback.groupby(["product_name", "product_category", "seasonal_flag"])
        .agg(
            feedback_count=("feedback_id", "count"),
            awareness_rate=("seasonal_drink_awareness", "mean"),
            avg_product_rating=("product_rating", "mean"),
            avg_repeat_purchase_intent=("repeat_purchase_intent", "mean"),
            price_value_complaint_rate=(
                "price_value_feedback",
                lambda s: (s == "too_expensive").mean(),
            ),
            sweetness_complaint_rate=(
                "sweetness_feedback",
                lambda s: (s == "too_sweet").mean(),
            ),
        )
        .reset_index()
    )
    grouped["trial_rate"] = grouped["feedback_count"] / total_surveys
    grouped.loc[grouped["seasonal_flag"] == 0, "awareness_rate"] = grouped.loc[
        grouped["seasonal_flag"] == 0, "trial_rate"
    ]

    segment_counts = (
        product_feedback.groupby(["product_name", "guest_segment"])
        .size()
        .reset_index(name="segment_count")
    )
    top_segments = (
        segment_counts.sort_values(["product_name", "segment_count"], ascending=[True, False])
        .drop_duplicates("product_name")
        .rename(columns={"guest_segment": "top_guest_segment"})
    )
    insights = grouped.merge(top_segments[["product_name", "top_guest_segment"]], on="product_name")
    insights["recommendation"] = insights.apply(_product_recommendation, axis=1)

    cols = [
        "product_name",
        "product_category",
        "seasonal_flag",
        "awareness_rate",
        "trial_rate",
        "avg_product_rating",
        "avg_repeat_purchase_intent",
        "price_value_complaint_rate",
        "sweetness_complaint_rate",
        "top_guest_segment",
        "recommendation",
    ]
    return insights[cols].sort_values("trial_rate", ascending=False).round(4).reset_index(drop=True)


def main() -> None:
    OUTPUT_TABLES.mkdir(parents=True, exist_ok=True)
    product_feedback = pd.read_parquet(PROCESSED_DIR / "product_feedback_clean.parquet")
    surveys = pd.read_parquet(PROCESSED_DIR / "guest_surveys_clean.parquet")
    insights = build_product_insights(product_feedback, surveys)
    insights.to_csv(OUTPUT_TABLES / "product_insights.csv", index=False)
    print(f"Product insights complete: {len(insights)} products profiled")


if __name__ == "__main__":
    main()
