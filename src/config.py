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

N_STORES = 90
N_SURVEYS = 12_000

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
