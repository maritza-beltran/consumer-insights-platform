"""Estimate financial impact of addressing top VoC pain points."""

from __future__ import annotations

import json

import pandas as pd

from config import OUTPUT_TABLES, PROCESSED_DIR

DETRACTOR_RECOVERY_RATE = 0.15
IMPLEMENTATION_COST_USD = 85_000


def _annual_revenue(stores: pd.DataFrame) -> float:
    return float((stores["avg_daily_transactions"] * stores["avg_ticket"] * 365).sum())


def estimate_theme_impact(theme_impact: pd.DataFrame, stores: pd.DataFrame, surveys: pd.DataFrame) -> dict:
    brand_nps = round(((surveys["nps"] >= 9).mean() - (surveys["nps"] <= 6).mean()) * 100, 1)
    top_theme = theme_impact.sort_values("impact_rank").iloc[0]
    theme_name = top_theme["primary_theme"]

    theme_summary_path = OUTPUT_TABLES / "theme_summary.csv"
    if theme_summary_path.exists():
        theme_summary = pd.read_csv(theme_summary_path)
        theme_row = theme_summary[theme_summary["primary_theme"] == theme_name]
        affected_share = float(theme_row["share_of_comments"].iloc[0]) if len(theme_row) else 0.1
        detractor_rate = float(theme_row["detractor_share"].iloc[0]) if len(theme_row) else 0.4
    else:
        affected_share = 0.1
        detractor_rate = 0.4

    annual_revenue = _annual_revenue(stores)

    priority_path = OUTPUT_TABLES / "store_opportunity_ranking.csv"
    if priority_path.exists():
        priority_stores = pd.read_csv(priority_path)
        urgent_cutoff = priority_stores["opportunity_score"].quantile(0.67)
        urgent = priority_stores[priority_stores["opportunity_score"] >= urgent_cutoff]
        urgent_revenue = float(
            (urgent["avg_daily_transactions"] * urgent["avg_ticket"] * 365).sum()
        )
    else:
        urgent = pd.DataFrame()
        urgent_revenue = annual_revenue * 0.35

    revenue_at_risk = urgent_revenue * affected_share * detractor_rate
    recoverable_revenue = revenue_at_risk * DETRACTOR_RECOVERY_RATE
    net_impact = recoverable_revenue - IMPLEMENTATION_COST_USD

    return {
        "brand_nps_baseline": brand_nps,
        "recommended_focus_theme": theme_name,
        "affected_guest_share": round(affected_share, 4),
        "pilot_scope": "top_tertile_opportunity_stores",
        "revenue_at_risk_usd": round(revenue_at_risk, 2),
        "recoverable_revenue_usd": round(recoverable_revenue, 2),
        "implementation_cost_usd": IMPLEMENTATION_COST_USD,
        "net_annual_impact_usd": round(net_impact, 2),
        "urgent_store_count": len(urgent),
        "urgent_store_annual_revenue_usd": round(urgent_revenue, 2),
        "meets_100k_threshold": net_impact >= 100_000,
        "assumptions": {
            "detractor_recovery_rate": DETRACTOR_RECOVERY_RATE,
            "implementation_scope": "peak-hour staffing + mobile order pickup workflow at top-opportunity stores",
        },
    }


def build_executive_recommendation(impact: dict) -> str:
    theme = impact["recommended_focus_theme"].replace("_", " ").title()
    return (
        f"## Primary Recommendation\n\n"
        f"Prioritize **{theme}** across **{impact['urgent_store_count']} top-opportunity stores**.\n\n"
        f"- Recoverable annual revenue: **${impact['recoverable_revenue_usd']:,.0f}**\n"
        f"- Implementation cost: **${impact['implementation_cost_usd']:,.0f}**\n"
        f"- **Net annual impact: ${impact['net_annual_impact_usd']:,.0f}**\n"
    )


def main() -> None:
    OUTPUT_TABLES.mkdir(parents=True, exist_ok=True)
    surveys = pd.read_parquet(PROCESSED_DIR / "guest_surveys_classified.parquet")
    stores = pd.read_parquet(PROCESSED_DIR / "stores_clean.parquet")
    theme_impact = pd.read_csv(OUTPUT_TABLES / "theme_impact.csv")
    impact = estimate_theme_impact(theme_impact, stores, surveys)
    (OUTPUT_TABLES / "impact_sizing.json").write_text(json.dumps(impact, indent=2))
    (OUTPUT_TABLES / "executive_recommendation_snippet.md").write_text(build_executive_recommendation(impact))
    print(f"Impact model complete: net impact ${impact['net_annual_impact_usd']:,.0f}")
    print(f"$100K+ threshold: {impact['meets_100k_threshold']}")


if __name__ == "__main__":
    main()
