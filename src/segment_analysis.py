"""Segment- and dimension-level VoC performance analysis."""

from __future__ import annotations

import matplotlib.pyplot as plt
import pandas as pd

from config import OUTPUT_CHARTS, OUTPUT_TABLES, PROCESSED_DIR


def _nps(series: pd.Series) -> float:
    return round(((series >= 9).mean() - (series <= 6).mean()) * 100, 1)


def segment_summary(df: pd.DataFrame) -> pd.DataFrame:
    summary = (
        df.groupby("guest_segment")
        .agg(
            survey_count=("survey_id", "count"),
            avg_nps=("nps", "mean"),
            avg_csat=("csat", "mean"),
            avg_revisit=("revisit_intent", "mean"),
            detractor_rate=("nps_category", lambda s: (s == "detractor").mean()),
        )
        .reset_index()
    )
    summary["brand_nps"] = summary["guest_segment"].map(df.groupby("guest_segment")["nps"].apply(_nps))
    return summary.round(4)


def dimension_summary(df: pd.DataFrame, dimension: str) -> pd.DataFrame:
    return (
        df.groupby(dimension)
        .agg(
            survey_count=("survey_id", "count"),
            avg_nps=("nps", "mean"),
            avg_csat=("csat", "mean"),
            avg_revisit=("revisit_intent", "mean"),
            detractor_rate=("nps_category", lambda s: (s == "detractor").mean()),
        )
        .reset_index()
        .round(4)
    )


def segment_theme_matrix(df: pd.DataFrame) -> pd.DataFrame:
    exploded = df.explode("themes").rename(columns={"themes": "theme"})
    matrix = exploded.groupby(["guest_segment", "theme"]).size().reset_index(name="mention_count")
    totals = exploded.groupby("guest_segment").size().rename("segment_total")
    matrix = matrix.merge(totals, on="guest_segment")
    matrix["mention_share"] = matrix["mention_count"] / matrix["segment_total"]
    return matrix.round(4)


def save_segment_charts(segment_df: pd.DataFrame, theme_matrix: pd.DataFrame) -> None:
    OUTPUT_CHARTS.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.bar(segment_df["guest_segment"], segment_df["brand_nps"], color="#6F4E37")
    ax.set_title("Brand NPS by Guest Segment")
    ax.tick_params(axis="x", rotation=20)
    fig.tight_layout()
    fig.savefig(OUTPUT_CHARTS / "segment_nps.png", dpi=120)
    plt.close(fig)

    pivot = theme_matrix.pivot(index="theme", columns="guest_segment", values="mention_share").fillna(0)
    top_themes = pivot.sum(axis=1).sort_values(ascending=False).head(8).index
    pivot = pivot.loc[top_themes]
    fig, ax = plt.subplots(figsize=(11, 6))
    im = ax.imshow(pivot.values, aspect="auto", cmap="YlOrBr")
    ax.set_xticks(range(len(pivot.columns)))
    ax.set_xticklabels(pivot.columns, rotation=20)
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
