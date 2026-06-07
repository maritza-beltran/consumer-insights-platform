"""Segment- and dimension-level VoC performance analysis."""

from __future__ import annotations

import matplotlib.pyplot as plt
import pandas as pd

from config import EXPERIENCE_COLS, OUTPUT_CHARTS, OUTPUT_TABLES, PROCESSED_DIR, THEME_RECOMMENDED_ACTIONS
from metrics import standard_nps

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


def _top_theme_by_sentiment(segment_df: pd.DataFrame, negative: bool) -> str:
    subset = segment_df[segment_df["is_negative_experience"] == negative]
    if subset.empty:
        return ""
    counts = subset.groupby("primary_theme").size()
    return counts.idxmax()


def _segment_primary_driver(segment_df: pd.DataFrame) -> str:
    """Lowest average experience rating in the segment (biggest improvement lever)."""
    means = segment_df[EXPERIENCE_COLS].mean()
    weakest = means.idxmin()
    return DRIVER_LABELS.get(weakest, weakest)


def _recommended_action(segment: str, top_negative: str, primary_driver: str) -> str:
    theme_action = THEME_RECOMMENDED_ACTIONS.get(top_negative, THEME_RECOMMENDED_ACTIONS["general_experience"])
    return f"For {segment.replace('_', ' ')}: address {top_negative.replace('_', ' ')} and improve {primary_driver}. {theme_action}"


def segment_summary(df: pd.DataFrame, global_top_driver: str = "") -> pd.DataFrame:
    rows: list[dict] = []
    for segment, segment_df in df.groupby("guest_segment"):
        top_negative = _top_theme_by_sentiment(segment_df, negative=True)
        top_positive = _top_theme_by_sentiment(segment_df, negative=False)
        primary_driver = global_top_driver or _segment_primary_driver(segment_df)
        rows.append(
            {
                "guest_segment": segment,
                "survey_count": len(segment_df),
                "avg_nps": standard_nps(segment_df["nps"]),
                "avg_csat": round(segment_df["csat"].mean(), 4),
                "avg_revisit_intent": round(segment_df["revisit_intent"].mean(), 4),
                "top_negative_theme": top_negative,
                "top_positive_theme": top_positive,
                "primary_driver": primary_driver,
                "recommended_action": _recommended_action(segment, top_negative, primary_driver),
            }
        )
    return pd.DataFrame(rows).sort_values("survey_count", ascending=False).reset_index(drop=True)


def segment_theme_matrix(df: pd.DataFrame) -> pd.DataFrame:
    commented = df[df["comment_text"].astype(str).str.strip() != ""]
    matrix = (
        commented.groupby(["guest_segment", "primary_theme"])
        .agg(
            comment_count=("survey_id", "count"),
            negative_share=("is_negative_experience", "mean"),
            avg_nps=("nps", "mean"),
            avg_csat=("csat", "mean"),
            avg_revisit_intent=("revisit_intent", "mean"),
        )
        .reset_index()
    )
    return matrix.round(4).sort_values(["guest_segment", "comment_count"], ascending=[True, False])


def dimension_summary(df: pd.DataFrame, dimension: str) -> pd.DataFrame:
    return (
        df.groupby(dimension)
        .agg(
            survey_count=("survey_id", "count"),
            avg_nps=("nps", "mean"),
            avg_csat=("csat", "mean"),
            avg_revisit=("revisit_intent", "mean"),
            detractor_rate=("nps", lambda s: (s <= 6).mean()),
        )
        .reset_index()
        .round(4)
    )


def save_segment_charts(summary: pd.DataFrame, theme_matrix: pd.DataFrame) -> None:
    OUTPUT_CHARTS.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.bar(summary["guest_segment"], summary["avg_nps"], color="#6F4E37")
    ax.set_title("Average NPS by Guest Segment")
    ax.tick_params(axis="x", rotation=20)
    fig.tight_layout()
    fig.savefig(OUTPUT_CHARTS / "segment_nps.png", dpi=120)
    plt.close(fig)

    pivot = theme_matrix.pivot(index="primary_theme", columns="guest_segment", values="comment_count").fillna(0)
    top_themes = pivot.sum(axis=1).sort_values(ascending=False).head(8).index
    pivot = pivot.loc[top_themes]
    fig, ax = plt.subplots(figsize=(11, 6))
    im = ax.imshow(pivot.values, aspect="auto", cmap="YlOrBr")
    ax.set_xticks(range(len(pivot.columns)))
    ax.set_xticklabels(pivot.columns, rotation=20)
    ax.set_yticks(range(len(pivot.index)))
    ax.set_yticklabels(pivot.index)
    ax.set_title("Comment Count by Segment and Theme")
    fig.colorbar(im, ax=ax, label="Comments")
    fig.tight_layout()
    fig.savefig(OUTPUT_CHARTS / "segment_theme_heatmap.png", dpi=120)
    plt.close(fig)


def main() -> None:
    OUTPUT_TABLES.mkdir(parents=True, exist_ok=True)
    df = pd.read_parquet(PROCESSED_DIR / "guest_surveys_classified.parquet")

    global_top_driver = ""
    driver_path = OUTPUT_TABLES / "driver_importance.csv"
    if driver_path.exists():
        drivers = pd.read_csv(driver_path)
        top = drivers.sort_values("rank").iloc[0]["driver"]
        global_top_driver = DRIVER_LABELS.get(top, top)

    segments = segment_summary(df, global_top_driver=global_top_driver)
    theme_matrix = segment_theme_matrix(df)
    channel_summary = dimension_summary(df, "visit_channel")
    region_summary = dimension_summary(df, "region")
    store_type_summary = dimension_summary(df, "store_type")

    segments.to_csv(OUTPUT_TABLES / "segment_summary.csv", index=False)
    theme_matrix.to_csv(OUTPUT_TABLES / "segment_theme_matrix.csv", index=False)
    channel_summary.to_csv(OUTPUT_TABLES / "channel_summary.csv", index=False)
    region_summary.to_csv(OUTPUT_TABLES / "region_summary.csv", index=False)
    store_type_summary.to_csv(OUTPUT_TABLES / "store_type_summary.csv", index=False)

    save_segment_charts(segments, theme_matrix)
    print(f"Segment analysis complete: {len(segments)} segments profiled")


if __name__ == "__main__":
    main()
