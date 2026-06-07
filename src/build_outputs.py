"""Orchestrate the full analytics pipeline and run DuckDB SQL exports."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parent.parent
SQL_DIR = ROOT / "sql"
PROCESSED_DIR = ROOT / "data" / "processed"
OUTPUT_TABLES = ROOT / "outputs" / "tables"

PIPELINE_STEPS = [
    "classify_voc_themes.py",
    "analyze_themes.py",
    "driver_analysis.py",
    "segment_analysis.py",
    "opportunity_scoring.py",
    "impact_model.py",
]

SQL_FILES = [
    "survey_metrics.sql",
    "theme_impact_analysis.sql",
    "segment_analysis.sql",
    "store_opportunity_analysis.sql",
]


def _run_script(script_name: str) -> None:
    script_path = ROOT / "src" / script_name
    print(f"\n--- Running {script_name} ---")
    result = subprocess.run([sys.executable, str(script_path)], check=False)
    if result.returncode != 0:
        raise RuntimeError(f"{script_name} failed with exit code {result.returncode}")


def _run_sql_exports() -> None:
    OUTPUT_TABLES.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect()

    classified = PROCESSED_DIR / "guest_surveys_classified.parquet"
    stores = PROCESSED_DIR / "stores_clean.parquet"
    if not classified.exists():
        raise FileNotFoundError("Run validate + classify before build_outputs")

    con.execute(f"CREATE OR REPLACE VIEW guest_surveys AS SELECT * FROM read_parquet('{classified}')")
    con.execute(f"CREATE OR REPLACE VIEW stores AS SELECT * FROM read_parquet('{stores}')")

    for sql_file in SQL_FILES:
        sql_path = SQL_DIR / sql_file
        query = sql_path.read_text()
        out_name = sql_path.stem + "_duckdb.csv"
        out_path = OUTPUT_TABLES / out_name
        df = con.execute(query).fetchdf()
        df.to_csv(out_path, index=False)
        print(f"SQL export: {out_name} ({len(df)} rows)")


def main() -> None:
    for step in PIPELINE_STEPS:
        _run_script(step)
    _run_sql_exports()
    print("\n=== Build complete ===")
    print(f"Tables: {OUTPUT_TABLES}")
    print(f"Charts: {ROOT / 'outputs' / 'charts'}")


if __name__ == "__main__":
    main()
