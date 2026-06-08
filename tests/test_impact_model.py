"""Tests for impact sizing model."""

import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from impact_model import (
    build_impact_sensitivity,
    build_impact_summary,
    calculate_incremental_revenue,
    estimate_theme_impact,
)


def test_calculate_incremental_revenue_exact_formula():
    revenue = calculate_incremental_revenue(
        target_store_count=20,
        avg_daily_transactions=500,
        avg_ticket=10,
        window_days=90,
        visit_lift=0.01,
    )
    assert revenue == pytest.approx(90_000, rel=1e-6)


def test_build_impact_summary_exceeds_100k():
    store_ranking = pd.DataFrame(
        {
            "avg_daily_transactions": [400] * 30,
            "avg_ticket": [8.0] * 30,
            "opportunity_score": [0.8] * 30,
        }
    )
    theme_impact = pd.DataFrame(
        {"primary_theme": ["speed_of_service"], "impact_rank": [1]}
    )
    summary = build_impact_summary(store_ranking, theme_impact)
    expected = calculate_incremental_revenue(30, 400, 8.0, 90, 0.02)
    assert summary.iloc[0]["estimated_incremental_revenue"] == pytest.approx(expected, rel=1e-6)
    assert summary.iloc[0]["estimated_incremental_revenue"] >= 100_000
    assert summary.iloc[0]["target_store_count"] == 30

def test_build_impact_sensitivity_creates_scenarios():
    store_ranking = pd.DataFrame(
        {
            "avg_daily_transactions": [500] * 30,
            "avg_ticket": [10.0] * 30
        }
    )
    sensitivity = build_impact_sensitivity(
        store_ranking,
        target_store_counts=(10, 30),
        visit_lifts=(.01, .02),
        window_days=90,
    )
    assert len(sensitivity) == 4
    base = sensitivity[
        (sensitivity["target_store_count"] == 30)
        & (sensitivity["expected_repeat_visit_lift"] == .02)
        ].iloc[0]
    assert base["estimated_incremental_revenue"] == pytest.approx(270_000)
    assert bool(base["meets_100k_threshold"]) is True


def test_estimate_theme_impact_structure():
    theme_impact = pd.DataFrame(
        {
            "primary_theme": ["speed_of_service"],
            "theme_avg_nps": [-20.0],
            "theme_nps_gap": [-3.0],
            "impact_rank": [1],
        }
    )
    stores = pd.DataFrame(
        {
            "store_id": ["BB-001"],
            "avg_daily_transactions": [500],
            "avg_ticket": [9.0],
        }
    )
    surveys = pd.DataFrame({"nps": [10, 10, 3, 3, 9, 4, 10, 2]})
    store_ranking = pd.DataFrame(
        {"avg_daily_transactions": [400] * 30, "avg_ticket": [8.0] * 30, "opportunity_score": [0.7] * 30}
    )
    summary = build_impact_summary(store_ranking, theme_impact)
    impact = estimate_theme_impact(theme_impact, stores, surveys)
    assert "estimated_incremental_revenue_usd" in impact
    assert impact["recommended_focus_theme"] == "speed_of_service"
    revenue = summary.iloc[0]["estimated_incremental_revenue"]
    assert impact["meets_100k_threshold"] == (revenue >= 100_000)
