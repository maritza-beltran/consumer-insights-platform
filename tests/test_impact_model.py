"""Tests for impact sizing model."""

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from impact_model import estimate_theme_impact


def test_estimate_theme_impact_structure():
    theme_impact = pd.DataFrame(
        {
            "theme": ["wait_time"],
            "mention_count": [500],
            "avg_nps": [4.5],
            "nps_gap_vs_brand": [-3.0],
            "detractor_rate": [0.45],
        }
    )
    stores = pd.DataFrame(
        {
            "store_id": ["BB-001"],
            "monthly_transactions": [15000],
            "avg_ticket_usd": [9.0],
        }
    )
    surveys = pd.DataFrame({"nps_score": [7, 8, 5, 9, 6, 4, 10, 3]})

    impact = estimate_theme_impact(theme_impact, stores, surveys)
    assert "net_annual_impact_usd" in impact
    assert "recommended_focus_theme" in impact
    assert impact["recommended_focus_theme"] == "wait_time"
    assert isinstance(impact["meets_100k_threshold"], bool)
