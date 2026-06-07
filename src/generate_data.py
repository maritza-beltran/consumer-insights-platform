"""Generate synthetic multi-dataset guest insights data for Brew & Bloom Coffee Co."""

from __future__ import annotations

import json
from datetime import datetime, timedelta

import numpy as np
import pandas as pd
from faker import Faker

from config import (
    BRAND_NAME,
    CHANNELS,
    DATA_SOURCE,
    N_STORES,
    N_SURVEYS,
    PRODUCTS,
    RAW_DIR,
    REGIONS,
    RANDOM_SEED,
    ROOT,
    SEGMENTS,
    SENTIMENTS,
    STORE_TYPES,
)

DATA_START = datetime(2024, 1, 1)
DATA_END = datetime(2024, 6, 30)

COMMENT_TEMPLATES = {
    "wait_time": [
        "Waited 12 minutes for a drink that should take five.",
        "Drive-thru line moved too slowly during the morning rush.",
        "Mobile order pickup shelf was disorganized and delayed handoff.",
    ],
    "drink_quality": [
        "My espresso tasted burnt and the milk was overheated.",
        "The cold brew was weaker than at other locations.",
        "Seasonal latte was creative and well balanced.",
    ],
    "order_accuracy": [
        "Received the wrong drink customization twice this week.",
        "Order was accurate and the barista confirmed my preferences.",
    ],
    "staff_friendliness": [
        "Barista was warm and remembered my usual order.",
        "Team felt rushed and did not greet guests at the counter.",
    ],
    "cleanliness": [
        "Tables were sticky and the restroom needed attention.",
        "Store felt tidy even during peak afternoon traffic.",
    ],
    "mobile_app": [
        "App crashed while I tried to customize my drink.",
        "Mobile order notifications made pickup easy today.",
    ],
    "rewards_program": [
        "Points never posted after my last three visits.",
        "Birthday reward made me feel valued as a member.",
    ],
    "price_value": [
        "Prices feel high for the cup size I received.",
        "Promo redemption made this visit feel like a good deal.",
    ],
    "seasonal_menu": [
        "Loved the new seasonal drink and would order again.",
        "Menu feels repetitive for frequent visitors.",
    ],
    "food_quality": [
        "Breakfast burrito was fresh and well seasoned.",
        "Pastry was stale even though I visited early morning.",
    ],
}


def _segment_profile(segment: str) -> dict:
    profiles = {
        "loyalty_regular": {"nps": 8.5, "loyalty": 0.92, "mobile": 0.45, "churn": 0.08},
        "occasional_guest": {"nps": 7.0, "loyalty": 0.35, "mobile": 0.3, "churn": 0.2},
        "mobile_first_guest": {"nps": 7.2, "loyalty": 0.55, "mobile": 0.88, "churn": 0.15},
        "price_sensitive_guest": {"nps": 6.2, "loyalty": 0.4, "mobile": 0.35, "churn": 0.25},
        "seasonal_product_explorer": {"nps": 7.8, "loyalty": 0.5, "mobile": 0.5, "churn": 0.12},
        "at_risk_guest": {"nps": 4.5, "loyalty": 0.3, "mobile": 0.4, "churn": 0.55},
    }
    return profiles[segment]


def build_stores(rng: np.random.Generator, fake: Faker) -> pd.DataFrame:
    markets = {
        "Midwest": ["Chicago", "Minneapolis", "Detroit", "Indianapolis"],
        "Northeast": ["Boston", "New York", "Philadelphia", "Hartford"],
        "South": ["Atlanta", "Dallas", "Miami", "Charlotte"],
        "West": ["Seattle", "Denver", "Portland", "Phoenix"],
    }
    rows = []
    for i in range(1, N_STORES + 1):
        region = str(rng.choice(REGIONS))
        market = str(rng.choice(markets[region]))
        store_type = str(rng.choice(STORE_TYPES))
        drive_thru = store_type in {"drive_thru", "suburban", "airport"} or rng.random() < 0.35
        rows.append(
            {
                "store_id": f"BB-{i:03d}",
                "store_name": f"{market} {store_type.replace('_', ' ').title()}",
                "market": market,
                "region": region,
                "store_type": store_type,
                "franchise_corporate_flag": str(rng.choice(["franchise", "corporate"], p=[0.62, 0.38])),
                "avg_daily_transactions": int(rng.integers(280, 920)),
                "avg_ticket": round(rng.uniform(6.8, 12.4), 2),
                "digital_order_share": round(float(rng.uniform(0.18, 0.62)), 3),
                "drive_thru_flag": int(drive_thru),
                "open_date": (datetime(int(rng.integers(2014, 2023)), int(rng.integers(1, 12)), 1)).strftime("%Y-%m-%d"),
                "data_source": DATA_SOURCE,
            }
        )
    return pd.DataFrame(rows)


