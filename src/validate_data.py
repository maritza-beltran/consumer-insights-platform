"""Validate synthetic datasets, flag suspicious records, and export clean data."""

from __future__ import annotations

import json
from datetime import datetime

import pandas as pd

from config import (
    CHANNELS,
    DATA_SOURCE,
    EXPECTED_ROW_COUNTS,
    EXPERIENCE_COLS,
    N_STORES,
    N_SURVEYS,
    OUTPUT_TABLES,
    PROCESSED_DIR,
    RAW_DIR,
    REGIONS,
    SEGMENTS,
    SENTIMENTS,
    STORE_TYPES,
    STUDY_END,
    STUDY_START,
)

RATING_COLS = ["csat", "revisit_intent", *EXPERIENCE_COLS]

REQUIRED_FIELDS = {
    "stores": [
        "store_id", "store_name", "market", "region", "store_type",
        "avg_daily_transactions", "avg_ticket", "data_source",
    ],
    "guest_surveys": [
        "survey_id", "guest_id", "store_id", "survey_date", "guest_segment",
        "visit_channel", "nps", "csat", "revisit_intent", "data_source",
    ],
    "guest_comments": [
        "comment_id", "survey_id", "guest_id", "store_id", "comment_date",
        "comment_text", "sentiment_label", "data_source",
    ],
    "product_feedback": [
        "feedback_id", "survey_id", "guest_id", "store_id", "feedback_date",
        "product_name", "data_source",
    ],
    "loyalty_behavior": ["guest_id", "data_source"],
}


def load_raw_datasets() -> dict[str, pd.DataFrame]:
    """Load all five raw CSV datasets from data/raw/."""
    files = {
        "stores": "stores.csv",
        "guest_surveys": "guest_surveys.csv",
        "guest_comments": "guest_comments.csv",
        "product_feedback": "product_feedback.csv",
        "loyalty_behavior": "loyalty_behavior.csv",
    }
    return {name: pd.read_csv(RAW_DIR / fname) for name, fname in files.items()}


def _add_check(
    rows: list[dict],
    check_name: str,
    records_checked: int,
    issue_count: int,
    notes: str,
    *,
    warn_only: bool = False,
) -> None:
    """Append one row to the validation summary."""
    if issue_count == 0:
        status = "pass"
    elif warn_only:
        status = "warn"
    else:
        status = "fail"
    rows.append(
        {
            "check_name": check_name,
            "status": status,
            "records_checked": records_checked,
            "issue_count": issue_count,
            "notes": notes,
        }
    )


def _parse_dates(series: pd.Series) -> pd.Series:
    return pd.to_datetime(series, errors="coerce")


def _flag_straight_lining(surveys: pd.DataFrame) -> pd.DataFrame:
    """Flag surveys where all eight experience ratings are identical."""
    rating_matrix = surveys[EXPERIENCE_COLS]
    same_value = rating_matrix.nunique(axis=1) == 1
    flagged = surveys.loc[same_value, ["survey_id", "guest_id"]].copy()
    flagged["flag_reason"] = "straight_lining"
    return flagged


def _flag_inconsistent_responses(surveys: pd.DataFrame) -> pd.DataFrame:
    """Flag promoter NPS paired with very low CSAT and revisit intent."""
    mask = (surveys["nps"] >= 9) & (surveys["csat"] <= 2) & (surveys["revisit_intent"] <= 2)
    flagged = surveys.loc[mask, ["survey_id", "guest_id", "nps", "csat", "revisit_intent"]].copy()
    flagged["flag_reason"] = "inconsistent_promoter_scores"
    return flagged


def _flag_orphan_comments(comments: pd.DataFrame, surveys: pd.DataFrame) -> pd.DataFrame:
    """Flag comments whose survey_id does not exist in guest_surveys."""
    orphans = comments[~comments["survey_id"].isin(surveys["survey_id"])].copy()
    orphans["flag_reason"] = "missing_survey_linkage"
    return orphans


def build_enriched_surveys(
    stores: pd.DataFrame,
    surveys: pd.DataFrame,
    comments: pd.DataFrame,
    loyalty: pd.DataFrame,
) -> pd.DataFrame:
    """Join store, loyalty, and comment context onto survey records."""
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


