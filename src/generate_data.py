"""Generate synthetic guest survey data for Brew & Bloom Coffee Co."""

from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd
from faker import Faker

RANDOM_SEED = 42
N_SURVEYS = 6000
BRAND_NAME = "Brew & Bloom Coffee Co."
DATA_START = datetime(2024, 1, 1)

ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = ROOT / "data" / "raw"

REGIONS = ["Northeast", "Southeast", "Midwest", "West"]
STORE_TYPES = ["urban flagship", "suburban", "airport", "campus", "drive-thru focused"]
CHANNELS = ["in-store", "drive-thru", "mobile order"]
SEGMENTS = ["loyalist", "occasional", "new_guest", "at_risk"]

THEME_TEMPLATES = {
    "speed_of_service": [
        "The line moved too slowly during my morning rush visit.",
        "Drive-thru wait was longer than expected for a simple latte.",
        "Mobile order was ready late even though I ordered ahead.",
    ],
    "product_quality": [
        "My espresso tasted burnt and the milk was overheated.",
        "The cold brew was weak compared to other locations.",
        "Pastry was stale even though I visited early morning.",
    ],
    "cleanliness": [
        "Tables were sticky and the restroom needed attention.",
        "Floor near the condiment bar was messy during peak hours.",
        "Trash bins were overflowing when I arrived.",
    ],
    "staff_friendliness": [
        "Barista was warm and remembered my usual order.",
        "Team felt rushed and did not greet guests at the counter.",
        "Staff apologized sincerely when my order was wrong.",
    ],
    "value_for_money": [
        "Prices feel high for the cup size I received.",
        "Happy hour discount made this visit feel like a good deal.",
        "Loyalty rewards rarely offset rising menu prices.",
    ],
    "ambiance": [
        "Music was too loud for a working session.",
        "Seating layout is cozy and inviting for meetings.",
        "Lighting felt harsh and made the space uncomfortable.",
    ],
    "mobile_app": [
        "App crashed while I tried to customize my drink.",
        "Mobile order pickup instructions were confusing.",
        "Push notifications for rewards are helpful and timely.",
    ],
    "loyalty_program": [
        "Points never posted after my last three visits.",
        "Tier benefits are unclear and hard to redeem.",
        "Birthday reward made me feel valued as a member.",
    ],
    "menu_variety": [
        "Limited dairy-free options compared to competitors.",
        "Seasonal menu items are creative and well executed.",
        "Food menu feels repetitive for frequent visitors.",
    ],
    "wait_time": [
        "Waited 12 minutes for a drink that should take five.",
        "Peak hour staffing seems insufficient for order volume.",
        "Pickup shelf was disorganized and delayed handoff.",
    ],
}

NEUTRAL_COMMENTS = [
    "Solid visit overall with no major issues.",
    "Convenient location near my office.",
    "Would return if I am in the neighborhood again.",
    "Standard coffee experience for a busy weekday.",
]


def _build_stores(fake: Faker, rng: np.random.Generator) -> pd.DataFrame:
    stores = []
    store_id = 1
    for region in REGIONS:
        n_stores = rng.integers(5, 8)
        for _ in range(n_stores):
            store_type = rng.choice(STORE_TYPES)
            monthly_transactions = int(rng.integers(8000, 22000))
            avg_ticket = round(rng.uniform(6.5, 11.5), 2)
            stores.append(
                {
                    "store_id": f"BB-{store_id:03d}",
                    "store_name": f"{fake.city()} {store_type.title()}",
                    "region": region,
                    "store_type": store_type,
                    "monthly_transactions": monthly_transactions,
                    "avg_ticket_usd": avg_ticket,
                    "opened_year": int(rng.integers(2016, 2023)),
                }
            )
            store_id += 1
    return pd.DataFrame(stores)


def _pick_themes(rng: np.random.Generator, segment: str) -> list[str]:
    base_weights = {
        "speed_of_service": 0.14,
        "product_quality": 0.12,
        "cleanliness": 0.1,
        "staff_friendliness": 0.11,
        "value_for_money": 0.09,
        "ambiance": 0.07,
        "mobile_app": 0.08,
        "loyalty_program": 0.09,
        "menu_variety": 0.1,
        "wait_time": 0.1,
    }
    if segment == "at_risk":
        base_weights["speed_of_service"] += 0.05
        base_weights["wait_time"] += 0.04
        base_weights["loyalty_program"] += 0.03
    if segment == "loyalist":
        base_weights["staff_friendliness"] += 0.04
        base_weights["loyalty_program"] += 0.03

    themes = list(base_weights.keys())
    weights = np.array([base_weights[t] for t in themes])
    weights /= weights.sum()
    n_themes = int(rng.choice([1, 1, 2, 2, 3]))
    chosen = rng.choice(themes, size=n_themes, replace=False, p=weights)
    return list(chosen)


