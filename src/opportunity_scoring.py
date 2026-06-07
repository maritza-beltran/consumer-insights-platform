"""Score store-level improvement opportunities."""

from __future__ import annotations

import matplotlib.pyplot as plt
import pandas as pd

from config import OUTPUT_CHARTS, OUTPUT_TABLES, PROCESSED_DIR, THEME_RECOMMENDED_ACTIONS
from metrics import minmax_index, standard_nps


def _top_negative_theme(store_df: pd.DataFrame) -> str:
    negative = store_df[store_df["is_negative_experience"]]
    if negative.empty:
        return "general_experience"
    counts = negative.groupby("primary_theme").size()
    return counts.idxmax()


def _recommended_action(theme: str) -> str:
    return THEME_RECOMMENDED_ACTIONS.get(theme, THEME_RECOMMENDED_ACTIONS["general_experience"])


def store_opportunity_ranking(surveys: pd.DataFrame, stores: pd.DataFrame) -> pd.DataFrame:
    brand_nps = standard_nps(surveys["nps"])
    brand_revisit = surveys["revisit_intent"].mean()
    max_traffic = stores["avg_daily_transactions"].max()

    store_groups = surveys.groupby(["store_id", "store_name", "market", "region", "store_type"])
    rows: list[dict] = []
    for (store_id, store_name, market, region, store_type), group in store_groups:
        store_row = stores.loc[stores["store_id"] == store_id].iloc[0]
        top_theme = _top_negative_theme(group)
        store_nps = standard_nps(group["nps"])
        negative_rate = group["is_negative_experience"].mean()
        nps_gap = round(store_nps - brand_nps, 4)
        revisit_gap = round(group["revisit_intent"].mean() - brand_revisit, 4)
        traffic_weight = store_row["avg_daily_transactions"] / max_traffic

        rows.append(
            {
                "store_id": store_id,
                "store_name": store_name,
                "market": market,
                "region": region,
                "store_type": store_type,
                "avg_daily_transactions": store_row["avg_daily_transactions"],
                "avg_ticket": store_row["avg_ticket"],
                "nps": store_nps,
                "csat": round(group["csat"].mean(), 4),
                "revisit_intent": round(group["revisit_intent"].mean(), 4),
                "top_negative_theme": top_theme,
                "negative_theme_rate": round(negative_rate, 4),
                "nps_gap": nps_gap,
                "revisit_intent_gap": revisit_gap,
                "traffic_weight": round(traffic_weight, 4),
            }
        )

    ranking = pd.DataFrame(rows)
    ranking["negative_theme_rate_index"] = minmax_index(ranking["negative_theme_rate"])
    ranking["nps_gap_index"] = minmax_index(-ranking["nps_gap"])
    ranking["revisit_intent_gap_index"] = minmax_index(-ranking["revisit_intent_gap"])
    ranking["opportunity_score"] = (
        0.35 * ranking["negative_theme_rate_index"]
        + 0.25 * ranking["nps_gap_index"]
        + 0.20 * ranking["revisit_intent_gap_index"]
        + 0.20 * ranking["traffic_weight"]
    ).round(4)
    ranking["recommended_action"] = ranking["top_negative_theme"].map(_recommended_action)
    ranking["estimated_90_day_upside"] = (
        ranking["avg_daily_transactions"]
        * ranking["avg_ticket"]
        * 90
        * ranking["opportunity_score"]
        * 0.08
    ).round(2)

    return ranking.sort_values("opportunity_score", ascending=False).reset_index(drop=True)


def save_store_chart(ranking: pd.DataFrame) -> None:
    OUTPUT_CHARTS.mkdir(parents=True, exist_ok=True)
    top = ranking.head(15).sort_values("opportunity_score")
    fig, ax = plt.subplots(figsize=(10, 7))
    ax.barh(top["store_name"], top["opportunity_score"], color="#6F4E37")
    ax.set_title("Top Store Improvement Opportunities")
    fig.tight_layout()
    fig.savefig(OUTPUT_CHARTS / "store_opportunities.png", dpi=120)
    plt.close(fig)


def main() -> None:
    OUTPUT_TABLES.mkdir(parents=True, exist_ok=True)
    surveys = pd.read_parquet(PROCESSED_DIR / "guest_surveys_classified.parquet")
    stores = pd.read_parquet(PROCESSED_DIR / "stores_clean.parquet")
    ranking = store_opportunity_ranking(surveys, stores)
    ranking.to_csv(OUTPUT_TABLES / "store_opportunity_ranking.csv", index=False)
    save_store_chart(ranking)
    print(f"Store scoring complete: {len(ranking)} stores ranked")
    print(f"Top opportunity store: {ranking.iloc[0]['store_name']}")


if __name__ == "__main__":
    main()
