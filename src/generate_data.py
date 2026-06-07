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
    VOC_THEMES,
)

DATA_START = datetime(2024, 1, 1)
DATA_END = datetime(2024, 6, 30)

# Primary-theme comment templates (varied realistic text)
THEME_COMMENTS: dict[str, list[str]] = {
    "speed_of_service": [
        "The line took forever even though there were only three people ahead of me.",
        "Morning rush staffing could not keep up with the volume at the counter.",
        "I waited far too long for a simple drip coffee order.",
        "The latte tasted different than usual, and the line took forever.",
    ],
    "drink_consistency": [
        "The latte tasted different than usual and did not match my last visit.",
        "My usual oat milk cortado was weaker and milkier than normal.",
        "Drink quality feels inconsistent across visits to this location.",
        "The espresso tasted burnt today even though it is usually solid.",
    ],
    "order_accuracy": [
        "My order was wrong and the pickup shelf was confusing.",
        "Received the wrong milk alternative twice in one week.",
        "Customization notes were ignored on my mobile order.",
        "Order was accurate and the barista confirmed my preferences.",
    ],
    "staff_friendliness": [
        "The staff was friendly even though the drive-thru was backed up.",
        "The store was clean and the cashier was helpful.",
        "Barista was warm and remembered my usual order.",
        "Team felt rushed and did not greet guests at the counter.",
    ],
    "cleanliness": [
        "Tables were sticky and the restroom needed attention.",
        "The store was clean and well maintained during a busy afternoon.",
        "Trash bins were overflowing near the condiment bar.",
        "Floor near the pickup area was messy during peak hours.",
    ],
    "mobile_app_issues": [
        "Mobile ordering was easy, but my drink was not ready when I arrived.",
        "App crashed while I tried to customize my drink.",
        "Pickup timing was off and the ready notification came late.",
        "Mobile order instructions were confusing at this location.",
    ],
    "rewards_value": [
        "The rewards program does not feel as valuable as it used to.",
        "Points never posted after my last three visits.",
        "Birthday reward made me feel valued as a member.",
        "Tier benefits are unclear and hard to redeem.",
    ],
    "price_value": [
        "I like the seasonal drinks, but the price feels high for the size.",
        "Prices feel high for the cup size I received.",
        "Promo redemption made this visit feel like a good deal.",
        "Happy hour pricing helped, but regular menu prices still feel steep.",
    ],
    "seasonal_menu_interest": [
        "I like the seasonal drinks and wanted to try the new cold brew.",
        "Seasonal menu items are creative but portion sizes feel small.",
        "Loved the new seasonal drink and would order again.",
        "Menu feels repetitive for frequent visitors.",
    ],
    "drive_thru_experience": [
        "Drive-thru lane was backed up and the speaker was hard to hear.",
        "Drive-thru handoff was smooth even with a long line.",
        "Window team was fast but the order was wrong at pickup.",
        "Drive-thru wait felt longer than the in-store line today.",
    ],
}

SECONDARY_SNIPPETS: dict[str, list[str]] = {
    "speed_of_service": ["and the line took forever.", "and the wait felt unacceptable."],
    "drink_consistency": ["and the drink tasted off.", "and quality was not consistent."],
    "order_accuracy": ["and my order was wrong.", "and the pickup shelf was confusing."],
    "staff_friendliness": ["but the staff was friendly throughout.", "and the cashier was helpful."],
    "cleanliness": ["and the store was very clean.", "but the seating area needed attention."],
    "mobile_app_issues": ["but mobile ordering was easy.", "and the app worked fine."],
    "rewards_value": ["and rewards did not feel worthwhile.", "and loyalty perks helped."],
    "price_value": ["and the price feels high for the size.", "and value was fair today."],
    "seasonal_menu_interest": ["and I liked the seasonal option.", "but seasonal drinks are hit or miss."],
    "drive_thru_experience": ["and the drive-thru was backed up.", "and drive-thru service was smooth."],
}


def _segment_profile(segment: str) -> dict:
    return {
        "loyalty_regular": {"nps": 8.5, "loyalty": 0.92, "mobile": 0.45, "churn": 0.08},
        "occasional_guest": {"nps": 7.0, "loyalty": 0.35, "mobile": 0.3, "churn": 0.2},
        "mobile_first_guest": {"nps": 7.2, "loyalty": 0.55, "mobile": 0.88, "churn": 0.15},
        "price_sensitive_guest": {"nps": 6.2, "loyalty": 0.4, "mobile": 0.35, "churn": 0.25},
        "seasonal_product_explorer": {"nps": 7.8, "loyalty": 0.5, "mobile": 0.5, "churn": 0.12},
        "at_risk_guest": {"nps": 4.5, "loyalty": 0.3, "mobile": 0.4, "churn": 0.55},
    }[segment]


