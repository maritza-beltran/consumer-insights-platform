"""Score store-level improvement opportunities."""

from __future__ import annotations

import matplotlib.pyplot as plt
import pandas as pd

from config import OUTPUT_CHARTS, OUTPUT_TABLES, PROCESSED_DIR


def _nps(series: pd.Series) -> float:
    return round(((series >= 9).mean() - (series <= 6).mean()) * 100, 1)


def store_performance(surveys: pd.DataFrame, stores: pd.DataFrame) -> pd.DataFrame:
    store_surveys = (
        surveys.groupby(["store_id", "store_name", "region", "store_type", "market"])
        .agg(
            survey_count=("survey_id", "count"),
            avg_nps=("nps", "mean"),
            avg_csat=("csat", "mean"),
            avg_revisit=("revisit_intent", "mean"),
            detractor_rate=("nps_category", lambda s: (s == "detractor").mean()),
            negative_sentiment_rate=("sentiment_label", lambda s: (s == "negative").mean()),
        )
        .reset_index()
    )
    store_surveys["store_nps"] = surveys.groupby("store_id")["nps"].apply(_nps).values
    merged = store_surveys.merge(
        stores[["store_id", "avg_daily_transactions", "avg_ticket", "franchise_corporate_flag"]],
        on="store_id",
        how="left",
    )
    merged["monthly_transactions"] = merged["avg_daily_transactions"] * 30
    merged["monthly_revenue_usd"] = merged["monthly_transactions"] * merged["avg_ticket"]
    return merged.round(4)


def top_store_themes(surveys: pd.DataFrame, store_ids: list[str], top_n: int = 3) -> pd.DataFrame:
    subset = surveys[surveys["store_id"].isin(store_ids)].explode("themes")
    counts = subset.groupby(["store_id", "themes"]).size().reset_index(name="mention_count")
    counts = counts.sort_values(["store_id", "mention_count"], ascending=[True, False])
    counts["rank"] = counts.groupby("store_id").cumcount() + 1
    return counts[counts["rank"] <= top_n].rename(columns={"themes": "theme"})


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
    scored["priority_tier"] = pd.qcut(scored["opportunity_score"], q=3, labels=["monitor", "improve", "urgent"])
    return scored.sort_values("opportunity_score", ascending=False).round(4)


def save_store_chart(scored: pd.DataFrame) -> None:
    OUTPUT_CHARTS.mkdir(parents=True, exist_ok=True)
    top = scored.head(15).sort_values("opportunity_score")
    colors = {"urgent": "#C0392B", "improve": "#E67E22", "monitor": "#95A5A6"}
    fig, ax = plt.subplots(figsize=(10, 7))
    ax.barh(top["store_name"], top["opportunity_score"], color=[colors.get(t, "#6F4E37") for t in top["priority_tier"]])
    ax.set_title("Top Store Improvement Opportunities")
    fig.tight_layout()
    fig.savefig(OUTPUT_CHARTS / "store_opportunities.png", dpi=120)
    plt.close(fig)


def main() -> None:
    OUTPUT_TABLES.mkdir(parents=True, exist_ok=True)
    surveys = pd.read_parquet(PROCESSED_DIR / "guest_surveys_classified.parquet")
    stores = pd.read_parquet(PROCESSED_DIR / "stores_clean.parquet")
    performance = store_performance(surveys, stores)
    scored = score_opportunities(performance)
    themes = top_store_themes(surveys, scored.head(10)["store_id"].tolist())
    scored.to_csv(OUTPUT_TABLES / "store_opportunity_scores.csv", index=False)
    themes.to_csv(OUTPUT_TABLES / "priority_store_themes.csv", index=False)
    save_store_chart(scored)
    print(f"Store scoring complete: {len(scored)} stores ranked")
    print(f"Top opportunity store: {scored.iloc[0]['store_name']}")


if __name__ == "__main__":
    main()
