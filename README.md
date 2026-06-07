# Voice of Customer Insights Platform

Analysis-first **Voice of Customer (VoC)** analytics project for **Brew & Bloom Coffee Co.**, a multi-location U.S. coffee brand. The repo demonstrates an end-to-end consumer insights workflow — from synthetic data generation through validation, theme classification, driver modeling, store prioritization, and executive reporting.

Built for **Brand & Guest Insights**, **Consumer Insights**, and **Strategy Analytics** portfolios.

---

## Business Problem

Brew & Bloom operates **90 U.S. locations** across malls, airports, drive-thrus, and urban formats. Leadership receives thousands of guest surveys and open-text comments but struggles to answer:

- Which experience issues matter most for **NPS**, **CSAT**, and **repeat visit intent**?
- Where should Operations, Marketing, and Digital invest limited pilot capacity?
- What is the **business case** for fixing the highest-priority pain points?

This project turns fragmented guest feedback into a ranked action plan with quantified upside.

---

## Why This Project Matters

Most VoC work stops at word clouds or sentiment scores. This platform goes further:

- **Separates frequency from impact** — the most-mentioned theme is not always the most damaging to loyalty.
- **Links qualitative feedback to quantitative outcomes** — themes are tied to NPS gaps, revisit intent, and logistic driver coefficients.
- **Prioritizes stores by opportunity** — composite scoring blends negative feedback rate, satisfaction gaps, and traffic weight.
- **Sizes a decision-ready business case** — default assumptions produce a **$100K+** incremental revenue estimate tied to a measurement plan.

The result is a portfolio-ready example of how insights teams translate open text into cross-functional recommendations.

---

## Tech Stack

| Layer | Tools |
|-------|-------|
| **Data & analytics** | Python, pandas, numpy, scikit-learn |
| **SQL validation** | DuckDB (`sql/*.sql`) |
| **Visualization** | matplotlib, plotly |
| **Dashboard** | Streamlit |
| **Synthetic data** | Faker, numpy (seed=42) |
| **Testing** | pytest |

---

## Project Structure

```
consumer-insights-platform/
├── app/
│   └── streamlit_app.py          # 4-page executive dashboard (reads precomputed outputs)
├── data/
│   ├── raw/                      # Synthetic CSV inputs (5 datasets)
│   └── processed/                # Validated parquet + validation_report.json
├── outputs/
│   ├── tables/                   # Analytic CSV tables and DuckDB exports
│   └── charts/                   # Static PNG charts
├── reports/
│   ├── executive_memo.md         # Leadership summary and recommendations
│   ├── methodology.md            # Pipeline, formulas, and limitations
│   └── voc_codebook.md           # Theme definitions and keyword rules
├── sql/
│   ├── survey_metrics.sql
│   ├── theme_impact_analysis.sql
│   ├── segment_analysis.sql
│   └── store_opportunity_analysis.sql
├── src/
│   ├── generate_data.py          # Synthetic data generation
│   ├── validate_data.py          # 33 validation checks
│   ├── classify_voc_themes.py    # Rule-based theme classifier
│   ├── analyze_themes.py         # Theme summary and impact
│   ├── driver_analysis.py        # Logistic revisit-intent model
│   ├── segment_analysis.py       # Guest segment profiles
│   ├── opportunity_scoring.py    # Store opportunity ranking
│   ├── impact_model.py           # $100K+ revenue sizing
│   ├── build_outputs.py          # Full pipeline orchestrator
│   └── config.py                 # Shared constants and theme keywords
├── notebooks/                    # Lightweight walkthrough notebooks (read src/ + outputs)
└── tests/                        # pytest suite (generation, validation, themes, scoring, impact)
```

---

## How to Run

On macOS, `python` and `pip` are often not on your PATH — use **`make`** (recommended) or **`.venv/bin/python`**.