def _theme_weights(store: pd.Series, segment: str, channel: str) -> np.ndarray:
    base = np.ones(len(VOC_THEMES))
    idx = {t: i for i, t in enumerate(VOC_THEMES)}

    if store["store_type"] == "drive_thru" or channel == "drive_thru":
        base[idx["speed_of_service"]] *= 3.0
        base[idx["drive_thru_experience"]] *= 2.5
    if segment == "mobile_first_guest" or channel == "mobile_order":
        base[idx["mobile_app_issues"]] *= 3.0
    if segment == "loyalty_regular":
        base[idx["rewards_value"]] *= 2.8
    if segment == "price_sensitive_guest":
        base[idx["price_value"]] *= 3.2
    if segment == "seasonal_product_explorer":
        base[idx["seasonal_menu_interest"]] *= 2.5
        base[idx["drink_consistency"]] *= 1.4
    if store["store_type"] in {"airport", "mall"}:
        base[idx["speed_of_service"]] *= 1.8
    if channel == "mobile_order":
        base[idx["order_accuracy"]] *= 1.5

    return base / base.sum()


def _pick_themes(
    rng: np.random.Generator, store: pd.Series, segment: str, channel: str
) -> tuple[str, str | None]:
    weights = _theme_weights(store, segment, channel)
    primary = str(rng.choice(VOC_THEMES, p=weights))
    secondary = None
    if rng.random() < 0.38:
        remaining = [t for t in VOC_THEMES if t != primary]
        rem_weights = _theme_weights(store, segment, channel)
        rem_probs = np.array([rem_weights[VOC_THEMES.index(t)] for t in remaining])
        rem_probs /= rem_probs.sum()
        secondary = str(rng.choice(remaining, p=rem_probs))
    return primary, secondary


def _compose_comment(
    rng: np.random.Generator,
    primary: str,
    secondary: str | None,
    sentiment: str,
) -> str:
    text = rng.choice(THEME_COMMENTS[primary])
    if secondary and rng.random() < 0.7:
        snippet = rng.choice(SECONDARY_SNIPPETS[secondary])
        if snippet.lower() not in text.lower():
            text = f"{text.rstrip('.')} {snippet}"
    if sentiment == "positive":
        text = (
            text.replace("took forever", "moved reasonably")
            .replace("was wrong", "was correct")
            .replace("not ready", "ready on time")
            .replace("does not feel as valuable", "feels valuable")
            .replace("price feels high", "price felt fair")
            .replace("way too sweet", "well balanced")
        )
    return text


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
        high_traffic = store_type in {"airport", "mall"}
        txn_low, txn_high = (620, 1050) if high_traffic else (280, 820)
        drive_thru = store_type in {"drive_thru", "suburban", "airport"} or rng.random() < 0.35
        rows.append(
            {
                "store_id": f"BB-{i:03d}",
                "store_name": f"{market} {store_type.replace('_', ' ').title()}",
                "market": market,
                "region": region,
                "store_type": store_type,
                "franchise_corporate_flag": str(rng.choice(["franchise", "corporate"], p=[0.62, 0.38])),
                "avg_daily_transactions": int(rng.integers(txn_low, txn_high)),
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


def _experience_scores(
    rng: np.random.Generator, segment: str, channel: str, store: pd.Series
) -> dict[str, int]:
    profile = _segment_profile(segment)
    base = profile["nps"] / 2
    if store["store_type"] in {"airport", "mall"}:
        base -= 0.35
    if store["store_type"] == "drive_thru" or channel == "drive_thru":
        wait_mean = base - 0.9
    else:
        wait_mean = base - 0.2

    scores: dict[str, float] = {
        "wait_time_rating": wait_mean,
        "drink_quality_rating": base,
        "order_accuracy_rating": base,
        "staff_friendliness_rating": base + 0.3,
        "cleanliness_rating": base,
        "mobile_app_experience_rating": base - (0.6 if channel == "mobile_order" else 0),
        "rewards_satisfaction": base + (0.5 if segment == "loyalty_regular" else -0.1),
        "price_value_perception": base - (0.7 if segment == "price_sensitive_guest" else 0),
    }
    if segment == "mobile_first_guest":
        scores["mobile_app_experience_rating"] -= 0.4

    return {k: int(np.clip(round(rng.normal(v, 0.65)), 1, 5)) for k, v in scores.items()}


def _derive_outcomes(
    rng: np.random.Generator, scores: dict[str, int], segment: str, store: pd.Series
) -> tuple[int, int, int]:
    profile = _segment_profile(segment)
    nps = int(np.clip(round(rng.normal(profile["nps"], 1.3)), 0, 10))

    if scores["wait_time_rating"] <= 2:
        nps = int(np.clip(nps - 2, 0, 10))
    elif scores["wait_time_rating"] == 3:
        nps = int(np.clip(nps - 1, 0, 10))

    csat_base = np.mean(list(scores.values()))
    if scores["staff_friendliness_rating"] >= 4:
        csat_base += 0.45
    if store["store_type"] in {"airport", "mall"}:
        csat_base -= 0.35
    csat = int(np.clip(round(csat_base), 1, 5))

    revisit_base = csat * 0.75 + 0.5
    if scores["drink_quality_rating"] <= 2:
        revisit_base -= 1.4
    elif scores["drink_quality_rating"] == 3:
        revisit_base -= 0.5
    if segment == "loyalty_regular" and scores["rewards_satisfaction"] <= 2:
        revisit_base -= 1.0
    if segment == "mobile_first_guest" and scores["mobile_app_experience_rating"] <= 2:
        revisit_base -= 0.8
    revisit = int(np.clip(round(revisit_base + rng.normal(0, 0.4)), 1, 5))
    return nps, csat, revisit


def build_surveys(stores: pd.DataFrame, rng: np.random.Generator) -> pd.DataFrame:
    weights = stores["avg_daily_transactions"].to_numpy(dtype=float)
    weights /= weights.sum()
    rows = []
    for i in range(N_SURVEYS):
        store = stores.iloc[int(rng.choice(len(stores), p=weights))]
        segment = str(rng.choice(SEGMENTS, p=[0.24, 0.22, 0.14, 0.14, 0.12, 0.14]))
        channel = _pick_channel(rng, store, segment)
        scores = _experience_scores(rng, segment, channel, store)
        nps, csat, revisit = _derive_outcomes(rng, scores, segment, store)
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


def build_comments(
    surveys: pd.DataFrame, stores: pd.DataFrame, rng: np.random.Generator
) -> pd.DataFrame:
    store_lookup = stores.set_index("store_id")
    rows = []
    for i, survey in surveys.iterrows():
        if rng.random() > 0.96:
            continue
        store = store_lookup.loc[survey["store_id"]]
        primary, secondary = _pick_themes(rng, store, survey["guest_segment"], survey["visit_channel"])
        profile = _segment_profile(survey["guest_segment"])
        p_neg = 0.22 + profile["churn"] * 0.45
        sentiment = str(
            rng.choice(SENTIMENTS, p=[0.32, 0.18, 0.5] if p_neg > 0.4 else [0.48, 0.22, 0.3])
        )
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
                "comment_text": _compose_comment(rng, primary, secondary, sentiment),
                "primary_theme": primary,
                "secondary_theme": secondary or "",
                "star_rating": star,
                "sentiment_label": sentiment,
                "data_source": DATA_SOURCE,
            }
        )
    return pd.DataFrame(rows)


