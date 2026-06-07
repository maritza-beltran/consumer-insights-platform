"""Segment- and region-level VoC performance analysis."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
PROCESSED_DIR = ROOT / "data" / "processed"
OUTPUT_TABLES = ROOT / "outputs" / "tables"
OUTPUT_CHARTS = ROOT / "outputs" / "charts"


def _nps_score(series: pd.Series) -> float:
    promoters = (series >= 9).mean()
    detractors = (series <= 6).mean()
    return round((promoters - detractors) * 100, 1)


def segment_summary(df: pd.DataFrame) -> pd.DataFrame:
    summary = (
        df.groupby("segment")
        .agg(
            survey_count=("survey_id", "count"),
            avg_nps=("nps_score", "mean"),
            avg_csat=("csat_score", "mean"),
            avg_revisit=("revisit_intent", "mean"),
            detractor_rate=("nps_category", lambda s: (s == "detractor").mean()),
        )
        .reset_index()
    )
    summary["brand_nps"] = summary["segment"].map(df.groupby("segment")["nps_score"].apply(_nps_score))
    return summary.round(4)


def segment_theme_matrix(df: pd.DataFrame) -> pd.DataFrame:
    exploded = df.explode("themes").rename(columns={"themes": "theme"})
    matrix = (
        exploded.groupby(["segment", "theme"])
        .size()
        .reset_index(name="mention_count")
    )
    segment_totals = exploded.groupby("segment").size().rename("segment_total")
    matrix = matrix.merge(segment_totals, on="segment")
    matrix["mention_share"] = matrix["mention_count"] / matrix["segment_total"]
    return matrix.round(4)


def region_channel_summary(df: pd.DataFrame) -> pd.DataFrame:
    summary = (
        df.groupby(["region", "channel"])
        .agg(
            survey_count=("survey_id", "count"),
            avg_nps=("nps_score", "mean"),
            avg_csat=("csat_score", "mean"),
            detractor_rate=("nps_category", lambda s: (s == "detractor").mean()),
        )
        .reset_index()
    )
    return summary.round(4)


def save_segment_charts(segment_df: pd.DataFrame, theme_matrix: pd.DataFrame) -> None:
    OUTPUT_CHARTS.mkdir(parents=True, exist_ok=True)

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.bar(segment_df["segment"], segment_df["brand_nps"], color="#6F4E37")
    ax.set_title("Brand NPS by Guest Segment")
    ax.set_ylabel("NPS")
    ax.tick_params(axis="x", rotation=15)
    fig.tight_layout()
    fig.savefig(OUTPUT_CHARTS / "segment_nps.png", dpi=120)
    plt.close(fig)

    pivot = theme_matrix.pivot(index="theme", columns="segment", values="mention_share").fillna(0)
    top_themes = pivot.sum(axis=1).sort_values(ascending=False).head(8).index
    pivot = pivot.loc[top_themes]

    fig, ax = plt.subplots(figsize=(10, 6))
    im = ax.imshow(pivot.values, aspect="auto", cmap="YlOrBr")
    ax.set_xticks(range(len(pivot.columns)))
    ax.set_xticklabels(pivot.columns, rotation=15)
    ax.set_yticks(range(len(pivot.index)))
    ax.set_yticklabels(pivot.index)
    ax.set_title("Theme Mention Share by Segment")
    fig.colorbar(im, ax=ax, label="Share")
    fig.tight_layout()
    fig.savefig(OUTPUT_CHARTS / "segment_theme_heatmap.png", dpi=120)
    plt.close(fig)


def main() -> None:
    OUTPUT_TABLES.mkdir(parents=True, exist_ok=True)
    df = pd.read_parquet(PROCESSED_DIR / "guest_surveys_classified.parquet")

    segments = segment_summary(df)
    theme_matrix = segment_theme_matrix(df)
    region_channel = region_channel_summary(df)

    segments.to_csv(OUTPUT_TABLES / "segment_summary.csv", index=False)
    theme_matrix.to_csv(OUTPUT_TABLES / "segment_theme_matrix.csv", index=False)
    region_channel.to_csv(OUTPUT_TABLES / "region_channel_summary.csv", index=False)
    save_segment_charts(segments, theme_matrix)

    print(f"Segment analysis complete: {len(segments)} segments profiled")


if __name__ == "__main__":
    main()
