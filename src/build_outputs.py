"""Orchestrate the full analytics pipeline from raw data to executive outputs."""

from __future__ import annotations

import sys
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = ROOT / "src"
SQL_DIR = ROOT / "sql"
PROCESSED_DIR = ROOT / "data" / "processed"
OUTPUT_TABLES = ROOT / "outputs" / "tables"

# Ensure src modules import correctly when run as a script
sys.path.insert(0, str(SRC_DIR))

from analyze_themes import main as run_theme_analysis
from classify_voc_themes import classify_and_save
from driver_analysis import main as run_driver_analysis
from impact_model import main as run_impact_model
from opportunity_scoring import main as run_opportunity_scoring
from product_insights import main as run_product_insights
from segment_analysis import main as run_segment_analysis
from validate_data import load_raw_datasets, validate_and_export

SQL_FILES = [
    "survey_metrics.sql",
    "theme_impact_analysis.sql",
    "segment_analysis.sql",
    "store_opportunity_analysis.sql",
]


def _run_sql_exports() -> None:
    """Re-aggregate key metrics with DuckDB for auditability."""
    OUTPUT_TABLES.mkdir(parents=True, exist_ok=True)
    classified = PROCESSED_DIR / "guest_surveys_classified.parquet"
    stores = PROCESSED_DIR / "stores_clean.parquet"
    if not classified.exists():
        raise FileNotFoundError("Classified surveys not found — run classification first")

    con = duckdb.connect()
    con.execute(f"CREATE OR REPLACE VIEW guest_surveys AS SELECT * FROM read_parquet('{classified}')")
    con.execute(f"CREATE OR REPLACE VIEW stores AS SELECT * FROM read_parquet('{stores}')")

    for sql_file in SQL_FILES:
        query = (SQL_DIR / sql_file).read_text()
        out_path = OUTPUT_TABLES / f"{sql_file.replace('.sql', '_duckdb.csv')}"
        df = con.execute(query).fetchdf()
        df.to_csv(out_path, index=False)
        print(f"  SQL export: {out_path.name} ({len(df)} rows)")


def main() -> None:
    print("=== Brew & Bloom Analytics Pipeline ===\n")

    # 1. Load raw data
    print("1. Loading raw data...")
    datasets = load_raw_datasets()
    for name, df in datasets.items():
        print(f"   {name}: {len(df):,} rows")

    # 2. Validate data (flags suspicious records; does not delete)
    print("\n2. Validating data...")
    summary, report = validate_and_export(datasets, raise_on_fail=True)
    print(f"   Status: {report['status']} | Warn checks: {report['warn_checks']}")
    print(f"   Summary -> {OUTPUT_TABLES / 'validation_summary.csv'}")

    # 3. Classify VoC themes
    print("\n3. Classifying VoC themes...")
    classified = classify_and_save()
    print(f"   Classified {len(classified):,} surveys -> guest_surveys_classified.parquet")

    # 4. Processed data already saved during validation + classification
    print("\n4. Processed data saved to data/processed/")

    # 5. Build analytical summary tables
    print("\n5. Building theme analysis tables...")
    run_theme_analysis()

    # 6. Train driver models (NPS promoters + revisit intent)
    print("\n6. Training satisfaction driver models...")
    run_driver_analysis()

    # 7. Segment and dimension analysis
    print("\n7. Building segment analysis...")
    run_segment_analysis()

    # 8. Store opportunity ranking
    print("\n8. Building store opportunity scores...")
    run_opportunity_scoring()

    # 9. Product insights
    print("\n9. Building product insights...")
    run_product_insights()

    # 10. Impact model output
    print("\n10. Building impact model...")
    run_impact_model()

    # DuckDB SQL exports for audit trail
    print("\n11. Running DuckDB SQL exports...")
    _run_sql_exports()

    print("\n=== Build complete ===")
    print(f"Tables: {OUTPUT_TABLES}")
    print(f"Charts: {ROOT / 'outputs' / 'charts'}")


if __name__ == "__main__":
    main()
