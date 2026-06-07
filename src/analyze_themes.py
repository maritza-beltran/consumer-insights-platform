"""Analyze VoC theme prevalence and impact on NPS, CSAT, and revisit intent."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
PROCESSED_DIR = ROOT / "data" / "processed"
OUTPUT_TABLES = ROOT / "outputs" / "tables"
OUTPUT_CHARTS = ROOT / "outputs" / "charts"


def _explode_themes(df: pd.DataFrame) -> pd.DataFrame:
    exploded = df.explode("themes").rename(columns={"themes": "theme"})
    return exploded


def theme_prevalence(df: pd.DataFrame) -> pd.DataFrame:
    exploded = _explode_themes(df)
    counts = (
        exploded.groupby("theme")
        .agg(
            mention_count=("survey_id", "count"),
            avg_nps=("nps_score", "mean"),
            avg_csat=("csat_score", "mean"),
            avg_revisit=("revisit_intent", "mean"),
            pct_negative_sentiment=("comment_sentiment", lambda s: (s == "negative").mean()),
        )
        .reset_index()
    )
    counts["mention_share"] = counts["mention_count"] / len(df)
    counts = counts.sort_values("mention_count", ascending=False)
    return counts.round(4)


def theme_impact_vs_baseline(df: pd.DataFrame) -> pd.DataFrame:
    baseline_nps = df["nps_score"].mean()
    baseline_csat = df["csat_score"].mean()
    baseline_revisit = df["revisit_intent"].mean()

    exploded = _explode_themes(df)
    impact = (
        exploded.groupby("theme")
        .agg(
            mention_count=("survey_id", "count"),
            avg_nps=("nps_score", "mean"),
            avg_csat=("csat_score", "mean"),
            avg_revisit=("revisit_intent", "mean"),
            detractor_rate=("nps_category", lambda s: (s == "detractor").mean()),
        )
        .reset_index()
    )
    impact["nps_gap_vs_brand"] = impact["avg_nps"] - baseline_nps
    impact["csat_gap_vs_brand"] = impact["avg_csat"] - baseline_csat
    impact["revisit_gap_vs_brand"] = impact["avg_revisit"] - baseline_revisit
    impact["priority_score"] = (
        impact["mention_count"] / impact["mention_count"].max() * 0.4
        + impact["detractor_rate"] * 0.35
        + (-impact["nps_gap_vs_brand"] / 10) * 0.25
    )
    return impact.sort_values("priority_score", ascending=False).round(4)


def save_theme_charts(prevalence: pd.DataFrame, impact: pd.DataFrame) -> None:
    OUTPUT_CHARTS.mkdir(parents=True, exist_ok=True)

    fig, ax = plt.subplots(figsize=(10, 6))
    top = prevalence.head(10)
    ax.barh(top["theme"], top["mention_count"], color="#6F4E37")
    ax.set_title("Top VoC Themes by Mention Volume")
    ax.set_xlabel("Mentions")
    ax.invert_yaxis()
    fig.tight_layout()
    fig.savefig(OUTPUT_CHARTS / "theme_prevalence.png", dpi=120)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(10, 6))
    top_impact = impact.head(10)
    colors = ["#C0392B" if g < 0 else "#27AE60" for g in top_impact["nps_gap_vs_brand"]]
    ax.barh(top_impact["theme"], top_impact["nps_gap_vs_brand"], color=colors)
    ax.axvline(0, color="black", linewidth=0.8)
    ax.set_title("NPS Gap vs Brand Average by Theme")
    ax.set_xlabel("NPS gap")
    ax.invert_yaxis()
    fig.tight_layout()
    fig.savefig(OUTPUT_CHARTS / "theme_nps_gap.png", dpi=120)
    plt.close(fig)


def main() -> None:
    OUTPUT_TABLES.mkdir(parents=True, exist_ok=True)
    df = pd.read_parquet(PROCESSED_DIR / "guest_surveys_classified.parquet")

    prevalence = theme_prevalence(df)
    impact = theme_impact_vs_baseline(df)

    prevalence.to_csv(OUTPUT_TABLES / "theme_prevalence.csv", index=False)
    impact.to_csv(OUTPUT_TABLES / "theme_impact.csv", index=False)
    save_theme_charts(prevalence, impact)

    print(f"Theme analysis complete: {len(prevalence)} themes")
    print(f"Top priority theme: {impact.iloc[0]['theme']}")


if __name__ == "__main__":
    main()
