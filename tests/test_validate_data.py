"""Tests for data validation logic."""

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from validate_data import validate_surveys


def _sample_surveys() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "survey_id": ["SVY-001", "SVY-002"],
            "guest_id": ["GST-A", "GST-B"],
            "survey_date": ["2024-06-01", "2024-06-02"],
            "store_id": ["BB-001", "BB-001"],
            "region": ["West", "West"],
            "store_type": ["urban flagship", "urban flagship"],
            "channel": ["in-store", "drive-thru"],
            "segment": ["loyalist", "at_risk"],
            "nps_score": [10, 3],
            "csat_score": [5, 2],
            "revisit_intent": [5, 1],
            "comment_text": ["Great visit.", "Long wait today."],
            "data_source": ["synthetic", "synthetic"],
        }
    )


def _sample_stores() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "store_id": ["BB-001"],
            "store_name": ["Test Store"],
            "region": ["West"],
            "store_type": ["urban flagship"],
            "monthly_transactions": [10000],
            "avg_ticket_usd": [8.5],
            "opened_year": [2020],
        }
    )


def test_validate_surveys_passes_clean_data():
    report = validate_surveys(_sample_surveys(), _sample_stores())
    assert report["status"] == "pass"
    assert report["record_counts"]["surveys"] == 2


def test_validate_surveys_fails_invalid_nps():
    surveys = _sample_surveys()
    surveys.loc[0, "nps_score"] = 11
    report = validate_surveys(surveys, _sample_stores())
    assert report["status"] == "fail"
    assert any("nps_score" in issue for issue in report["issues"])