```bash
make setup    # create .venv and install dependencies (first time only)
make data     # generate synthetic raw data
make validate # run validation checks
make build    # run full analytics pipeline
make app      # launch Streamlit dashboard
make test     # run pytest (16 tests: data gen, validation, themes, drivers, scoring, impact)
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

After `make setup`, activate the venv so `python` works in your shell:

```bash
source .venv/bin/activate
python src/build_outputs.py
streamlit run app/streamlit_app.py
```

### Pipeline

```
generate_data → validate_data → classify_voc_themes → analyze_themes
  → driver_analysis → segment_analysis → opportunity_scoring → impact_model
```

---

## Analytical Questions Answered

1. What are the most common VoC themes in guest comments?
2. Which themes are most associated with low NPS, CSAT, and revisit intent?
3. Which experience ratings best predict high repeat visit intent?
4. How do pain points differ by guest segment, visit channel, region, and store type?
5. Which themes over-index among detractors?
6. Which stores should leadership prioritize for improvement pilots?
7. Which initiative has the clearest **$100K+** business impact under stated assumptions?

---

## Data Sources Are Simulated

**All data in this repository is synthetic** (`data_source = "synthetic"`, `RANDOM_SEED = 42`). No real guest, store, or transaction data is used.

| Dataset | Records | Description |
|---------|---------|-------------|
| `stores.csv` | 90 | Store metadata, traffic, and ticket proxies |
| `guest_surveys.csv` | 12,000 | NPS, CSAT, revisit intent, 8 experience ratings |
| `guest_comments.csv` | ~11,500 | Open-ended VoC comments linked to surveys |
| `product_feedback.csv` | ~7,700 | Product trial and rating feedback |
| `loyalty_behavior.csv` | 12,000 | Visit frequency and loyalty signals |

Study period: **January–June 2024**. See `reports/methodology.md` for generation logic and embedded assumptions.

---

## Key Outputs

| Output | Purpose |
|--------|---------|
| `theme_summary.csv` | Theme volume, negative share, NPS/CSAT/revisit |
| `theme_impact.csv` | Theme gaps vs brand baseline, impact rank |
| `detractor_theme_analysis.csv` | Detractor over-index by theme |
| `driver_importance.csv` | Logistic revisit-intent drivers (odds ratios) |
| `model_metrics.csv` | Classifier accuracy, precision, recall, ROC-AUC |
| `segment_summary.csv` | Segment KPIs, top themes, recommended actions |
| `segment_theme_matrix.csv` | Segment × theme comment matrix |
| `store_opportunity_ranking.csv` | Ranked stores with opportunity scores |
| `product_insights.csv` | Product trial, rating, and complaint insights |
| `impact_summary.csv` | Incremental revenue sizing and measurement plan |
| `validation_summary.csv` | 33 automated data quality checks |
| `reports/executive_memo.md` | Leadership memo with key insights and actions |

---

## Dashboard Page Descriptions

The Streamlit app (`app/streamlit_app.py`) reads precomputed tables only — no live pipeline execution.

### Page 1 — Executive Readout

Brand-level KPIs (surveys, comments, NPS, CSAT, revisit intent), top negative theme, top satisfaction driver, and estimated 90-day revenue opportunity. Charts: top 5 themes by volume, top 5 themes by NPS gap, top 5 store opportunities. Includes key takeaway, recommended action, expected business impact, and the full executive memo.

### Page 2 — Voice of Customer Deep Dive

Filterable exploration by region, store type, guest segment, and visit channel. Theme frequency, negative share, NPS/CSAT/revisit by theme, detractor over-index, and sample guest comments. Highlights that the most frequent issue is not always the most damaging.

### Page 3 — Drivers and Segments

Logistic regression driver importance (coefficients, odds ratios, plain-English interpretation) and model metrics. Segment-level NPS chart, segment summary table, and segment × theme pain-point heatmap.

### Page 4 — Opportunities and Recommendations

Ranked store opportunity table and bar chart. Interactive **business impact calculator** (target stores, window days, visit lift) with assumptions, measurement plan, and pilot store detail.

---

## Example Insights

- **Frequency ≠ impact:** Speed of service is the #1 theme by volume (13.8% of comments) but price/value shows the deepest NPS gap (-10.9 vs brand).
- **Loyalty lever:** Drink quality rating is the strongest predictor of high revisit intent (5.30× odds per standard-deviation increase).
- **Operational risk:** Speed of service has 64.6% negative comment share and over-indexes among detractors (1.08×).
- **Store concentration:** Hartford Mall, Indianapolis Mall, and Miami Mall rank highest on opportunity score — high traffic with elevated negative feedback.
- **Segment divergence:** Mobile-first guests over-index on mobile app issues; at-risk guests show NPS near -100 with the lowest revisit intent.

---

## Business Impact Estimate

Using default assumptions from `impact_summary.csv` and the top **30** stores in `store_opportunity_ranking.csv`:

| Parameter | Default |
|-----------|---------|
| Target stores | 30 |
| Mean daily transactions | 793 |
| Mean average ticket | $9.18 |
| Improvement window | 90 days |
| Expected repeat-visit lift | 2.0% |

**Estimated incremental revenue: ~$393,034** — exceeds the **$100K+** decision threshold.

Before/after pilot tracking covers NPS, CSAT, revisit intent, negative comment rate, speed-of-service theme frequency, drink consistency complaint rate, and repeat visit behavior. See `reports/executive_memo.md` for recommended actions and limitations.

---

## Resume Bullet Section

Copy-ready bullets for analytics and insights roles:

- Built a Voice of Customer Insights Platform using Python, SQL, and Streamlit to analyze simulated guest survey, review, product, and store-level data for a multi-location coffee brand; classified customer feedback themes, quantified NPS/CSAT impact, and identified top drivers of repeat visit intent.

- Developed a research-style analytics workflow with data validation checks, VoC codebook design, detractor analysis, guest segmentation, logistic regression driver modeling, and executive recommendations tied to a $100K+ business impact case.

- Created an executive dashboard and memo translating open-text guest feedback into prioritized actions for Marketing, Operations, Digital, and Strategy teams.

---

## Acceptance Checklist

Verified end-to-end with `make data`, `make validate`, `make build`, `make test`, and `make app`:

| # | Criterion | Status |
|---|-----------|--------|
| 1 | Repo structure (`src/`, `app/`, `data/`, `outputs/`, `sql/`, `reports/`, `tests/`, `notebooks/`) | Pass |
| 2 | `requirements.txt` | Pass |
| 3 | Synthetic raw datasets generated (5 CSVs + dictionary) | Pass |
| 4 | `validation_summary.csv` produced (32 checks) | Pass |
| 5 | VoC themes classified → `guest_surveys_classified.parquet` | Pass |
| 6 | Processed parquet datasets in `data/processed/` | Pass |
| 7 | Required analytical CSVs in `outputs/tables/` | Pass |
| 8 | DuckDB SQL queries in `sql/` (+ `_duckdb.csv` exports) | Pass |
| 9 | Streamlit app loads all required files | Pass |
| 10 | Dashboard: Executive Readout, VoC Deep Dive, Drivers & Segments, Opportunities | Pass |
| 11 | `executive_memo.md` — data-backed findings (not placeholders) | Pass |
| 12 | `methodology.md` | Pass |
| 13 | Portfolio-ready README | Pass |
| 14 | Default impact case **>$100K** (~$393K at 30 stores / 90 days / 2% lift) | Pass |
| 15 | Results match embedded patterns (speed theme volume, drink-quality driver, mall opportunities) | Pass |
| 16 | No placeholder TODOs in codebase | Pass |

---

## Further Reading

- `reports/executive_memo.md` — business question, key insights, recommended actions, impact sizing
- `reports/methodology.md` — data generation, validation, classification, driver model, opportunity formula
- `reports/voc_codebook.md` — theme definitions and keyword rules