def _theme_sentiment(rng: np.random.Generator, theme: str, segment: str) -> str:
    negative_bias = {
        "speed_of_service": 0.55,
        "wait_time": 0.6,
        "cleanliness": 0.5,
        "mobile_app": 0.45,
        "loyalty_program": 0.4,
        "product_quality": 0.35,
        "value_for_money": 0.4,
        "staff_friendliness": 0.25,
        "ambiance": 0.3,
        "menu_variety": 0.3,
    }
    p_neg = negative_bias.get(theme, 0.35)
    if segment == "at_risk":
        p_neg += 0.12
    if segment == "loyalist":
        p_neg -= 0.1
    p_neg = float(np.clip(p_neg, 0.1, 0.85))
    return "negative" if rng.random() < p_neg else "positive"


def _compose_comment(rng: np.random.Generator, themes: list[str], segment: str) -> str:
    if not themes:
        return rng.choice(NEUTRAL_COMMENTS)
    parts = []
    for theme in themes:
        template = rng.choice(THEME_TEMPLATES[theme])
        sentiment = _theme_sentiment(rng, theme, segment)
        if sentiment == "positive" and "too" in template.lower():
            template = template.replace("too ", "").replace("longer than expected", "reasonable")
        parts.append(template)
    if rng.random() < 0.2:
        parts.append(rng.choice(NEUTRAL_COMMENTS))
    return " ".join(parts)


def _derive_scores(
    rng: np.random.Generator, themes: list[str], segment: str, channel: str
) -> tuple[int, int, int]:
    base_nps = {"loyalist": 9, "occasional": 7, "new_guest": 8, "at_risk": 4}[segment]
    nps = int(np.clip(rng.normal(base_nps, 1.6), 0, 10))

    negative_themes = {"speed_of_service", "wait_time", "cleanliness", "mobile_app", "product_quality"}
    penalty = sum(1 for t in themes if t in negative_themes and _theme_sentiment(rng, t, segment) == "negative")
    nps = int(np.clip(nps - penalty, 0, 10))

    if channel == "mobile order" and "mobile_app" in themes:
        nps = int(np.clip(nps - 1, 0, 10))

    csat = int(np.clip(round(nps / 2 + rng.normal(0, 0.4)), 1, 5))
    revisit = int(np.clip(round(nps / 2.2 + rng.normal(0.5, 0.5)), 1, 5))
    return nps, csat, revisit


def generate_surveys(stores: pd.DataFrame, rng: np.random.Generator, fake: Faker) -> pd.DataFrame:
    rows = []
    store_weights = stores["monthly_transactions"].to_numpy(dtype=float)
    store_weights /= store_weights.sum()

    for i in range(N_SURVEYS):
        store_idx = int(rng.choice(len(stores), p=store_weights))
        store = stores.iloc[store_idx]
        segment = str(rng.choice(SEGMENTS, p=[0.32, 0.34, 0.18, 0.16]))
        channel = str(rng.choice(CHANNELS, p=[0.42, 0.33, 0.25]))
        if store["store_type"] == "drive-thru focused":
            channel = str(rng.choice(["drive-thru", "mobile order"], p=[0.7, 0.3]))
        if store["store_type"] == "airport":
            channel = str(rng.choice(CHANNELS, p=[0.55, 0.1, 0.35]))

        themes = _pick_themes(rng, segment)
        nps, csat, revisit = _derive_scores(rng, themes, segment, channel)
        survey_date = DATA_START + timedelta(days=int(rng.integers(0, 365)))

        rows.append(
            {
                "survey_id": f"SVY-{i + 1:06d}",
                "guest_id": f"GST-{fake.uuid4()[:8].upper()}",
                "survey_date": survey_date.strftime("%Y-%m-%d"),
                "store_id": store["store_id"],
                "store_name": store["store_name"],
                "region": store["region"],
                "store_type": store["store_type"],
                "channel": channel,
                "segment": segment,
                "nps_score": nps,
                "csat_score": csat,
                "revisit_intent": revisit,
                "visit_frequency_monthly": int(rng.integers(1, 16)),
                "comment_text": _compose_comment(rng, themes, segment),
                "data_source": "synthetic",
                "brand": BRAND_NAME,
            }
        )
    return pd.DataFrame(rows)


def main() -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(RANDOM_SEED)
    fake = Faker()
    Faker.seed(RANDOM_SEED)
    fake.seed_instance(RANDOM_SEED)

    stores = _build_stores(fake, rng)
    surveys = generate_surveys(stores, rng, fake)

    stores_path = RAW_DIR / "stores.csv"
    surveys_path = RAW_DIR / "guest_surveys.csv"
    metadata_path = RAW_DIR / "data_dictionary.json"

    stores.to_csv(stores_path, index=False)
    surveys.to_csv(surveys_path, index=False)

    metadata = {
        "brand": BRAND_NAME,
        "data_type": "synthetic",
        "random_seed": RANDOM_SEED,
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "n_stores": len(stores),
        "n_surveys": len(surveys),
        "files": {
            "stores": str(stores_path.relative_to(ROOT)),
            "guest_surveys": str(surveys_path.relative_to(ROOT)),
        },
    }
    metadata_path.write_text(json.dumps(metadata, indent=2))

    print(f"Generated {len(stores)} stores -> {stores_path}")
    print(f"Generated {len(surveys)} surveys -> {surveys_path}")


if __name__ == "__main__":
    main()
