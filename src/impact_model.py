"""Estimate financial impact of addressing top VoC pain points."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
PROCESSED_DIR = ROOT / "data" / "processed"
OUTPUT_TABLES = ROOT / "outputs" / "tables"

# Assumptions documented for executive transparency (synthetic scenario)
NPS_TO_REVISIT_ELASTICITY = 0.018  # 1-point NPS lift -> 1.8% revisit rate lift
AVG_VISITS_PER_GUEST_YEAR = 18
IMPLEMENTATION_COST_USD = 85_000
RECOVERY_RATE_OF_AT_RISK = 0.50  # share of theme-linked revenue at risk recaptured post-intervention


def _annual_revenue(stores: pd.DataFrame) -> float:
    return float((stores["monthly_transactions"] * stores["avg_ticket_usd"] * 12).sum())


def estimate_theme_impact(
    theme_impact: pd.DataFrame,
    stores: pd.DataFrame,
    surveys: pd.DataFrame,
) -> dict:
    brand_nps = round(
        ((surveys["nps_score"] >= 9).mean() - (surveys["nps_score"] <= 6).mean()) * 100,
        1,
    )
    top_theme = theme_impact.iloc[0]
    theme_name = top_theme["theme"]

    affected_share = float(top_theme["mention_count"] / len(surveys))
    nps_lift_points = float(min(8, abs(top_theme["nps_gap_vs_brand"]) * 0.6))

    revisit_lift_pct = nps_lift_points * NPS_TO_REVISIT_ELASTICITY
    annual_revenue = _annual_revenue(stores)
    detractor_rate = float(top_theme["detractor_rate"])
    revenue_at_risk = annual_revenue * affected_share * detractor_rate

    elasticity_revenue = annual_revenue * affected_share * revisit_lift_pct
    recoverable_revenue = revenue_at_risk * RECOVERY_RATE_OF_AT_RISK
    net_impact = recoverable_revenue - IMPLEMENTATION_COST_USD

    priority_path = OUTPUT_TABLES / "store_opportunity_scores.csv"
    if priority_path.exists():
        priority_stores = pd.read_csv(priority_path)
        urgent_stores = priority_stores[priority_stores["priority_tier"] == "urgent"]
        urgent_revenue = float(urgent_stores["monthly_revenue_usd"].sum() * 12)
    else:
        urgent_stores = pd.DataFrame()
        urgent_revenue = 0.0

    return {
        "brand_nps_baseline": brand_nps,
        "recommended_focus_theme": theme_name,
        "affected_guest_share": round(affected_share, 4),
        "projected_nps_lift_points": round(nps_lift_points, 2),
        "projected_revisit_lift_pct": round(revisit_lift_pct, 4),
        "annual_system_revenue_usd": round(annual_revenue, 2),
        "revenue_at_risk_usd": round(revenue_at_risk, 2),
        "recoverable_revenue_usd": round(recoverable_revenue, 2),
        "implementation_cost_usd": IMPLEMENTATION_COST_USD,
        "net_annual_impact_usd": round(net_impact, 2),
        "urgent_store_count": len(urgent_stores),
        "urgent_store_annual_revenue_usd": round(urgent_revenue, 2),
        "meets_100k_threshold": net_impact >= 100_000,
        "elasticity_based_revenue_usd": round(elasticity_revenue, 2),
        "assumptions": {
            "nps_to_revisit_elasticity": NPS_TO_REVISIT_ELASTICITY,
            "recovery_rate_of_at_risk": RECOVERY_RATE_OF_AT_RISK,
            "nps_gap_recovery_factor": 0.6,
            "implementation_scope": "peak-hour staffing + mobile order pickup workflow",
        },
    }


def build_executive_recommendation(impact: dict) -> str:
    theme = impact["recommended_focus_theme"].replace("_", " ").title()
    net = impact["net_annual_impact_usd"]
    nps_lift = impact["projected_nps_lift_points"]
    urgent = impact["urgent_store_count"]

    return (
        f"## Primary Recommendation\n\n"
        f"Leadership should prioritize **{theme}** interventions across the "
        f"**{urgent} highest-opportunity stores**, starting with peak-hour staffing "
        f"and mobile order pickup workflow fixes.\n\n"
        f"### Expected Impact\n"
        f"- Projected NPS lift: **+{nps_lift} points** among affected guests\n"
        f"- Recoverable annual revenue: **${impact['recoverable_revenue_usd']:,.0f}**\n"
        f"- Implementation cost: **${impact['implementation_cost_usd']:,.0f}**\n"
        f"- **Net annual impact: ${net:,.0f}** "
        f"({'meets' if impact['meets_100k_threshold'] else 'below'} $100K threshold)\n\n"
        f"### Why Now\n"
        f"- {impact['affected_guest_share']:.0%} of surveyed guests mention this theme\n"
        f"- Revenue at risk tied to detractor concentration: "
        f"**${impact['revenue_at_risk_usd']:,.0f}**\n"
    )


def main() -> None:
    OUTPUT_TABLES.mkdir(parents=True, exist_ok=True)
    surveys = pd.read_parquet(PROCESSED_DIR / "guest_surveys_classified.parquet")
    stores = pd.read_parquet(PROCESSED_DIR / "stores_clean.parquet")
    theme_impact = pd.read_csv(OUTPUT_TABLES / "theme_impact.csv")

    impact = estimate_theme_impact(theme_impact, stores, surveys)
    impact_path = OUTPUT_TABLES / "impact_sizing.json"
    impact_path.write_text(json.dumps(impact, indent=2))

    memo_snippet = build_executive_recommendation(impact)
    snippet_path = OUTPUT_TABLES / "executive_recommendation_snippet.md"
    snippet_path.write_text(memo_snippet)

    print(f"Impact model complete: net impact ${impact['net_annual_impact_usd']:,.0f}")
    print(f"$100K+ threshold: {impact['meets_100k_threshold']}")


if __name__ == "__main__":
    main()
