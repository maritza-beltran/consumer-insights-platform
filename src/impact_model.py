"""Estimate financial impact of addressing top VoC pain points."""

from __future__ import annotations

import json

import pandas as pd

from config import IMPACT_DEFAULTS, OUTPUT_TABLES, PROCESSED_DIR, THEME_RECOMMENDED_ACTIONS
from metrics import standard_nps


def build_impact_summary(
    store_ranking: pd.DataFrame,
    theme_impact: pd.DataFrame,
) -> pd.DataFrame:
    """
    Size incremental revenue from a priority-store initiative.

    estimated_incremental_revenue =
        target_store_count * avg_daily_transactions * avg_ticket
        * improvement_window_days * expected_repeat_visit_lift
    """
    defaults = IMPACT_DEFAULTS
    target_n = defaults["target_store_count"]
    window_days = defaults["improvement_window_days"]
    visit_lift = defaults["expected_repeat_visit_lift"]

    targets = store_ranking.head(target_n)
    avg_txn = float(targets["avg_daily_transactions"].mean())
    avg_ticket = float(targets["avg_ticket"].mean())

    estimated_revenue = target_n * avg_txn * avg_ticket * window_days * visit_lift

    top_theme = theme_impact.sort_values("impact_rank").iloc[0]["primary_theme"]
    initiative = f"Priority-store {top_theme.replace('_', ' ')} improvement pilot"
    action = THEME_RECOMMENDED_ACTIONS.get(top_theme, THEME_RECOMMENDED_ACTIONS["general_experience"])

    assumptions = (
        f"Top {target_n} stores from store_opportunity_ranking.csv; "
        f"mean daily transactions {avg_txn:,.1f}; mean ticket ${avg_ticket:.2f}; "
        f"{window_days}-day window; {visit_lift:.1%} repeat-visit lift. {action}"
    )
    measurement_plan = (
        "Track weekly NPS, CSAT, revisit intent, and repeat visit rate in pilot stores "
        f"vs matched control stores over {window_days} days; reconcile against POS transaction counts."
    )

    return pd.DataFrame(
        [
            {
                "initiative": initiative,
                "target_store_count": target_n,
                "avg_daily_transactions": round(avg_txn, 2),
                "avg_ticket": round(avg_ticket, 2),
                "improvement_window_days": window_days,
                "expected_repeat_visit_lift": visit_lift,
                "estimated_incremental_revenue": round(estimated_revenue, 2),
                "assumptions": assumptions,
                "measurement_plan": measurement_plan,
            }
        ]
    )


def estimate_theme_impact(theme_impact: pd.DataFrame, stores: pd.DataFrame, surveys: pd.DataFrame) -> dict:
    """Backward-compatible summary dict for dashboard and tests."""
    brand_nps = standard_nps(surveys["nps"])
    top_theme = theme_impact.sort_values("impact_rank").iloc[0]
    theme_name = top_theme["primary_theme"]

    ranking_path = OUTPUT_TABLES / "store_opportunity_ranking.csv"
    summary_path = OUTPUT_TABLES / "impact_summary.csv"
    if summary_path.exists():
        summary = pd.read_csv(summary_path)
        estimated = float(summary.iloc[0]["estimated_incremental_revenue"])
        target_n = int(summary.iloc[0]["target_store_count"])
    elif ranking_path.exists():
        summary_df = build_impact_summary(pd.read_csv(ranking_path), theme_impact)
        estimated = float(summary_df.iloc[0]["estimated_incremental_revenue"])
        target_n = int(summary_df.iloc[0]["target_store_count"])
    else:
        estimated = 0.0
        target_n = IMPACT_DEFAULTS["target_store_count"]

    return {
        "brand_nps_baseline": brand_nps,
        "recommended_focus_theme": theme_name,
        "target_store_count": target_n,
        "estimated_incremental_revenue_usd": estimated,
        "meets_100k_threshold": estimated >= IMPACT_DEFAULTS["min_incremental_revenue_usd"],
        "net_annual_impact_usd": round(estimated, 2),
    }


def build_executive_recommendation(impact: dict) -> str:
    theme = impact["recommended_focus_theme"].replace("_", " ").title()
    return (
        f"## Primary Recommendation\n\n"
        f"Prioritize **{theme}** across **{impact['target_store_count']} priority stores**.\n\n"
        f"- Estimated incremental revenue: **${impact['estimated_incremental_revenue_usd']:,.0f}**\n"
        f"- **Meets $100K threshold: {impact['meets_100k_threshold']}**\n"
    )


def main() -> None:
    OUTPUT_TABLES.mkdir(parents=True, exist_ok=True)
    surveys = pd.read_parquet(PROCESSED_DIR / "guest_surveys_classified.parquet")
    stores = pd.read_parquet(PROCESSED_DIR / "stores_clean.parquet")
    theme_impact = pd.read_csv(OUTPUT_TABLES / "theme_impact.csv")
    store_ranking = pd.read_csv(OUTPUT_TABLES / "store_opportunity_ranking.csv")

    summary = build_impact_summary(store_ranking, theme_impact)
    summary.to_csv(OUTPUT_TABLES / "impact_summary.csv", index=False)

    impact = estimate_theme_impact(theme_impact, stores, surveys)
    (OUTPUT_TABLES / "impact_sizing.json").write_text(json.dumps(impact, indent=2))
    (OUTPUT_TABLES / "executive_recommendation_snippet.md").write_text(build_executive_recommendation(impact))

    row = summary.iloc[0]
    print(f"Impact summary: ${row['estimated_incremental_revenue']:,.0f} incremental revenue")
    print(f"$100K+ threshold: {impact['meets_100k_threshold']}")


if __name__ == "__main__":
    main()
