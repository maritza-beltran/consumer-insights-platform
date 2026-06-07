"""Tests for VoC theme classification."""

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from classify_voc_themes import classify_comment, classify_dataframe, match_themes


def test_match_themes_detects_speed_of_service():
    comment = "The line took forever even though there were only three people ahead of me."
    themes = match_themes(comment)
    assert "speed_of_service" in themes


def test_match_themes_detects_mobile_app_issues():
    comment = "Mobile ordering was easy, but my drink was not ready when I arrived."
    result = classify_comment(comment, "negative")
    assert result.primary_theme == "mobile_app_issues"
    assert result.is_negative_experience is True


def test_match_themes_primary_and_secondary():
    comment = "The latte tasted different than usual, and the line took forever."
    result = classify_comment(comment)
    assert len(result.themes) == 2
    assert "drink_consistency" in result.themes
    assert "speed_of_service" in result.themes
    assert result.theme_confidence >= 0.6


def test_match_themes_fallback_general():
    result = classify_comment("Okay.")
    assert result.primary_theme == "general_experience"
    assert result.theme_confidence == 0.35


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
    for col in ["primary_theme", "secondary_theme", "theme_confidence", "is_negative_experience"]:
        assert col in result.columns
    assert 0 <= result.iloc[0]["theme_confidence"] <= 1
