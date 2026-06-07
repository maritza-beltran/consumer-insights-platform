"""Shared metric helpers for Brew & Bloom analytics."""

from __future__ import annotations

import pandas as pd

# Theme priority weights — frequency alone must not dominate intervention ranking.
THEME_PRIORITY_WEIGHTS = {
    "frequency": 0.15,
    "negative_sentiment": 0.25,
    "nps_drag": 0.25,
    "csat_drag": 0.15,
    "revisit_drag": 0.20,
}


def standard_nps(scores: pd.Series) -> float:
    """NPS = (% promoters with nps >= 9 - % detractors with nps <= 6) * 100."""
    if scores.empty:
        return 0.0
    promoters = (scores >= 9).mean()
    detractors = (scores <= 6).mean()
    return round((promoters - detractors) * 100, 1)


def minmax_index(series: pd.Series) -> pd.Series:
    """Normalize a series to 0–1; constant series returns 0.5."""
    lo = float(series.min())
    hi = float(series.max())
    if hi == lo:
        return pd.Series(0.5, index=series.index)
    return (series - lo) / (hi - lo)


def theme_priority_score(
    share_of_comments: pd.Series,
    negative_share: pd.Series,
    theme_nps_gap: pd.Series,
    theme_csat_gap: pd.Series,
    theme_revisit_gap: pd.Series,
) -> pd.Series:
    """
    Composite theme priority score (0–1).

    Combines comment frequency, negative sentiment, and satisfaction gaps below
    brand baseline. High volume alone cannot dominate the ranking.
    """
    w = THEME_PRIORITY_WEIGHTS
    freq = minmax_index(share_of_comments)
    neg = minmax_index(negative_share)
    nps_drag = minmax_index((-theme_nps_gap).clip(lower=0))
    csat_drag = minmax_index((-theme_csat_gap).clip(lower=0))
    revisit_drag = minmax_index((-theme_revisit_gap).clip(lower=0))
    return (
        w["frequency"] * freq
        + w["negative_sentiment"] * neg
        + w["nps_drag"] * nps_drag
        + w["csat_drag"] * csat_drag
        + w["revisit_drag"] * revisit_drag
    ).round(4)