def run_validation(
    stores: pd.DataFrame,
    surveys: pd.DataFrame,
    comments: pd.DataFrame,
    product_feedback: pd.DataFrame,
    loyalty: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    """
    Run all validation checks and return summary, flagged records, and report.

    Suspicious records are flagged — never deleted by default.
    """
    summary_rows: list[dict] = []
    flagged_frames: list[pd.DataFrame] = []

    # --- Uniqueness checks ---
    dup_store = int(stores["store_id"].duplicated().sum())
    _add_check(summary_rows, "unique_store_id", len(stores), dup_store, "Duplicate store_id values")

    dup_survey = int(surveys["survey_id"].duplicated().sum())
    _add_check(summary_rows, "unique_survey_id", len(surveys), dup_survey, "Duplicate survey_id values")

    dup_comment = int(comments["comment_id"].duplicated().sum())
    _add_check(summary_rows, "unique_comment_id", len(comments), dup_comment, "Duplicate comment_id values")

    dup_feedback = int(product_feedback["feedback_id"].duplicated().sum())
    _add_check(summary_rows, "unique_feedback_id", len(product_feedback), dup_feedback, "Duplicate feedback_id values")

    dup_loyalty = int(loyalty["guest_id"].duplicated().sum())
    _add_check(summary_rows, "unique_loyalty_guest_id", len(loyalty), dup_loyalty, "Duplicate guest_id in loyalty")

    # --- Referential integrity ---
    orphan_survey_stores = surveys[~surveys["store_id"].isin(stores["store_id"])]
    _add_check(
        summary_rows,
        "survey_store_exists",
        len(surveys),
        len(orphan_survey_stores),
        "Survey store_id must exist in stores",
    )

    orphan_comment_surveys = comments[~comments["survey_id"].isin(surveys["survey_id"])]
    _add_check(
        summary_rows,
        "comment_survey_exists",
        len(comments),
        len(orphan_comment_surveys),
        "Comment survey_id must exist in guest_surveys",
    )
    if len(orphan_comment_surveys):
        flagged_frames.append(_flag_orphan_comments(comments, surveys))

    orphan_product = product_feedback[~product_feedback["survey_id"].isin(surveys["survey_id"])]
    _add_check(
        summary_rows,
        "product_feedback_survey_exists",
        len(product_feedback),
        len(orphan_product),
        "Product feedback survey_id must exist in guest_surveys",
    )

    orphan_loyalty = surveys[~surveys["guest_id"].isin(loyalty["guest_id"])]
    _add_check(
        summary_rows,
        "loyalty_guest_exists",
        len(surveys),
        len(orphan_loyalty),
        "Every survey guest_id must exist in loyalty_behavior",
    )

    # --- Score range checks ---
    nps_oob = int((~surveys["nps"].between(0, 10)).sum())
    _add_check(summary_rows, "nps_range_0_10", len(surveys), nps_oob, "NPS must be between 0 and 10")

    rating_oob = 0
    for col in RATING_COLS:
        rating_oob += int((~surveys[col].between(1, 5)).sum())
    _add_check(
        summary_rows,
        "ratings_range_1_5",
        len(surveys) * len(RATING_COLS),
        rating_oob,
        "CSAT, revisit_intent, and experience ratings must be 1–5",
    )

    # --- Categorical validity ---
    invalid_segments = surveys[~surveys["guest_segment"].isin(SEGMENTS)]
    _add_check(
        summary_rows,
        "valid_guest_segment",
        len(surveys),
        len(invalid_segments),
        f"Allowed: {SEGMENTS}",
    )

    invalid_channels = surveys[~surveys["visit_channel"].isin(CHANNELS)]
    _add_check(
        summary_rows,
        "valid_visit_channel",
        len(surveys),
        len(invalid_channels),
        f"Allowed: {CHANNELS}",
    )

    invalid_regions = stores[~stores["region"].isin(REGIONS)]
    _add_check(summary_rows, "valid_region", len(stores), len(invalid_regions), f"Allowed: {REGIONS}")

    invalid_store_types = stores[~stores["store_type"].isin(STORE_TYPES)]
    _add_check(
        summary_rows,
        "valid_store_type",
        len(stores),
        len(invalid_store_types),
        f"Allowed: {STORE_TYPES}",
    )

    invalid_sentiment = comments[~comments["sentiment_label"].isin(SENTIMENTS)]
    _add_check(
        summary_rows,
        "valid_sentiment_label",
        len(comments),
        len(invalid_sentiment),
        f"Allowed: {SENTIMENTS}",
    )

    # --- Date range checks ---
    survey_dates = _parse_dates(surveys["survey_date"])
    survey_date_oob = int(
        ((survey_dates < STUDY_START) | (survey_dates > STUDY_END) | survey_dates.isna()).sum()
    )
    _add_check(
        summary_rows,
        "survey_date_in_study_period",
        len(surveys),
        survey_date_oob,
        f"Study period: {STUDY_START} to {STUDY_END}",
    )

    comment_dates = _parse_dates(comments["comment_date"])
    comment_date_oob = int(
        ((comment_dates < STUDY_START) | (comment_dates > STUDY_END) | comment_dates.isna()).sum()
    )
    _add_check(
        summary_rows,
        "comment_date_in_study_period",
        len(comments),
        comment_date_oob,
        f"Study period: {STUDY_START} to {STUDY_END}",
    )

    # --- Required fields populated ---
    required_issues = 0
    for dataset_name, df in [
        ("stores", stores),
        ("guest_surveys", surveys),
        ("guest_comments", comments),
        ("product_feedback", product_feedback),
        ("loyalty_behavior", loyalty),
    ]:
        cols = REQUIRED_FIELDS[dataset_name]
        nulls = int(df[cols].isnull().sum().sum())
        empty_text = 0
        for col in cols:
            if df[col].dtype == object:
                empty_text += int(df[col].astype(str).str.strip().eq("").sum())
        count = nulls + empty_text
        required_issues += count
        _add_check(
            summary_rows,
            f"required_fields_{dataset_name}",
            len(df) * len(cols),
            count,
            f"Required columns populated for {dataset_name}",
        )

    # --- Expected row counts ---
    datasets = {
        "stores": stores,
        "guest_surveys": surveys,
        "guest_comments": comments,
        "product_feedback": product_feedback,
        "loyalty_behavior": loyalty,
    }
    for name, (lo, hi) in EXPECTED_ROW_COUNTS.items():
        n = len(datasets[name])
        in_range = lo <= n <= hi
        _add_check(
            summary_rows,
            f"expected_row_count_{name}",
            n,
            0 if in_range else 1,
            f"Expected {lo:,}–{hi:,}; found {n:,}",
            warn_only=True,
        )

    # --- Data source label ---
    non_synthetic = int(surveys["data_source"].ne(DATA_SOURCE).sum())
    _add_check(
        summary_rows,
        "synthetic_data_label",
        len(surveys),
        non_synthetic,
        f"All records must be labeled data_source={DATA_SOURCE}",
    )

    # --- Quality flags (warn only — records retained) ---
    straight_line = _flag_straight_lining(surveys)
    _add_check(
        summary_rows,
        "flag_straight_lining",
        len(surveys),
        len(straight_line),
        "All experience ratings identical on one survey",
        warn_only=True,
    )
    if len(straight_line):
        flagged_frames.append(straight_line)

    inconsistent = _flag_inconsistent_responses(surveys)
    _add_check(
        summary_rows,
        "flag_inconsistent_promoter_scores",
        len(surveys),
        len(inconsistent),
        "NPS>=9 but CSAT<=2 and revisit_intent<=2",
        warn_only=True,
    )
    if len(inconsistent):
        flagged_frames.append(inconsistent)

    surveys_without_comments = surveys[~surveys["survey_id"].isin(comments["survey_id"])]
    _add_check(
        summary_rows,
        "flag_surveys_without_comments",
        len(surveys),
        len(surveys_without_comments),
        "Surveys missing linked guest comment",
        warn_only=True,
    )

    # --- Assemble outputs ---
    summary = pd.DataFrame(summary_rows)
    flagged = pd.concat(flagged_frames, ignore_index=True) if flagged_frames else pd.DataFrame()

    fail_count = int((summary["status"] == "fail").sum())
    warn_count = int((summary["status"] == "warn").sum())
    promoters = (surveys["nps"] >= 9).mean()
    detractors = (surveys["nps"] <= 6).mean()

    report = {
        "validated_at": datetime.utcnow().isoformat() + "Z",
        "status": "pass" if fail_count == 0 else "fail",
        "fail_checks": fail_count,
        "warn_checks": warn_count,
        "flagged_record_count": len(flagged),
        "record_counts": {name: len(df) for name, df in datasets.items()},
        "quality_metrics": {
            "brand_nps": round((promoters - detractors) * 100, 1),
            "avg_csat": round(float(surveys["csat"].mean()), 2),
            "avg_revisit_intent": round(float(surveys["revisit_intent"].mean()), 2),
            "comment_linkage_rate": round(len(comments) / len(surveys), 4),
        },
    }
    return summary, flagged, report


def save_processed_datasets(
    stores: pd.DataFrame,
    surveys: pd.DataFrame,
    comments: pd.DataFrame,
    product_feedback: pd.DataFrame,
    loyalty: pd.DataFrame,
) -> pd.DataFrame:
    """Write clean parquet files and return enriched survey dataframe."""
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    stores.to_parquet(PROCESSED_DIR / "stores_clean.parquet", index=False)
    surveys.to_parquet(PROCESSED_DIR / "guest_surveys_clean.parquet", index=False)
    comments.to_parquet(PROCESSED_DIR / "guest_comments_clean.parquet", index=False)
    product_feedback.to_parquet(PROCESSED_DIR / "product_feedback_clean.parquet", index=False)
    loyalty.to_parquet(PROCESSED_DIR / "loyalty_behavior_clean.parquet", index=False)
    enriched = build_enriched_surveys(stores, surveys, comments, loyalty)
    enriched.to_parquet(PROCESSED_DIR / "guest_surveys_enriched.parquet", index=False)
    return enriched


def validate_and_export(
    datasets: dict[str, pd.DataFrame] | None = None,
    *,
    raise_on_fail: bool = True,
) -> tuple[pd.DataFrame, dict]:
    """
    Full validation workflow: check, flag, save summary and processed data.

    Returns validation summary DataFrame and JSON-serializable report dict.
    """
    OUTPUT_TABLES.mkdir(parents=True, exist_ok=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    if datasets is None:
        datasets = load_raw_datasets()

    summary, flagged, report = run_validation(
        datasets["stores"],
        datasets["guest_surveys"],
        datasets["guest_comments"],
        datasets["product_feedback"],
        datasets["loyalty_behavior"],
    )

    summary.to_csv(OUTPUT_TABLES / "validation_summary.csv", index=False)
    (PROCESSED_DIR / "validation_report.json").write_text(json.dumps(report, indent=2))
    if len(flagged):
        flagged.to_csv(PROCESSED_DIR / "flagged_records.csv", index=False)

    save_processed_datasets(
        datasets["stores"],
        datasets["guest_surveys"],
        datasets["guest_comments"],
        datasets["product_feedback"],
        datasets["loyalty_behavior"],
    )

    if raise_on_fail and report["status"] == "fail":
        raise ValueError(f"Validation failed: {report['fail_checks']} failing checks")

    return summary, report


def validate_all(
    stores: pd.DataFrame,
    surveys: pd.DataFrame,
    comments: pd.DataFrame,
    product_feedback: pd.DataFrame,
    loyalty: pd.DataFrame,
) -> dict:
    """Backward-compatible wrapper used by tests."""
    summary, report = validate_and_export(
        {
            "stores": stores,
            "guest_surveys": surveys,
            "guest_comments": comments,
            "product_feedback": product_feedback,
            "loyalty_behavior": loyalty,
        },
        raise_on_fail=False,
    )
    report["issues"] = summary.loc[summary["status"] == "fail", "notes"].tolist()
    report["warnings"] = summary.loc[summary["status"] == "warn", "notes"].tolist()
    return report


def main() -> None:
    summary, report = validate_and_export()
    print(f"Validation status: {report['status'].upper()}")
    print(f"Fail checks: {report['fail_checks']} | Warn checks: {report['warn_checks']}")
    print(f"Flagged records: {report['flagged_record_count']}")
    print(f"Summary -> {OUTPUT_TABLES / 'validation_summary.csv'}")
    if report["status"] == "fail":
        print(summary.loc[summary["status"] == "fail", ["check_name", "issue_count", "notes"]])
        raise SystemExit(1)


if __name__ == "__main__":
    main()
