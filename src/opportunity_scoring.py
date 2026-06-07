"""Score store-level improvement opportunities."""

from __future__ import annotations

import matplotlib.pyplot as plt
import pandas as pd

from config import OUTPUT_CHARTS, OUTPUT_TABLES, PROCESSED_DIR

THEME_ACTIONS = {
    "speed_of_service": "Deploy peak-hour staffing and line-busting roles.",
    "drink_consistency": "Run weekly calibration and recipe QA audits.",
    "order_accuracy": "Add order confirmation at pickup window and mobile handoff.",
    "staff_friendliness": "Coach service recovery and greeting standards.",
    "cleanliness": "Increase mid-day dining-area and restroom checks.",
    "mobile_app_issues": "Fix order-ready timing and pickup status notifications.",
    "rewards_value": "Pilot bonus-star campaigns for repeat visits.",
    "price_value": "Highlight value bundles and size clarity on menu boards.",
    "seasonal_menu_interest": "Promote LTO trial offers with quality follow-up.",
    "drive_thru_experience": "Optimize lane staffing and speaker-box confirmation.",
    "general_experience": "Implement service recovery playbook for detractors.",
}


def _brand_nps(series: pd.Series) -> float:
    return round(((series >= 9).mean() - (series <= 6).mean()) * 100, 1)


def _top_negative_theme(store_df: pd.DataFrame) -> str:
    negative = store_df[store_df["is_negative_experience"]]
    if negative.empty:
        return "general_experience"
    counts = negative.groupby("primary_theme").size()
    return counts.idxmax()


def _recommended_action(theme: str, region: str) -> str:
    action = THEME_ACTIONS.get(theme, THEME_ACTIONS["general_experience"])
    return f"{region}: focus on {theme.replace('_', ' ')}. {action}"


def store_opportunity_ranking(surveys: pd.DataFrame, stores: pd.DataFrame) -> pd.DataFrame:
    brand_nps = _brand_nps(surveys["nps"])
    brand_revisit = surveys["revisit_intent"].mean()
    max_traffic = stores["avg_daily_transactions"].max()

    store_groups = surveys.groupby(["store_id", "store_name", "market", "region", "store_type"])
    rows: list[dict] = []
    for (store_id, store_name, market, region, store_type), group in store_groups:
        store_row = stores.loc[stores["store_id"] == store_id].iloc[0]
        top_theme = _top_negative_theme(group)
        store_nps = _brand_nps(group["nps"])
        negative_rate = group["is_negative_experience"].mean()
        nps_gap = store_nps - brand_nps
        revisit_gap = group["revisit_intent"].mean() - brand_revisit
        traffic_weight = store_row["avg_daily_transactions"] / max_traffic
        opportunity_score = (
            negative_rate * 0.35
            + max(0, -nps_gap / 100) * 0.30
            + max(0, -revisit_gap / 5) * 0.20
            + traffic_weight * 0.15
        )
        quarterly_revenue = store_row["avg_daily_transactions"] * store_row["avg_ticket"] * 90
        estimated_upside = quarterly_revenue * opportunity_score * 0.08

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
                "nps_gap": round(nps_gap, 4),
                "revisit_intent_gap": round(revisit_gap, 4),
                "traffic_weight": round(traffic_weight, 4),
                "opportunity_score": round(opportunity_score, 4),
                "recommended_action": _recommended_action(top_theme, region),
                "estimated_90_day_upside": round(estimated_upside, 2),
            }
        )

    ranking = pd.DataFrame(rows).sort_values("opportunity_score", ascending=False).reset_index(drop=True)
    return ranking


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
