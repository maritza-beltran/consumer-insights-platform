"""Analyze VoC theme prevalence and impact on NPS, CSAT, and revisit intent."""

from __future__ import annotations

import matplotlib.pyplot as plt
import pandas as pd

from config import OUTPUT_CHARTS, OUTPUT_TABLES, PROCESSED_DIR


def _commented_surveys(df: pd.DataFrame) -> pd.DataFrame:
    """Surveys with linked guest comment text."""
    return df[df["comment_text"].astype(str).str.strip() != ""]


def theme_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate theme metrics by primary_theme for surveys with comments."""
    commented = _commented_surveys(df)
    total = len(commented)

    summary = (
        commented.groupby("primary_theme")
        .agg(
            comment_count=("survey_id", "count"),
            negative_comment_count=("is_negative_experience", "sum"),
            avg_nps=("nps", "mean"),
            avg_csat=("csat", "mean"),
            avg_revisit_intent=("revisit_intent", "mean"),
            detractor_share=("nps", lambda s: (s <= 6).mean()),
            low_csat_share=("csat", lambda s: (s <= 2).mean()),
        )
        .reset_index()
    )
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


def theme_impact(df: pd.DataFrame) -> pd.DataFrame:
    """Compare each theme's satisfaction metrics to brand-wide averages."""
    commented = _commented_surveys(df)
    overall_nps = commented["nps"].mean()
    overall_csat = commented["csat"].mean()
    overall_revisit = commented["revisit_intent"].mean()

    impact = (
        commented.groupby("primary_theme")
        .agg(
            theme_avg_nps=("nps", "mean"),
            theme_avg_csat=("csat", "mean"),
            theme_avg_revisit_intent=("revisit_intent", "mean"),
            comment_count=("survey_id", "count"),
        )
        .reset_index()
    )
    impact["overall_avg_nps"] = round(overall_nps, 4)
    impact["theme_nps_gap"] = impact["theme_avg_nps"] - overall_nps
    impact["overall_avg_csat"] = round(overall_csat, 4)
    impact["theme_csat_gap"] = impact["theme_avg_csat"] - overall_csat
    impact["overall_avg_revisit_intent"] = round(overall_revisit, 4)
    impact["theme_revisit_gap"] = impact["theme_avg_revisit_intent"] - overall_revisit

    impact["impact_rank"] = (
        impact["theme_nps_gap"].abs()
        + impact["theme_csat_gap"].abs()
        + impact["theme_revisit_gap"].abs()
    ).rank(ascending=False, method="dense").astype(int)

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
        "impact_rank",
    ]
    return impact[cols].sort_values("impact_rank").round(4).reset_index(drop=True)


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

    metrics = (
        commented.groupby("primary_theme")
        .agg(avg_nps=("nps", "mean"), negative_share=("is_negative_experience", "mean"))
        .reset_index()
    )
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
    impact = theme_impact(df)
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
