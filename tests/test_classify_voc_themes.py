"""Tests for VoC theme classification."""

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from classify_voc_themes import classify_dataframe, match_themes


def test_match_themes_detects_wait_time():
    comment = "Waited 12 minutes for a drink that should take five."
    assert "wait_time" in match_themes(comment)


def test_match_themes_fallback_general():
    assert match_themes("Okay.") == ["general_experience"]


def test_classify_dataframe_columns():
    df = pd.DataFrame(
        {
            "survey_id": ["SVY-001"],
            "comment_text": ["Barista was warm and remembered my usual order."],
            "nps": [9],
            "csat": [5],
            "revisit_intent": [5],
            "sentiment_label": ["positive"],
        }
    )
    result = classify_dataframe(df)
    assert "primary_theme" in result.columns
    assert result.iloc[0]["primary_theme"] == "staff_friendliness"
