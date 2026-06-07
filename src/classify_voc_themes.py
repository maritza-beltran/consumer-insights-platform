"""Rule-based VoC theme classification from guest comment text."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from config import PROCESSED_DIR, THEME_KEYWORDS, VOC_THEMES

# ---------------------------------------------------------------------------
# Keyword dictionaries (rule-based classifier — no ML / paid APIs)
# ---------------------------------------------------------------------------
# Themes and keywords are defined in config.THEME_KEYWORDS.
# Matching is case-insensitive substring search; longer phrases are preferred
# because they are listed explicitly in the dictionary.

NEGATIVE_EXPERIENCE_CUES = [
    "wrong", "slow", "forever", "burnt", "stale", "weak", "confusing",
    "expensive", "high for the size", "not ready", "crashed", "sticky",
    "messy", "rushed", "not as valuable", "inconsistent", "disorganized",
    "too sweet", "ignored", "overflowing", "hard to hear", "off",
]

POSITIVE_EXPERIENCE_CUES = [
    "friendly", "helpful", "clean", "accurate", "easy", "smooth",
    "valued", "good deal", "well balanced", "on time", "remembered",
    "creative", "solid", "tidy", "fresh",
]

FALLBACK_THEME = "general_experience"


@dataclass
class ThemeClassification:
    """Structured output for a single comment classification."""

    primary_theme: str
    secondary_theme: str
    theme_confidence: float
    is_negative_experience: bool
    themes: list[str]


def _normalize_text(comment: str) -> str:
    return re.sub(r"\s+", " ", comment.strip().lower())


def _keyword_hits(text: str, keywords: list[str]) -> int:
    """Count how many theme keywords appear in the comment."""
    return sum(1 for kw in keywords if kw in text)


def _score_themes(text: str) -> dict[str, int]:
    """Score every VoC theme by keyword hit count."""
    return {theme: _keyword_hits(text, THEME_KEYWORDS[theme]) for theme in VOC_THEMES}


def _compute_confidence(primary_score: int, secondary_score: int) -> float:
    """
    Map keyword hits to a 0–1 confidence score.

    - 0 hits on primary → 0.35 (fallback/general)
    - 1 hit → 0.60
    - 2+ hits → 0.75–0.95 depending on secondary support
    """
    if primary_score <= 0:
        return 0.35
    base = min(0.75 + 0.1 * (primary_score - 1), 0.9)
    if secondary_score > 0:
        base = min(base + 0.05, 0.95)
    return round(base, 3)


def _is_negative_experience(text: str, sentiment_label: str) -> bool:
    """
    Flag comments that describe a negative guest experience.

    Uses sentiment label when available, otherwise compares negative vs
    positive language cues in the comment text.
    """
    if sentiment_label == "negative":
        return True
    if sentiment_label == "positive":
        return False
    neg = sum(1 for cue in NEGATIVE_EXPERIENCE_CUES if cue in text)
    pos = sum(1 for cue in POSITIVE_EXPERIENCE_CUES if cue in text)
    return neg > pos


def classify_comment(comment: str, sentiment_label: str = "neutral") -> ThemeClassification:
    """
    Classify one comment into primary/secondary themes with confidence.

    Rules:
    1. Score each theme by keyword hits.
    2. Rank themes by score (ties broken by VOC_THEMES order).
    3. Assign primary = top theme; secondary = runner-up if score > 0.
    4. If no keywords match, assign general_experience fallback.
    """
    text = _normalize_text(comment)
    scores = _score_themes(text)
    ranked = sorted(scores.items(), key=lambda x: (-x[1], VOC_THEMES.index(x[0])))

    primary, primary_score = ranked[0]
    secondary, secondary_score = ranked[1] if len(ranked) > 1 else ("", 0)

    if primary_score == 0:
        primary = FALLBACK_THEME
        secondary = ""
        themes = [FALLBACK_THEME]
        confidence = _compute_confidence(0, 0)
    else:
        themes = [primary]
        if secondary_score > 0 and secondary != primary:
            themes.append(secondary)
        else:
            secondary = ""
        confidence = _compute_confidence(primary_score, secondary_score)

    return ThemeClassification(
        primary_theme=primary,
        secondary_theme=secondary,
        theme_confidence=confidence,
        is_negative_experience=_is_negative_experience(text, sentiment_label),
        themes=themes,
    )


def match_themes(comment: str) -> list[str]:
    """Backward-compatible helper returning [primary, secondary?]."""
    return classify_comment(comment).themes


def classify_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Apply rule-based classification to a survey/comment dataframe."""
    classified = df.copy()
    results = classified.apply(
        lambda row: classify_comment(
            str(row.get("comment_text", "")),
            str(row.get("sentiment_label", "neutral")),
        ),
        axis=1,
    )
    classified["primary_theme"] = results.apply(lambda r: r.primary_theme)
    classified["secondary_theme"] = results.apply(lambda r: r.secondary_theme)
    classified["theme_confidence"] = results.apply(lambda r: r.theme_confidence)
    classified["is_negative_experience"] = results.apply(lambda r: r.is_negative_experience)
    classified["themes"] = results.apply(lambda r: r.themes)
    classified["theme_count"] = classified["themes"].apply(len)
    return classified


def classify_and_save(
    input_path: Path | None = None,
    output_path: Path | None = None,
) -> pd.DataFrame:
    """Load enriched surveys, classify themes, and save parquet."""
    input_path = input_path or PROCESSED_DIR / "guest_surveys_enriched.parquet"
    output_path = output_path or PROCESSED_DIR / "guest_surveys_classified.parquet"
    enriched = pd.read_parquet(input_path)
    classified = classify_dataframe(enriched)
    classified.to_parquet(output_path, index=False)
    return classified


def main() -> None:
    classified = classify_and_save()
    print(f"Classified {len(classified):,} surveys")
    print(f"Primary themes: {classified['primary_theme'].nunique()}")
    print(f"Negative experience share: {classified['is_negative_experience'].mean():.1%}")


if __name__ == "__main__":
    main()
