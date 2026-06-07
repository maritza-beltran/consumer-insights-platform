"""Analyze VoC theme prevalence and impact on NPS, CSAT, and revisit intent."""

from __future__ import annotations

import matplotlib.pyplot as plt
import pandas as pd

from config import OUTPUT_CHARTS, OUTPUT_TABLES, PROCESSED_DIR
from metrics import standard_nps, theme_priority_score


def _commented_surveys(df: pd.DataFrame) -> pd.DataFrame:
    """Surveys with linked guest comment text."""
    return df[df["comment_text"].astype(str).str.strip() != ""]


def theme_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate theme metrics by primary_theme for surveys with comments."""
    commented = _commented_surveys(df)
    total = len(commented)

    theme_groups = commented.groupby("primary_theme")
    summary = theme_groups.agg(
        comment_count=("survey_id", "count"),
        negative_comment_count=("is_negative_experience", "sum"),
        avg_csat=("csat", "mean"),
        avg_revisit_intent=("revisit_intent", "mean"),
        detractor_share=("nps", lambda s: (s <= 6).mean()),
        low_csat_share=("csat", lambda s: (s <= 2).mean()),
    ).reset_index()
    summary["avg_nps"] = theme_groups["nps"].apply(standard_nps).values
    summary["share_of_comments"] = summary["comment_count"] / total
    summary["negative_share"] = summary["negative_comment_count"] / summary["comment_count"]
    cols = [
        "primary_theme",
        "comment_count",
        "share_of_comments",
        "negative_comment_count",
        "negative_share",
        "avg_nps",
        "avg_csat",
        "avg_revisit_intent",
        "detractor_share",
        "low_csat_share",
    ]
    return (
        summary[cols]
        .sort_values("comment_count", ascending=False)
        .round(4)
        .reset_index(drop=True)
    )


def theme_impact(df: pd.DataFrame, summary: pd.DataFrame | None = None) -> pd.DataFrame:
    """
    Compare each theme's satisfaction metrics to brand-wide averages.

    ``impact_rank`` uses a multi-factor priority score (frequency, negative
    sentiment, NPS/CSAT/revisit gaps) — not comment volume alone.
    """
    commented = _commented_surveys(df)
    overall_csat = commented["csat"].mean()
    overall_revisit = commented["revisit_intent"].mean()

    theme_groups = commented.groupby("primary_theme")
    impact = theme_groups.agg(
        theme_avg_csat=("csat", "mean"),
        theme_avg_revisit_intent=("revisit_intent", "mean"),
        comment_count=("survey_id", "count"),
    ).reset_index()
    overall_nps = standard_nps(commented["nps"])
    impact["theme_avg_nps"] = theme_groups["nps"].apply(standard_nps).values
    impact["overall_avg_nps"] = overall_nps
    impact["theme_nps_gap"] = impact["theme_avg_nps"] - overall_nps
    impact["overall_avg_csat"] = round(overall_csat, 4)
    impact["theme_csat_gap"] = impact["theme_avg_csat"] - overall_csat
    impact["overall_avg_revisit_intent"] = round(overall_revisit, 4)
    impact["theme_revisit_gap"] = impact["theme_avg_revisit_intent"] - overall_revisit

    theme_summary_df = summary if summary is not None else theme_summary(df)
    merged = impact.merge(
        theme_summary_df[["primary_theme", "share_of_comments", "negative_share"]],
        on="primary_theme",
        how="left",
    )
    merged["priority_score"] = theme_priority_score(
        merged["share_of_comments"],
        merged["negative_share"],
        merged["theme_nps_gap"],
        merged["theme_csat_gap"],
        merged["theme_revisit_gap"],
    )
    merged["impact_rank"] = merged["priority_score"].rank(
        ascending=False, method="dense"
    ).astype(int)

    cols = [
        "primary_theme",
        "overall_avg_nps",
        "theme_avg_nps",
        "theme_nps_gap",
        "overall_avg_csat",
        "theme_avg_csat",
        "theme_csat_gap",
        "overall_avg_revisit_intent",
        "theme_avg_revisit_intent",
        "theme_revisit_gap",
        "priority_score",
        "impact_rank",
    ]
    return merged[cols].sort_values("impact_rank").round(4).reset_index(drop=True)


def detractor_theme_analysis(df: pd.DataFrame) -> pd.DataFrame:
    """Theme concentration among detractor (NPS 0–6) comments."""
    commented = _commented_surveys(df)
    detractors = commented[commented["nps"] <= 6]
    total = len(commented)
    detractor_total = len(detractors)

    theme_counts = commented.groupby("primary_theme").size().rename("all_count")
    detractor_counts = detractors.groupby("primary_theme").size().rename("detractor_count")

    analysis = (
        pd.concat([theme_counts, detractor_counts], axis=1)
        .fillna(0)
        .astype(int)
        .reset_index()
    )
    analysis["share_of_all_comments"] = analysis["all_count"] / total
    analysis["share_of_detractor_comments"] = analysis["detractor_count"] / detractor_total
    analysis["detractor_over_index"] = (
        analysis["share_of_detractor_comments"] / analysis["share_of_all_comments"]
    ).replace([float("inf")], 0)

    theme_groups = commented.groupby("primary_theme")
    metrics = theme_groups.agg(negative_share=("is_negative_experience", "mean")).reset_index()
    metrics["avg_nps"] = theme_groups["nps"].apply(standard_nps).values
    analysis = analysis.merge(metrics, on="primary_theme")
    analysis = analysis.drop(columns=["all_count", "detractor_count"])

    return (
        analysis.sort_values("share_of_detractor_comments", ascending=False)
        .round(4)
        .reset_index(drop=True)
    )


def save_theme_charts(summary: pd.DataFrame, impact: pd.DataFrame) -> None:
    OUTPUT_CHARTS.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(10, 6))
    top = summary.head(10)
    ax.barh(top["primary_theme"], top["comment_count"], color="#6F4E37")
    ax.set_title("Top VoC Themes by Comment Volume")
    ax.invert_yaxis()
    fig.tight_layout()
    fig.savefig(OUTPUT_CHARTS / "theme_prevalence.png", dpi=120)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(10, 6))
    top_impact = impact.sort_values("theme_nps_gap").head(10)
    colors = ["#C0392B" if g < 0 else "#27AE60" for g in top_impact["theme_nps_gap"]]
    ax.barh(top_impact["primary_theme"], top_impact["theme_nps_gap"], color=colors)
    ax.axvline(0, color="black", linewidth=0.8)
    ax.set_title("NPS Gap vs Brand Average by Theme")
    ax.invert_yaxis()
    fig.tight_layout()
    fig.savefig(OUTPUT_CHARTS / "theme_nps_gap.png", dpi=120)
    plt.close(fig)


def main() -> None:
    OUTPUT_TABLES.mkdir(parents=True, exist_ok=True)
    df = pd.read_parquet(PROCESSED_DIR / "guest_surveys_classified.parquet")

    summary = theme_summary(df)
    impact = theme_impact(df, summary=summary)
    detractors = detractor_theme_analysis(df)

    summary.to_csv(OUTPUT_TABLES / "theme_summary.csv", index=False)
    impact.to_csv(OUTPUT_TABLES / "theme_impact.csv", index=False)
    detractors.to_csv(OUTPUT_TABLES / "detractor_theme_analysis.csv", index=False)
    save_theme_charts(summary, impact)

    top = impact.sort_values("impact_rank").iloc[0]
    print(f"Theme analysis complete: {len(summary)} themes")
    print(f"Top impact theme: {top['primary_theme']} (rank {top['impact_rank']})")


if __name__ == "__main__":
    main()
