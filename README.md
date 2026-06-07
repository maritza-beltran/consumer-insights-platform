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

```bash
make setup
make data
make validate
make build
make app
```

Or step-by-step:

```bash
pip install -r requirements.txt
python src/generate_data.py
python src/validate_data.py
python src/build_outputs.py
streamlit run app/streamlit_app.py
```

## Pipeline

```
generate_data → validate_data → classify_voc_themes → analyze_themes
  → driver_analysis → segment_analysis → opportunity_scoring → impact_model
```

## Key Outputs

- `outputs/tables/theme_impact.csv` — theme volume and NPS gaps
- `outputs/tables/revisit_intent_drivers.csv` — experience rating predictors (Q3)
- `outputs/tables/store_opportunity_scores.csv` — prioritized stores
- `outputs/tables/impact_sizing.json` — $100K+ opportunity sizing
- `reports/executive_memo.md` — leadership recommendation

## Tech Stack

pandas · numpy · scikit-learn · streamlit · plotly · duckdb · faker · matplotlib · pytest
