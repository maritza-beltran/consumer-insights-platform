"""Score store-level improvement opportunities from VoC and performance signals."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
PROCESSED_DIR = ROOT / "data" / "processed"
OUTPUT_TABLES = ROOT / "outputs" / "tables"
OUTPUT_CHARTS = ROOT / "outputs" / "charts"


def _nps_score(series: pd.Series) -> float:
    return round(((series >= 9).mean() - (series <= 6).mean()) * 100, 1)


def store_performance(surveys: pd.DataFrame, stores: pd.DataFrame) -> pd.DataFrame:
    store_surveys = (
        surveys.groupby(["store_id", "store_name", "region", "store_type"])
        .agg(
            survey_count=("survey_id", "count"),
            avg_nps=("nps_score", "mean"),
            avg_csat=("csat_score", "mean"),
            avg_revisit=("revisit_intent", "mean"),
            detractor_rate=("nps_category", lambda s: (s == "detractor").mean()),
            negative_sentiment_rate=("comment_sentiment", lambda s: (s == "negative").mean()),
        )
        .reset_index()
    )
    store_surveys["store_nps"] = (
        surveys.groupby("store_id")["nps_score"].apply(_nps_score).values
    )

    merged = store_surveys.merge(
        stores[["store_id", "monthly_transactions", "avg_ticket_usd"]],
        on="store_id",
        how="left",
    )
    merged["monthly_revenue_usd"] = merged["monthly_transactions"] * merged["avg_ticket_usd"]
    return merged.round(4)


def top_store_themes(surveys: pd.DataFrame, store_ids: list[str], top_n: int = 3) -> pd.DataFrame:
    subset = surveys[surveys["store_id"].isin(store_ids)].explode("themes")
    theme_counts = (
        subset.groupby(["store_id", "themes"])
        .size()
        .reset_index(name="mention_count")
    )
    theme_counts = theme_counts.sort_values(["store_id", "mention_count"], ascending=[True, False])
    theme_counts["rank"] = theme_counts.groupby("store_id").cumcount() + 1
    return theme_counts[theme_counts["rank"] <= top_n].rename(columns={"themes": "theme"})


def score_opportunities(store_df: pd.DataFrame) -> pd.DataFrame:
    scored = store_df.copy()
    scored["nps_gap_vs_brand"] = scored["avg_nps"] - scored["avg_nps"].mean()
    scored["volume_weight"] = scored["survey_count"] / scored["survey_count"].max()
    scored["revenue_weight"] = scored["monthly_revenue_usd"] / scored["monthly_revenue_usd"].max()

    scored["opportunity_score"] = (
        scored["detractor_rate"] * 0.35
        + scored["negative_sentiment_rate"] * 0.25
        + (-scored["nps_gap_vs_brand"] / 10) * 0.2
        + scored["volume_weight"] * 0.1
        + scored["revenue_weight"] * 0.1
    )
    scored["priority_tier"] = pd.qcut(
        scored["opportunity_score"],
        q=3,
        labels=["monitor", "improve", "urgent"],
    )
    return scored.sort_values("opportunity_score", ascending=False).round(4)


def save_store_chart(scored: pd.DataFrame) -> None:
    OUTPUT_CHARTS.mkdir(parents=True, exist_ok=True)
    top = scored.head(15).sort_values("opportunity_score")

    fig, ax = plt.subplots(figsize=(10, 7))
    colors = {"urgent": "#C0392B", "improve": "#E67E22", "monitor": "#95A5A6"}
    bar_colors = [colors.get(t, "#6F4E37") for t in top["priority_tier"]]
    ax.barh(top["store_name"], top["opportunity_score"], color=bar_colors)
    ax.set_title("Top Store Improvement Opportunities")
    ax.set_xlabel("Opportunity score")
    fig.tight_layout()
    fig.savefig(OUTPUT_CHARTS / "store_opportunities.png", dpi=120)
    plt.close(fig)


def main() -> None:
    OUTPUT_TABLES.mkdir(parents=True, exist_ok=True)
    surveys = pd.read_parquet(PROCESSED_DIR / "guest_surveys_classified.parquet")
    stores = pd.read_parquet(PROCESSED_DIR / "stores_clean.parquet")

    performance = store_performance(surveys, stores)
    scored = score_opportunities(performance)

    priority_stores = scored.head(10)["store_id"].tolist()
    themes = top_store_themes(surveys, priority_stores)

    scored.to_csv(OUTPUT_TABLES / "store_opportunity_scores.csv", index=False)
    themes.to_csv(OUTPUT_TABLES / "priority_store_themes.csv", index=False)
    save_store_chart(scored)

    print(f"Store scoring complete: {len(scored)} stores ranked")
    print(f"Top opportunity store: {scored.iloc[0]['store_name']}")


if __name__ == "__main__":
    main()
