# consumer-insights-platform

Analysis-first **Voice of Customer (VoC)** project for **Brew & Bloom Coffee Co.**, a multi-location U.S. coffee brand. Built for Brand & Guest Insights, Consumer Insights, and Strategy Analytics portfolios.

**All data is synthetic** (seed=42), spanning **90 stores** and **12,000 surveys** over **Jan–Jun 2024**.

## Analytical Questions

1. What are the most common VoC themes?
2. Which themes are most associated with low NPS, CSAT, and revisit intent?
3. Which experience ratings best predict repeat visit intent?
4. How do pain points differ by segment, channel, region, and store type?
5. Which stores should leadership prioritize?
6. Which action has the clearest **$100K+** business impact?

## Raw Datasets (synthetic)

| File | Description |
|------|-------------|
| `data/raw/stores.csv` | 90 store locations with transaction and digital mix |
| `data/raw/guest_surveys.csv` | 12K surveys with NPS, CSAT, revisit intent, 8 experience ratings |
| `data/raw/guest_comments.csv` | Open-ended VoC comments linked to surveys |
| `data/raw/product_feedback.csv` | Product-level ratings across 13 menu items |
| `data/raw/loyalty_behavior.csv` | Guest loyalty, promo, and churn-risk signals |

## Quick Start

On macOS, `python` and `pip` are often not on your PATH — use **`make`** (recommended) or **`python3`** / **`.venv/bin/python`** below.

```bash
make setup    # creates .venv and installs dependencies (first time only)
make data
make validate
make build
make app
```

Or step-by-step with the project virtualenv:

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python src/generate_data.py
.venv/bin/python src/validate_data.py
.venv/bin/python src/build_outputs.py
.venv/bin/streamlit run app/streamlit_app.py
```

After `make setup`, you can activate the venv so `python` works in your shell:

```bash
source .venv/bin/activate
python src/build_outputs.py
streamlit run app/streamlit_app.py
```

## Pipeline

```
generate_data → validate_data → classify_voc_themes → analyze_themes
  → driver_analysis → segment_analysis → opportunity_scoring → impact_model
```

## Key Outputs

- `outputs/tables/theme_summary.csv` — theme volume, negative share, satisfaction metrics
- `outputs/tables/theme_impact.csv` — theme gaps vs brand averages
- `outputs/tables/detractor_theme_analysis.csv` — theme concentration among detractors
- `outputs/tables/driver_importance.csv` — logistic revisit-intent drivers
- `outputs/tables/model_metrics.csv` — classifier accuracy, precision, recall, ROC-AUC
- `outputs/tables/segment_summary.csv` — segment profiles and recommended actions
- `outputs/tables/segment_theme_matrix.csv` — segment × theme comment matrix
- `outputs/tables/store_opportunity_ranking.csv` — prioritized stores with upside sizing
- `outputs/tables/product_insights.csv` — product trial, rating, and complaint insights
- `outputs/tables/impact_summary.csv` — $100K+ incremental revenue sizing
- `outputs/tables/impact_sizing.json` — executive impact snapshot
- `reports/executive_memo.md` — leadership recommendation

## Tech Stack

pandas · numpy · scikit-learn · streamlit · plotly · duckdb · faker · matplotlib · pytest
