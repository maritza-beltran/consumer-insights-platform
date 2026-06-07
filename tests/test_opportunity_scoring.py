"""Tests for store opportunity scoring."""

import pandas as pd

from opportunity_scoring import store_opportunity_ranking


def _sample_stores() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "store_id": ["BB-001", "BB-002"],
            "store_name": ["High Traffic Mall", "Low Traffic Urban"],
            "market": ["Hartford", "Boston"],
            "region": ["Northeast", "Northeast"],
            "store_type": ["mall", "urban"],
            "avg_daily_transactions": [900, 300],
            "avg_ticket": [9.0, 8.0],
            "data_source": ["synthetic", "synthetic"],
        }
    )


def _sample_surveys() -> pd.DataFrame:
    rows = []
    for store_id, store_name, nps_vals, revisit_vals, themes in [
        ("BB-001", "High Traffic Mall", [3, 4, 5], [2, 2, 3], ["speed_of_service"] * 3),
        ("BB-002", "Low Traffic Urban", [8, 9, 9], [4, 5, 5], ["rewards_value"] * 3),
    ]:
        for i, (nps, revisit, theme) in enumerate(zip(nps_vals, revisit_vals, themes)):
            rows.append(
                {
                    "survey_id": f"SVY-{store_id}-{i}",
                    "store_id": store_id,
                    "store_name": store_name,
                    "market": "Test",
                    "region": "Northeast",
                    "store_type": "mall" if store_id == "BB-001" else "urban",
                    "nps": nps,
                    "csat": 3 if nps <= 6 else 4,
                    "revisit_intent": revisit,
                    "comment_text": "Wait was too long." if theme == "speed_of_service" else "Great rewards.",
                    "primary_theme": theme,
                    "is_negative_experience": theme == "speed_of_service",
                    "sentiment_label": "negative" if theme == "speed_of_service" else "positive",
                }
            )
    return pd.DataFrame(rows)


def test_opportunity_scores_bounded_zero_one():
    ranking = store_opportunity_ranking(_sample_surveys(), _sample_stores())
    assert ranking["opportunity_score"].between(0, 1).all()
    assert ranking["traffic_weight"].between(0, 1).all()


def test_high_traffic_negative_store_ranks_above_low_traffic_positive():
    ranking = store_opportunity_ranking(_sample_surveys(), _sample_stores())
    mall = ranking.loc[ranking["store_id"] == "BB-001", "opportunity_score"].iloc[0]
    urban = ranking.loc[ranking["store_id"] == "BB-002", "opportunity_score"].iloc[0]
    assert mall > urban