def _pick_channel(rng: np.random.Generator, store: pd.Series, segment: str) -> str:
    if store["store_type"] == "drive_thru":
        weights = [0.08, 0.72, 0.15, 0.05]
    elif store["store_type"] == "airport":
        weights = [0.45, 0.05, 0.4, 0.1]
    elif segment == "mobile_first_guest":
        weights = [0.12, 0.18, 0.62, 0.08]
    else:
        weights = [0.38, 0.28, 0.24, 0.1]
    return str(rng.choice(CHANNELS, p=weights))


def _experience_scores(rng: np.random.Generator, segment: str, channel: str) -> dict[str, int]:
    profile = _segment_profile(segment)
    base = profile["nps"] / 2
    scores = {}
    for col in [
        "wait_time_rating",
        "drink_quality_rating",
        "order_accuracy_rating",
        "staff_friendliness_rating",
        "cleanliness_rating",
        "mobile_app_experience_rating",
        "rewards_satisfaction",
        "price_value_perception",
    ]:
        mean = base
        if col == "wait_time_rating" and channel in {"drive_thru", "mobile_order"}:
            mean -= 0.4
        if col == "mobile_app_experience_rating" and channel == "mobile_order":
            mean -= 0.3
        if col == "price_value_perception" and segment == "price_sensitive_guest":
            mean -= 0.5
        if col == "rewards_satisfaction" and segment == "loyalty_regular":
            mean += 0.4
        scores[col] = int(np.clip(round(rng.normal(mean, 0.7)), 1, 5))
    return scores


def _derive_outcomes(rng: np.random.Generator, scores: dict[str, int], segment: str) -> tuple[int, int, int]:
    profile = _segment_profile(segment)
    nps = int(np.clip(round(rng.normal(profile["nps"], 1.4)), 0, 10))
    penalty = sum(1 for k, v in scores.items() if v <= 2 and k in {"wait_time_rating", "drink_quality_rating"})
    nps = int(np.clip(nps - penalty, 0, 10))
    csat = int(np.clip(round(np.mean(list(scores.values()))), 1, 5))
    revisit = int(np.clip(round(csat * 0.85 + rng.normal(0.3, 0.5)), 1, 5))
    return nps, csat, revisit


def build_surveys(stores: pd.DataFrame, rng: np.random.Generator) -> pd.DataFrame:
    weights = stores["avg_daily_transactions"].to_numpy(dtype=float)
    weights /= weights.sum()
    rows = []
    for i in range(N_SURVEYS):
        store = stores.iloc[int(rng.choice(len(stores), p=weights))]
        segment = str(rng.choice(SEGMENTS, p=[0.24, 0.22, 0.14, 0.14, 0.12, 0.14]))
        channel = _pick_channel(rng, store, segment)
        scores = _experience_scores(rng, segment, channel)
        nps, csat, revisit = _derive_outcomes(rng, scores, segment)
        days = int((DATA_END - DATA_START).days)
        survey_date = DATA_START + timedelta(days=int(rng.integers(0, days)))

        rows.append(
            {
                "survey_id": f"SVY-{i + 1:06d}",
                "guest_id": f"GST-{i + 1:06d}",
                "store_id": store["store_id"],
                "survey_date": survey_date.strftime("%Y-%m-%d"),
                "guest_segment": segment,
                "visit_channel": channel,
                "nps": nps,
                "csat": csat,
                "revisit_intent": revisit,
                **scores,
                "data_source": DATA_SOURCE,
            }
        )
    return pd.DataFrame(rows)


def _compose_comment(rng: np.random.Generator, themes: list[str], sentiment: str) -> str:
    if not themes:
        return "Standard coffee visit with no major issues."
    parts = [rng.choice(COMMENT_TEMPLATES[t]) for t in themes]
    if sentiment == "positive":
        parts = [p.replace("too ", "").replace("weak", "solid") for p in parts]
    return " ".join(parts)


def build_comments(surveys: pd.DataFrame, rng: np.random.Generator) -> pd.DataFrame:
    theme_names = list(COMMENT_TEMPLATES.keys())
    rows = []
    for i, survey in surveys.iterrows():
        if rng.random() > 0.96:
            continue
        n_themes = int(rng.choice([1, 1, 2]))
        themes = list(rng.choice(theme_names, size=n_themes, replace=False))
        profile = _segment_profile(survey["guest_segment"])
        p_neg = 0.25 + profile["churn"] * 0.4
        sentiment = str(rng.choice(SENTIMENTS, p=[0.35, 0.2, 0.45] if p_neg > 0.4 else [0.45, 0.25, 0.3]))
        star = int(np.clip(round(survey["csat"] + rng.normal(0, 0.4)), 1, 5))
        rows.append(
            {
                "comment_id": f"CMT-{i + 1:06d}",
                "survey_id": survey["survey_id"],
                "guest_id": survey["guest_id"],
                "store_id": survey["store_id"],
                "comment_date": survey["survey_date"],
                "guest_segment": survey["guest_segment"],
                "visit_channel": survey["visit_channel"],
                "comment_text": _compose_comment(rng, themes, sentiment),
                "star_rating": star,
                "sentiment_label": sentiment,
                "data_source": DATA_SOURCE,
            }
        )
    return pd.DataFrame(rows)


