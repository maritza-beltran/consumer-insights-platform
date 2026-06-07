"""Classify Voice of Customer themes from guest comment text."""

from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
PROCESSED_DIR = ROOT / "data" / "processed"

THEME_KEYWORDS: dict[str, list[str]] = {
    "speed_of_service": [
        "slow", "line", "rush", "waited", "delay", "long line", "peak hour",
    ],
    "product_quality": [
        "espresso", "burnt", "stale", "weak", "cold brew", "pastry", "taste", "milk",
    ],
    "cleanliness": [
        "sticky", "restroom", "messy", "trash", "dirty", "clean", "floor",
    ],
    "staff_friendliness": [
        "barista", "staff", "greet", "friendly", "warm", "apologized", "team",
    ],
    "value_for_money": [
        "price", "deal", "discount", "value", "expensive", "loyalty rewards",
    ],
    "ambiance": [
        "music", "seating", "lighting", "cozy", "loud", "ambiance", "space",
    ],
    "mobile_app": [
        "app", "mobile order", "pickup", "notification", "crashed", "customize",
    ],
    "loyalty_program": [
        "points", "tier", "reward", "redeem", "birthday", "member",
    ],
    "menu_variety": [
        "menu", "dairy-free", "seasonal", "food menu", "options", "variety",
    ],
    "wait_time": [
        "minutes", "wait", "staffing", "pickup shelf", "handoff", "volume",
    ],
}

POSITIVE_CUES = [
    "helpful", "warm", "cozy", "good deal", "valued", "creative", "reasonable",
    "remembered", "sincerely", "timely", "well executed", "inviting",
]
NEGATIVE_CUES = [
    "too slow", "burnt", "stale", "weak", "sticky", "messy", "overflowing",
    "rushed", "high", "loud", "harsh", "crashed", "confusing", "never posted",
    "unclear", "limited", "repetitive", "insufficient", "disorganized", "late",
]


def _match_themes(comment: str) -> list[str]:
    text = comment.lower()
    matched = []
    for theme, keywords in THEME_KEYWORDS.items():
        if any(re.search(rf"\b{re.escape(kw)}\b", text) for kw in keywords):
            matched.append(theme)
    return matched or ["general_experience"]


def _comment_sentiment(comment: str) -> str:
    text = comment.lower()
    pos = sum(1 for cue in POSITIVE_CUES if cue in text)
    neg = sum(1 for cue in NEGATIVE_CUES if cue in text)
    if pos > neg:
        return "positive"
    if neg > pos:
        return "negative"
    return "neutral"


def classify_dataframe(surveys: pd.DataFrame) -> pd.DataFrame:
    classified = surveys.copy()
    classified["themes"] = classified["comment_text"].apply(_match_themes)
    classified["primary_theme"] = classified["themes"].apply(lambda t: t[0])
    classified["theme_count"] = classified["themes"].apply(len)
    classified["comment_sentiment"] = classified["comment_text"].apply(_comment_sentiment)
    classified["nps_category"] = pd.cut(
        classified["nps_score"],
        bins=[-1, 6, 8, 10],
        labels=["detractor", "passive", "promoter"],
    )
    return classified


def main() -> None:
    surveys = pd.read_parquet(PROCESSED_DIR / "guest_surveys_clean.parquet")
    classified = classify_dataframe(surveys)
    out_path = PROCESSED_DIR / "guest_surveys_classified.parquet"
    classified.to_parquet(out_path, index=False)
    print(f"Classified {len(classified)} surveys -> {out_path}")
    print(f"Unique primary themes: {classified['primary_theme'].nunique()}")


if __name__ == "__main__":
    main()
