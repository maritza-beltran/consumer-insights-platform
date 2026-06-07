"""Classify Voice of Customer themes from guest comment text."""

from __future__ import annotations

import re

import pandas as pd

from config import PROCESSED_DIR, THEME_KEYWORDS

POSITIVE_CUES = ["warm", "easy", "valued", "creative", "balanced", "fresh", "tidy", "accurate", "solid"]
NEGATIVE_CUES = [
    "slow", "burnt", "stale", "weak", "sticky", "messy", "crashed", "wrong",
    "expensive", "rushed", "disorganized", "never posted", "repetitive",
]


def match_themes(comment: str) -> list[str]:
    text = comment.lower()
    matched = []
    for theme, keywords in THEME_KEYWORDS.items():
        if any(re.search(rf"\b{re.escape(kw)}\b", text) for kw in keywords):
            matched.append(theme)
    return matched or ["general_experience"]


def classify_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    classified = df.copy()
    classified["themes"] = classified["comment_text"].apply(match_themes)
    classified["primary_theme"] = classified["themes"].apply(lambda t: t[0])
    classified["theme_count"] = classified["themes"].apply(len)
    return classified


def main() -> None:
    enriched = pd.read_parquet(PROCESSED_DIR / "guest_surveys_enriched.parquet")
    classified = classify_dataframe(enriched)
    out_path = PROCESSED_DIR / "guest_surveys_classified.parquet"
    classified.to_parquet(out_path, index=False)
    print(f"Classified {len(classified)} surveys -> {out_path}")
    print(f"Unique primary themes: {classified['primary_theme'].nunique()}")


if __name__ == "__main__":
    main()
