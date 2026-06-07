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
    "wait_time": ["wait", "minutes", "slow", "line", "staffing", "handoff", "rush"],
    "drink_quality": ["espresso", "burnt", "stale", "weak", "taste", "milk", "cold brew", "drink"],
    "order_accuracy": ["wrong order", "accuracy", "customize", "missing", "incorrect"],
    "staff_friendliness": ["barista", "staff", "greet", "friendly", "warm", "team", "apologized"],
    "cleanliness": ["sticky", "restroom", "messy", "trash", "dirty", "clean", "floor"],
    "mobile_app": ["app", "mobile order", "pickup", "notification", "crashed", "digital"],
    "rewards_program": ["points", "tier", "reward", "redeem", "birthday", "member", "promo"],
    "price_value": ["price", "deal", "discount", "value", "expensive", "cost"],
    "seasonal_menu": ["seasonal", "pumpkin", "limited", "menu", "variety", "options"],
    "food_quality": ["pastry", "burrito", "toast", "sandwich", "muffin", "food", "bakery"],
}
