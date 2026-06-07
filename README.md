# consumer-insights-platform

Analysis-first **Voice of Customer (VoC)** project for **Brew & Bloom Coffee Co.**, a multi-location coffee brand. Built for Brand & Guest Insights, Consumer Insights, and Strategy Analytics portfolios.

**All data is synthetic** (seed=42) and clearly labeled. No paid APIs or external data sources.

## Business Questions

- What are the most common Voice of Customer themes?
- Which themes are most associated with low NPS and low revisit intent?
- How do pain points differ by guest segment, channel, region, and store type?
- Which stores should leadership prioritize?
- What action has the clearest **$100K+** upside?

## Quick Start

```bash
pip install -r requirements.txt
python src/generate_data.py
python src/validate_data.py
python src/build_outputs.py
streamlit run app/streamlit_app.py
```

Or use Makefile targets:

```bash
make setup    # install dependencies
make data     # generate synthetic data
make validate # run quality checks
make build    # run full analytics pipeline
make app      # launch Streamlit dashboard
make test     # run pytest
```

## Project Structure

```
consumer-insights-platform/
├── app/streamlit_app.py          # Interactive executive dashboard
├── data/raw/                     # Synthetic source CSVs
├── data/processed/               # Validated & classified parquet
├── notebooks/                    # Research notebooks (01–05)
├── outputs/tables/               # Analysis CSV/JSON exports
├── outputs/charts/               # Static matplotlib charts
├── reports/                      # Executive memo, methodology, codebook
├── sql/                          # DuckDB-compatible metric queries
├── src/                          # Pipeline scripts
└── tests/                        # pytest suite
```

## Pipeline

| Step | Script | Output |
|------|--------|--------|
| 1 | `generate_data.py` | `data/raw/guest_surveys.csv`, `stores.csv` |
| 2 | `validate_data.py` | `validation_report.json`, clean parquet |
| 3 | `build_outputs.py` | Themes, drivers, segments, stores, impact sizing |
| 4 | `streamlit_app.py` | Interactive exploration |

`build_outputs.py` orchestrates: theme classification → theme analysis → driver modeling → segment analysis → store scoring → impact sizing → DuckDB SQL exports.

## Tech Stack

pandas · numpy · scikit-learn · streamlit · plotly · duckdb · faker · matplotlib · pytest

## Key Deliverables

- **Executive memo:** `reports/executive_memo.md`
- **Methodology:** `reports/methodology.md`
- **VoC codebook:** `reports/voc_codebook.md`
- **Impact sizing:** `outputs/tables/impact_sizing.json`
- **Store priorities:** `outputs/tables/store_opportunity_scores.csv`

## Notebooks

| Notebook | Focus |
|----------|-------|
| `01_data_quality_review` | Validation metrics & distributions |
| `02_voc_theme_analysis` | Theme prevalence and NPS gaps |
| `03_satisfaction_driver_analysis` | Logistic driver model |
| `04_segment_and_store_opportunities` | Segment & store prioritization |
| `05_executive_recommendations` | Impact sizing & leadership actions |

## License

Portfolio / demonstration project. Synthetic data only.
