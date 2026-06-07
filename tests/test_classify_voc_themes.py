"""Tests for VoC theme classification."""

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from classify_voc_themes import classify_dataframe, match_themes


def test_match_themes_detects_speed_of_service():
    comment = "The line took forever even though there were only three people ahead of me."
    themes = match_themes(comment)
    assert "speed_of_service" in themes


def test_match_themes_detects_mobile_app_issues():
    comment = "Mobile ordering was easy, but my drink was not ready when I arrived."
    themes = match_themes(comment)
    assert themes[0] == "mobile_app_issues"


def test_match_themes_primary_and_secondary():
    comment = "The latte tasted different than usual, and the line took forever."
    themes = match_themes(comment)
    assert len(themes) == 2
    assert "drink_consistency" in themes
    assert "speed_of_service" in themes


def test_match_themes_fallback_general():
    assert match_themes("Okay.") == ["general_experience"]


def test_classify_dataframe_columns():
    df = pd.DataFrame(
        {
            "survey_id": ["SVY-001"],
            "comment_text": ["The staff was friendly even though the drive-thru was backed up."],
            "nps": [9],
            "csat": [5],
            "revisit_intent": [5],
            "sentiment_label": ["positive"],
        }
    )
    result = classify_dataframe(df)
    assert "primary_theme" in result.columns
    assert "secondary_theme" in result.columns
    assert result.iloc[0]["primary_theme"] in {"staff_friendliness", "drive_thru_experience", "speed_of_service"}
