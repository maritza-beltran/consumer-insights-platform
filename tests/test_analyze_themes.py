"""Tests for multi-factor theme prioritization."""

import pandas as pd

from analyze_themes import theme_impact, theme_summary


def _synthetic_classified_surveys() -> pd.DataFrame:
    """High-volume low-damage theme vs low-volume high-damage theme."""
    rows = []
    for i in range(20):
        rows.append(
            {
                "survey_id": f"SVY-VOL-{i}",
                "nps": 7,
                "csat": 3,
                "revisit_intent": 3,
                "comment_text": f"Line took forever visit {i}",
                "primary_theme": "speed_of_service",
                "is_negative_experience": True,
            }
        )
    for i in range(3):
        rows.append(
            {
                "survey_id": f"SVY-DMG-{i}",
                "nps": 2,
                "csat": 1,
                "revisit_intent": 1,
                "comment_text": f"Price feels high for the size visit {i}",
                "primary_theme": "price_value",
                "is_negative_experience": True,
            }
        )
    return pd.DataFrame(rows)


def test_theme_priority_not_volume_alone():
    df = _synthetic_classified_surveys()
    summary = theme_summary(df)
    impact = theme_impact(df, summary=summary)

    vol_leader = summary.sort_values("comment_count", ascending=False).iloc[0]["primary_theme"]
    priority_leader = impact.sort_values("impact_rank").iloc[0]["primary_theme"]

    assert vol_leader == "speed_of_service"
    assert priority_leader == "price_value"
    assert impact["priority_score"].between(0, 1).all()
