"""Shared constants for Brew & Bloom synthetic data and analytics."""

from pathlib import Path

RANDOM_SEED = 42
BRAND_NAME = "Brew & Bloom Coffee Co."
DATA_SOURCE = "synthetic"

ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = ROOT / "data" / "raw"
PROCESSED_DIR = ROOT / "data" / "processed"
OUTPUT_TABLES = ROOT / "outputs" / "tables"
OUTPUT_CHARTS = ROOT / "outputs" / "charts"

REQUIRED_RAW_FILES = (
    "stores.csv",
    "guest_surveys.csv",
    "guest_comments.csv",
    "product_feedback.csv",
    "loyalty_behavior.csv",
    "data_dictionary.json",
)

N_STORES = 90
N_SURVEYS = 12_000

STUDY_START = "2024-01-01"
STUDY_END = "2024-06-30"

EXPECTED_ROW_COUNTS = {
    "stores": (75, 100),
    "guest_surveys": (8_000, 15_000),
    "guest_comments": (7_500, 15_000),
    "product_feedback": (5_000, 12_000),
    "loyalty_behavior": (8_000, 15_000),
}

REGIONS = ["Midwest", "Northeast", "South", "West"]
STORE_TYPES = ["urban", "suburban", "drive_thru", "mall", "airport", "campus"]
SEGMENTS = [
    "loyalty_regular",
    "occasional_guest",
    "mobile_first_guest",
    "price_sensitive_guest",
    "seasonal_product_explorer",
    "at_risk_guest",
]
CHANNELS = ["in_store", "drive_thru", "mobile_order", "delivery"]
SENTIMENTS = ["positive", "neutral", "negative"]

VOC_THEMES = [
    "speed_of_service",
    "drink_consistency",
    "order_accuracy",
    "staff_friendliness",
    "cleanliness",
    "mobile_app_issues",
    "rewards_value",
    "price_value",
    "seasonal_menu_interest",
    "drive_thru_experience",
]

PRODUCTS = [
    {"name": "Classic Latte", "category": "espresso", "seasonal": False},
    {"name": "Cold Brew", "category": "cold_brew", "seasonal": False},
    {"name": "Caramel Macchiato", "category": "espresso", "seasonal": False},
    {"name": "Oat Milk Cortado", "category": "espresso", "seasonal": False},
    {"name": "Pumpkin Spice Latte", "category": "espresso", "seasonal": True},
    {"name": "Iced Matcha Latte", "category": "tea", "seasonal": False},
    {"name": "Nitro Cold Brew", "category": "cold_brew", "seasonal": False},
    {"name": "Chai Tea Latte", "category": "tea", "seasonal": False},
    {"name": "Breakfast Burrito", "category": "food", "seasonal": False},
    {"name": "Avocado Toast", "category": "food", "seasonal": False},
    {"name": "Chocolate Croissant", "category": "bakery", "seasonal": False},
    {"name": "Blueberry Muffin", "category": "bakery", "seasonal": False},
    {"name": "Turkey Sandwich", "category": "food", "seasonal": False},
    {"name": "Seasonal Cold Brew", "category": "cold_brew", "seasonal": True},
]

EXPERIENCE_COLS = EXPERIENCE_RATINGS = [
    "wait_time_rating",
    "drink_quality_rating",
    "order_accuracy_rating",
    "staff_friendliness_rating",
    "cleanliness_rating",
    "mobile_app_experience_rating",
    "rewards_satisfaction",
    "price_value_perception",
]

THEME_RECOMMENDED_ACTIONS: dict[str, str] = {
    "speed_of_service": "Pilot peak-hour staffing and queue management in priority stores.",
    "drink_consistency": "Launch recipe adherence audit and barista retraining.",
    "order_accuracy": "Improve order handoff verification and customization checks.",
    "staff_friendliness": "Reinforce hospitality coaching and recognition programs.",
    "cleanliness": "Increase front-of-house cleaning cadence.",
    "mobile_app_issues": "Review mobile pickup timing and app-to-store handoff.",
    "rewards_value": "Test clearer loyalty value messaging and targeted rewards offers.",
    "price_value": "Test bundled offers or size-value messaging.",
    "seasonal_menu_interest": "Improve seasonal product positioning and sampling.",
    "drive_thru_experience": "Optimize drive-thru lane flow and pickup communication.",
    "general_experience": "Deploy service recovery and follow-up on low-CSAT guest surveys.",
}

IMPACT_DEFAULTS = {
    "target_store_count": 30,
    "improvement_window_days": 90,
    "expected_repeat_visit_lift": 0.02,
    "min_incremental_revenue_usd": 100_000,
}


def measurement_plan(window_days: int = 90) -> str:
    """Before/after metrics tracked for pilot stores vs matched controls."""
    return (
        "Before/after tracking in pilot stores vs matched controls over "
        f"{window_days} days: NPS, CSAT, revisit intent, negative comment rate, "
        "speed-of-service theme frequency, drink consistency complaint rate, "
        "and repeat visit behavior. Reconcile weekly against POS transaction counts."
    )

THEME_KEYWORDS: dict[str, list[str]] = {
    "speed_of_service": [
        "line took", "took forever", "slow", "long line", "waited", "backed up",
        "rush", "minutes", "peak hour", "forever",
    ],
    "drink_consistency": [
        "tasted different", "different than usual", "inconsistent", "burnt",
        "weak", "not the same", "quality", "espresso", "latte tasted",
    ],
    "order_accuracy": [
        "order was wrong", "wrong order", "incorrect", "missing", "customization",
        "pickup shelf", "confusing",
    ],
    "staff_friendliness": [
        "staff was friendly", "cashier was helpful", "barista", "friendly",
        "helpful", "warm", "greet", "apologized", "remembered",
    ],
    "cleanliness": [
        "clean", "sticky", "restroom", "messy", "trash", "dirty", "tidy", "floor",
    ],
    "mobile_app_issues": [
        "mobile ordering", "mobile order", "app", "not ready", "pickup timing",
        "pickup shelf", "notification", "crashed", "arrived",
    ],
    "rewards_value": [
        "rewards program", "points", "tier", "redeem", "not as valuable",
        "member", "birthday reward", "loyalty",
    ],
    "price_value": [
        "price feels", "expensive", "high for the size", "deal", "discount",
        "value", "cost", "too much",
    ],
    "seasonal_menu_interest": [
        "seasonal", "seasonal drink", "seasonal cold brew", "pumpkin",
        "limited", "new drink", "menu",
    ],
    "drive_thru_experience": [
        "drive-thru", "drive thru", "drive-thru was", "window", "lane",
        "speaker", "handoff",
    ],
}