def build_product_feedback(surveys: pd.DataFrame, rng: np.random.Generator) -> pd.DataFrame:
    rows = []
    feedback_id = 1
    seasonal_idx = [i for i, p in enumerate(PRODUCTS) if p["seasonal"]]
    for _, survey in surveys.iterrows():
        trial_prob = 0.78 if survey["guest_segment"] == "seasonal_product_explorer" else 0.62
        if rng.random() > trial_prob:
            continue
        if survey["guest_segment"] == "seasonal_product_explorer" and rng.random() < 0.55:
            product = PRODUCTS[int(rng.choice(seasonal_idx))]
        else:
            product = PRODUCTS[int(rng.choice(len(PRODUCTS)))]
        too_sweet = str(rng.choice(["too_sweet", "balanced", "not_sweet_enough"], p=[0.28, 0.55, 0.17]))
        repeat = int(np.clip(round(survey["revisit_intent"] + rng.normal(0, 0.5)), 1, 5))
        if product["seasonal"] and too_sweet == "too_sweet":
            repeat = int(np.clip(repeat - 2, 1, 5))
        if survey["guest_segment"] == "seasonal_product_explorer" and product["seasonal"]:
            repeat = int(np.clip(round(rng.choice([2, 3, 4, 5], p=[0.25, 0.3, 0.25, 0.2])), 1, 5))
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
                    rng.choice([0, 1], p=[0.2, 0.8]) if product["seasonal"] else rng.choice([0, 1], p=[0.7, 0.3])
                ),
                "trial_flag": 1,
                "product_rating": int(np.clip(round(survey["drink_quality_rating"] + rng.normal(0, 0.5)), 1, 5)),
                "repeat_purchase_intent": repeat,
                "sweetness_feedback": too_sweet,
                "price_value_feedback": str(
                    rng.choice(["good_value", "fair", "too_expensive"], p=[0.25, 0.4, 0.35])
                    if survey["guest_segment"] == "price_sensitive_guest"
                    else rng.choice(["good_value", "fair", "too_expensive"], p=[0.35, 0.45, 0.2])
                ),
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
                "visit_frequency_30d": int(np.clip(rng.poisson(4 if member else 1.2), 0, 20)),
                "days_since_last_visit": int(rng.integers(1, 45)),
                "promo_exposure_flag": int(rng.random() < 0.55),
                "promo_redeemed_flag": int(rng.random() < (0.35 if member else 0.12)),
                "mobile_order_usage_rate": round(float(np.clip(rng.normal(profile["mobile"], 0.15), 0, 1)), 3),
                "rewards_redemption_count": int(rng.poisson(2.0 if member else 0.2)),
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
    comments = build_comments(surveys, stores, rng)
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
        "voc_themes": VOC_THEMES,
    }
    (RAW_DIR / "data_dictionary.json").write_text(json.dumps(metadata, indent=2))


if __name__ == "__main__":
    main()
