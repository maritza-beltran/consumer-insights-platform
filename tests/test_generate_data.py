"""Tests for synthetic data generation."""

from pathlib import Path

from config import N_STORES, N_SURVEYS, REQUIRED_RAW_FILES
from generate_data import generate_all_datasets, write_raw_datasets
from metrics import standard_nps

def test_generate_all_datasets_returns_five_tables():
    datasets = generate_all_datasets()
    assert set(datasets.keys()) == {
        "stores.csv",
        "guest_surveys.csv",
        "guest_comments.csv",
        "product_feedback.csv",
        "loyalty_behavior.csv",
    }
    assert len(datasets["stores.csv"]) == N_STORES
    assert len(datasets["guest_surveys.csv"]) == N_SURVEYS


def test_generated_brand_nps_is_challenged_but_plausible():
    datasets = generate_all_datasets()
    brand_nps = standard_nps(datasets["guest_surveys.csv"]["nps"])
    assert -20 <= brand_nps <= 15

def test_write_raw_datasets_creates_required_files(tmp_path: Path):
    written = write_raw_datasets(tmp_path)
    for filename in REQUIRED_RAW_FILES:
        assert (tmp_path / filename).exists(), f"missing {filename}"
        assert filename in written
