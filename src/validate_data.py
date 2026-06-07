"""Validate synthetic datasets and export clean parquet files."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import pandas as pd

from config import CHANNELS, PROCESSED_DIR, RAW_DIR, REGIONS, SEGMENTS, SENTIMENTS, STORE_TYPES

EXPERIENCE_COLS = [
    "wait_time_rating",
    "drink_quality_rating",
    "order_accuracy_rating",
    "staff_friendliness_rating",
    "cleanliness_rating",
    "mobile_app_experience_rating",
    "rewards_satisfaction",
    "price_value_perception",
]


def _missing_cols(df: pd.DataFrame, required: list[str]) -> list[str]:
    return [c for c in required if c not in df.columns]


def validate_all(
    stores: pd.DataFrame,
    surveys: pd.DataFrame,
    comments: pd.DataFrame,
    product_feedback: pd.DataFrame,
    loyalty: pd.DataFrame,
) -> dict:
    issues: list[str] = []
    warnings: list[str] = []

    if _missing_cols(stores, ["store_id", "region", "store_type", "avg_daily_transactions", "avg_ticket"]):
        issues.append("stores.csv missing required columns")

    if surveys["survey_id"].duplicated().any():
        issues.append("Duplicate survey_id in guest_surveys")
    if not surveys["nps"].between(0, 10).all():
        issues.append("nps outside 0-10 range")
    for col in ["csat", "revisit_intent", *EXPERIENCE_COLS]:
        if not surveys[col].between(1, 5).all():
            issues.append(f"{col} outside 1-5 range")

    invalid_segments = set(surveys["guest_segment"].unique()) - set(SEGMENTS)
    if invalid_segments:
        issues.append(f"Invalid guest_segment values: {sorted(invalid_segments)}")
    invalid_channels = set(surveys["visit_channel"].unique()) - set(CHANNELS)
    if invalid_channels:
        issues.append(f"Invalid visit_channel values: {sorted(invalid_channels)}")

    orphan_survey_stores = set(surveys["store_id"]) - set(stores["store_id"])
    if orphan_survey_stores:
        issues.append(f"Survey store_ids not in stores: {len(orphan_survey_stores)}")

    if comments["comment_id"].duplicated().any():
        issues.append("Duplicate comment_id in guest_comments")
    invalid_sentiment = set(comments["sentiment_label"].unique()) - set(SENTIMENTS)
    if invalid_sentiment:
        issues.append(f"Invalid sentiment_label values: {sorted(invalid_sentiment)}")

    orphan_comment_surveys = set(comments["survey_id"]) - set(surveys["survey_id"])
    if orphan_comment_surveys:
        issues.append(f"Comment survey_ids not in surveys: {len(orphan_comment_surveys)}")

    orphan_product_surveys = set(product_feedback["survey_id"]) - set(surveys["survey_id"])
    if orphan_product_surveys:
        issues.append(f"Product feedback survey_ids not in surveys: {len(orphan_product_surveys)}")

    orphan_loyalty = set(surveys["guest_id"]) - set(loyalty["guest_id"])
    if orphan_loyalty:
        issues.append(f"Survey guest_ids missing from loyalty_behavior: {len(orphan_loyalty)}")

    if surveys["data_source"].ne("synthetic").any():
        issues.append("Non-synthetic records found in guest_surveys")

    comment_rate = len(comments) / len(surveys)
    if comment_rate < 0.9:
        warnings.append(f"Comment linkage rate below 90%: {comment_rate:.1%}")

    promoters = (surveys["nps"] >= 9).mean()
    detractors = (surveys["nps"] <= 6).mean()
    brand_nps = round((promoters - detractors) * 100, 1)

    return {
        "validated_at": datetime.utcnow().isoformat() + "Z",
        "status": "pass" if not issues else "fail",
        "record_counts": {
            "stores": len(stores),
            "surveys": len(surveys),
            "comments": len(comments),
            "product_feedback": len(product_feedback),
            "loyalty_behavior": len(loyalty),
        },
        "quality_metrics": {
            "comment_linkage_rate": round(comment_rate, 4),
            "brand_nps": brand_nps,
            "avg_csat": round(float(surveys["csat"].mean()), 2),
            "avg_revisit_intent": round(float(surveys["revisit_intent"].mean()), 2),
        },
        "issues": issues,
        "warnings": warnings,
    }


def build_enriched_surveys(
    stores: pd.DataFrame,
    surveys: pd.DataFrame,
    comments: pd.DataFrame,
    loyalty: pd.DataFrame,
) -> pd.DataFrame:
    store_cols = ["store_id", "store_name", "market", "region", "store_type", "franchise_corporate_flag"]
    enriched = surveys.merge(stores[store_cols], on="store_id", how="left")
    enriched = enriched.merge(loyalty, on="guest_id", how="left", suffixes=("", "_loyalty"))

    comment_agg = (
        comments.groupby("survey_id")
        .agg(
            comment_count=("comment_id", "count"),
            comment_text=("comment_text", "first"),
            sentiment_label=("sentiment_label", "first"),
            star_rating=("star_rating", "mean"),
        )
        .reset_index()
    )
    enriched = enriched.merge(comment_agg, on="survey_id", how="left")
    enriched["comment_text"] = enriched["comment_text"].fillna("")
    enriched["sentiment_label"] = enriched["sentiment_label"].fillna("neutral")
    enriched["nps_category"] = pd.cut(
        enriched["nps"], bins=[-1, 6, 8, 10], labels=["detractor", "passive", "promoter"]
    )
    return enriched


def main() -> None:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    stores = pd.read_csv(RAW_DIR / "stores.csv")
    surveys = pd.read_csv(RAW_DIR / "guest_surveys.csv")
    comments = pd.read_csv(RAW_DIR / "guest_comments.csv")
    product_feedback = pd.read_csv(RAW_DIR / "product_feedback.csv")
    loyalty = pd.read_csv(RAW_DIR / "loyalty_behavior.csv")

    report = validate_all(stores, surveys, comments, product_feedback, loyalty)
    (PROCESSED_DIR / "validation_report.json").write_text(json.dumps(report, indent=2))

    stores.to_parquet(PROCESSED_DIR / "stores_clean.parquet", index=False)
    surveys.to_parquet(PROCESSED_DIR / "guest_surveys_clean.parquet", index=False)
    comments.to_parquet(PROCESSED_DIR / "guest_comments_clean.parquet", index=False)
    product_feedback.to_parquet(PROCESSED_DIR / "product_feedback_clean.parquet", index=False)
    loyalty.to_parquet(PROCESSED_DIR / "loyalty_behavior_clean.parquet", index=False)

    enriched = build_enriched_surveys(stores, surveys, comments, loyalty)
    enriched.to_parquet(PROCESSED_DIR / "guest_surveys_enriched.parquet", index=False)

    print(f"Validation status: {report['status'].upper()}")
    print(f"Brand NPS: {report['quality_metrics']['brand_nps']}")
    print(f"Report -> {PROCESSED_DIR / 'validation_report.json'}")

    if report["status"] == "fail":
        for issue in report["issues"]:
            print(f"  ISSUE: {issue}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
