"""Tests for impact sizing model."""

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from impact_model import estimate_theme_impact


def test_estimate_theme_impact_structure():
    theme_impact = pd.DataFrame(
        {
            "primary_theme": ["wait_time"],
            "theme_avg_nps": [4.5],
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
    surveys = pd.DataFrame({"nps": [7, 8, 5, 9, 6, 4, 10, 3]})
    impact = estimate_theme_impact(theme_impact, stores, surveys)
    assert "net_annual_impact_usd" in impact
    assert impact["recommended_focus_theme"] == "wait_time"
    assert impact["pilot_scope"] == "top_tertile_opportunity_stores"
    assert isinstance(impact["meets_100k_threshold"], bool)
