"""Tests for VoC theme classification."""

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from classify_voc_themes import _comment_sentiment, _match_themes, classify_dataframe


def test_match_themes_detects_wait_time():
    comment = "Waited 12 minutes for a drink that should take five."
    themes = _match_themes(comment)
    assert "wait_time" in themes


def test_match_themes_fallback_general():
    themes = _match_themes("Okay.")
    assert themes == ["general_experience"]


def test_comment_sentiment_negative():
    comment = "App crashed while I tried to customize my drink."
    assert _comment_sentiment(comment) == "negative"


def test_classify_dataframe_columns():
    df = pd.DataFrame(
        {
            "survey_id": ["SVY-001"],
            "comment_text": ["Barista was warm and remembered my usual order."],
            "nps_score": [9],
            "csat_score": [5],
            "revisit_intent": [5],
        }
    )
    result = classify_dataframe(df)
    assert "primary_theme" in result.columns
    assert "nps_category" in result.columns
    assert result.iloc[0]["comment_sentiment"] == "positive"
