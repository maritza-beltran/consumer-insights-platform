"""Validate synthetic survey data quality and export a validation report."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = ROOT / "data" / "raw"
PROCESSED_DIR = ROOT / "data" / "processed"

REQUIRED_SURVEY_COLS = [
    "survey_id",
    "guest_id",
    "survey_date",
    "store_id",
    "region",
    "store_type",
    "channel",
    "segment",
    "nps_score",
    "csat_score",
    "revisit_intent",
    "comment_text",
    "data_source",
]

VALID_SEGMENTS = {"loyalist", "occasional", "new_guest", "at_risk"}
VALID_CHANNELS = {"in-store", "drive-thru", "mobile order"}


def _check_required_columns(df: pd.DataFrame, required: list[str]) -> list[str]:
    return [col for col in required if col not in df.columns]


def _check_numeric_ranges(df: pd.DataFrame) -> list[str]:
    issues = []
    if not df["nps_score"].between(0, 10).all():
        issues.append("nps_score outside 0-10 range")
    if not df["csat_score"].between(1, 5).all():
        issues.append("csat_score outside 1-5 range")
    if not df["revisit_intent"].between(1, 5).all():
        issues.append("revisit_intent outside 1-5 range")
    return issues


def validate_surveys(surveys: pd.DataFrame, stores: pd.DataFrame) -> dict:
    issues: list[str] = []
    warnings: list[str] = []

    missing_cols = _check_required_columns(surveys, REQUIRED_SURVEY_COLS)
    if missing_cols:
        issues.append(f"Missing columns: {missing_cols}")

    if surveys["survey_id"].duplicated().any():
        issues.append("Duplicate survey_id values detected")

    if surveys["data_source"].ne("synthetic").any():
        issues.append("Non-synthetic records found in guest_surveys")

    range_issues = _check_numeric_ranges(surveys)
    issues.extend(range_issues)

    null_counts = surveys[REQUIRED_SURVEY_COLS].isnull().sum()
    for col, count in null_counts.items():
        if count > 0:
            issues.append(f"Null values in {col}: {count}")

    invalid_segments = set(surveys["segment"].unique()) - VALID_SEGMENTS
    if invalid_segments:
        issues.append(f"Invalid segment values: {sorted(invalid_segments)}")

    invalid_channels = set(surveys["channel"].unique()) - VALID_CHANNELS
    if invalid_channels:
        issues.append(f"Invalid channel values: {sorted(invalid_channels)}")

    orphan_stores = set(surveys["store_id"]) - set(stores["store_id"])
    if orphan_stores:
        issues.append(f"Survey store_ids not in stores master: {len(orphan_stores)}")

    comment_fill = surveys["comment_text"].astype(str).str.strip().ne("").mean()
    if comment_fill < 0.95:
        warnings.append(f"Comment fill rate below 95%: {comment_fill:.1%}")

    nps_promoters = (surveys["nps_score"] >= 9).mean()
    nps_detractors = (surveys["nps_score"] <= 6).mean()
    nps_score = round((nps_promoters - nps_detractors) * 100, 1)

    report = {
        "validated_at": datetime.utcnow().isoformat() + "Z",
        "status": "pass" if not issues else "fail",
        "record_counts": {
            "surveys": len(surveys),
            "stores": len(stores),
        },
        "quality_metrics": {
            "comment_fill_rate": round(float(comment_fill), 4),
            "brand_nps": nps_score,
            "avg_csat": round(float(surveys["csat_score"].mean()), 2),
            "avg_revisit_intent": round(float(surveys["revisit_intent"].mean()), 2),
        },
        "issues": issues,
        "warnings": warnings,
    }
    return report


def main() -> None:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    surveys = pd.read_csv(RAW_DIR / "guest_surveys.csv")
    stores = pd.read_csv(RAW_DIR / "stores.csv")

    report = validate_surveys(surveys, stores)
    report_path = PROCESSED_DIR / "validation_report.json"
    report_path.write_text(json.dumps(report, indent=2))

    clean_surveys = surveys.copy()
    clean_surveys["survey_date"] = pd.to_datetime(clean_surveys["survey_date"])
    clean_surveys.to_parquet(PROCESSED_DIR / "guest_surveys_clean.parquet", index=False)
    stores.to_parquet(PROCESSED_DIR / "stores_clean.parquet", index=False)

    print(f"Validation status: {report['status'].upper()}")
    print(f"Brand NPS: {report['quality_metrics']['brand_nps']}")
    print(f"Report saved -> {report_path}")

    if report["status"] == "fail":
        for issue in report["issues"]:
            print(f"  ISSUE: {issue}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
