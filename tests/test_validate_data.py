"""Tests for data validation logic."""

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from validate_data import validate_all


def _sample_surveys() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "survey_id": ["SVY-001", "SVY-002"],
            "guest_id": ["GST-001", "GST-002"],
            "store_id": ["BB-001", "BB-001"],
            "survey_date": ["2024-06-01", "2024-06-02"],
            "guest_segment": ["loyalty_regular", "at_risk_guest"],
            "visit_channel": ["in_store", "drive_thru"],
            "nps": [10, 3],
            "csat": [5, 2],
            "revisit_intent": [5, 1],
            "wait_time_rating": [5, 2],
            "drink_quality_rating": [5, 2],
            "order_accuracy_rating": [5, 2],
            "staff_friendliness_rating": [5, 2],
            "cleanliness_rating": [5, 2],
            "mobile_app_experience_rating": [4, 2],
            "rewards_satisfaction": [5, 2],
            "price_value_perception": [4, 2],
            "data_source": ["synthetic", "synthetic"],
        }
    )


def _sample_stores() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "store_id": ["BB-001"],
            "store_name": ["Test Store"],
            "market": ["Seattle"],
            "region": ["West"],
            "store_type": ["urban"],
            "franchise_corporate_flag": ["corporate"],
            "avg_daily_transactions": [500],
            "avg_ticket": [8.5],
            "digital_order_share": [0.4],
            "drive_thru_flag": [1],
            "open_date": ["2020-01-01"],
            "data_source": ["synthetic"],
        }
    )


def _sample_comments() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "comment_id": ["CMT-001"],
            "survey_id": ["SVY-001"],
            "guest_id": ["GST-001"],
            "store_id": ["BB-001"],
            "comment_date": ["2024-06-01"],
            "guest_segment": ["loyalty_regular"],
            "visit_channel": ["in_store"],
            "comment_text": ["Great visit."],
            "star_rating": [5],
            "sentiment_label": ["positive"],
            "data_source": ["synthetic"],
        }
    )


def _sample_product() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "feedback_id": ["PFD-001"],
            "survey_id": ["SVY-001"],
            "guest_id": ["GST-001"],
            "store_id": ["BB-001"],
            "feedback_date": ["2024-06-01"],
            "product_name": ["Classic Latte"],
            "product_category": ["espresso"],
            "seasonal_flag": [0],
            "seasonal_drink_awareness": [0],
            "trial_flag": [1],
            "product_rating": [5],
            "repeat_purchase_intent": [5],
            "sweetness_feedback": ["balanced"],
            "price_value_feedback": ["good_value"],
            "guest_segment": ["loyalty_regular"],
            "data_source": ["synthetic"],
        }
    )


def _sample_loyalty() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "guest_id": ["GST-001", "GST-002"],
            "loyalty_member_flag": [1, 0],
            "visit_frequency_30d": [5, 1],
            "days_since_last_visit": [3, 20],
            "promo_exposure_flag": [1, 0],
            "promo_redeemed_flag": [1, 0],
            "mobile_order_usage_rate": [0.5, 0.2],
            "rewards_redemption_count": [2, 0],
            "churn_risk_proxy": [0.1, 0.6],
            "data_source": ["synthetic", "synthetic"],
        }
    )


def test_validate_all_passes_clean_data():
    report = validate_all(
        _sample_stores(),
        _sample_surveys(),
        _sample_comments(),
        _sample_product(),
        _sample_loyalty(),
    )
    assert report["status"] == "pass"


def test_validate_all_fails_invalid_nps():
    surveys = _sample_surveys()
    surveys.loc[0, "nps"] = 11
    report = validate_all(
        _sample_stores(),
        surveys,
        _sample_comments(),
        _sample_product(),
        _sample_loyalty(),
    )
    assert report["status"] == "fail"
