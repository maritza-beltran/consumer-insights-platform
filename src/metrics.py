"""Shared metric helpers for Brew & Bloom analytics."""

from __future__ import annotations

import pandas as pd


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