def build_product_feedback(surveys: pd.DataFrame, rng: np.random.Generator) -> pd.DataFrame:
    rows = []
    feedback_id = 1
    for _, survey in surveys.iterrows():
        if rng.random() > 0.68:
            continue
        n_items = int(rng.choice([1, 1, 2]))
        chosen = rng.choice(len(PRODUCTS), size=n_items, replace=False)
        for idx in chosen:
            product = PRODUCTS[int(idx)]
            rows.append(
                {
                    "feedback_id": f"PFD-{feedback_id:06d}",
                    "survey_id": survey["survey_id"],
                    "guest_id": survey["guest_id"],
                    "store_id": survey["store_id"],
                    "feedback_date": survey["survey_date"],
                    "product_name": product["name"],
                    "product_category": product["category"],
                    "seasonal_flag": int(product["seasonal"]),
                    "seasonal_drink_awareness": int(
                        rng.choice([0, 1], p=[0.35, 0.65]) if product["seasonal"] else rng.choice([0, 1], p=[0.7, 0.3])
                    ),
                    "trial_flag": 1,
                    "product_rating": int(np.clip(round(survey["drink_quality_rating"] + rng.normal(0, 0.5)), 1, 5)),
                    "repeat_purchase_intent": int(np.clip(round(survey["revisit_intent"] + rng.normal(0, 0.4)), 1, 5)),
                    "sweetness_feedback": str(rng.choice(["too_sweet", "balanced", "not_sweet_enough"], p=[0.2, 0.6, 0.2])),
                    "price_value_feedback": str(rng.choice(["good_value", "fair", "too_expensive"], p=[0.3, 0.45, 0.25])),
                    "guest_segment": survey["guest_segment"],
                    "data_source": DATA_SOURCE,
                }
            )
            feedback_id += 1
    return pd.DataFrame(rows)


def build_loyalty_behavior(surveys: pd.DataFrame, rng: np.random.Generator) -> pd.DataFrame:
    rows = []
    for guest_id, group in surveys.groupby("guest_id"):
        segment = group.iloc[0]["guest_segment"]
        profile = _segment_profile(segment)
        member = int(rng.random() < profile["loyalty"])
        rows.append(
            {
                "guest_id": guest_id,
                "loyalty_member_flag": member,
                "visit_frequency_30d": int(np.clip(rng.poisson(3 if member else 1.2), 0, 20)),
                "days_since_last_visit": int(rng.integers(1, 45)),
                "promo_exposure_flag": int(rng.random() < 0.55),
                "promo_redeemed_flag": int(rng.random() < (0.35 if member else 0.12)),
                "mobile_order_usage_rate": round(float(np.clip(rng.normal(profile["mobile"], 0.15), 0, 1)), 3),
                "rewards_redemption_count": int(rng.poisson(1.5 if member else 0.2)),
                "churn_risk_proxy": round(float(np.clip(rng.normal(profile["churn"], 0.12), 0, 1)), 3),
                "data_source": DATA_SOURCE,
            }
        )
    return pd.DataFrame(rows)


def main() -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(RANDOM_SEED)
    fake = Faker()
    Faker.seed(RANDOM_SEED)
    fake.seed_instance(RANDOM_SEED)

    stores = build_stores(rng, fake)
    surveys = build_surveys(stores, rng)
    comments = build_comments(surveys, rng)
    product_feedback = build_product_feedback(surveys, rng)
    loyalty = build_loyalty_behavior(surveys, rng)

    paths = {
        "stores.csv": stores,
        "guest_surveys.csv": surveys,
        "guest_comments.csv": comments,
        "product_feedback.csv": product_feedback,
        "loyalty_behavior.csv": loyalty,
    }
    for name, df in paths.items():
        df.to_csv(RAW_DIR / name, index=False)
        print(f"Generated {len(df):,} rows -> {RAW_DIR / name}")

    metadata = {
        "brand": BRAND_NAME,
        "data_type": DATA_SOURCE,
        "random_seed": RANDOM_SEED,
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "date_range": {"start": DATA_START.strftime("%Y-%m-%d"), "end": DATA_END.strftime("%Y-%m-%d")},
        "record_counts": {k: len(v) for k, v in paths.items()},
    }
    (RAW_DIR / "data_dictionary.json").write_text(json.dumps(metadata, indent=2))
    print(f"Metadata -> {RAW_DIR / 'data_dictionary.json'}")


if __name__ == "__main__":
    main()
