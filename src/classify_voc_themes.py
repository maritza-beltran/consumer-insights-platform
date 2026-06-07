"""Classify Voice of Customer themes from guest comment text."""

from __future__ import annotations

import re

import pandas as pd

from config import PROCESSED_DIR, THEME_KEYWORDS, VOC_THEMES


def _theme_score(comment: str, theme: str) -> int:
    text = comment.lower()
    return sum(1 for kw in THEME_KEYWORDS[theme] if kw in text)


def match_themes(comment: str) -> list[str]:
    """Return primary theme and optional secondary theme (max 2)."""
    scores = {theme: _theme_score(comment, theme) for theme in VOC_THEMES}
    ranked = sorted(scores.items(), key=lambda x: (-x[1], VOC_THEMES.index(x[0])))
    if ranked[0][1] == 0:
        return ["general_experience"]
    matched = [ranked[0][0]]
    if ranked[1][1] > 0 and ranked[1][0] != matched[0]:
        matched.append(ranked[1][0])
    return matched


def classify_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    classified = df.copy()
    classified["themes"] = classified["comment_text"].apply(match_themes)
    classified["primary_theme"] = classified["themes"].apply(lambda t: t[0])
    classified["secondary_theme"] = classified["themes"].apply(lambda t: t[1] if len(t) > 1 else "")
    classified["theme_count"] = classified["themes"].apply(len)
    return classified


def main() -> None:
    enriched = pd.read_parquet(PROCESSED_DIR / "guest_surveys_enriched.parquet")
    classified = classify_dataframe(enriched)
    out_path = PROCESSED_DIR / "guest_surveys_classified.parquet"
    classified.to_parquet(out_path, index=False)
    print(f"Classified {len(classified)} surveys -> {out_path}")
    print(f"Primary themes: {classified['primary_theme'].nunique()}")


if __name__ == "__main__":
    main()
