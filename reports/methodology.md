# Methodology — Consumer Insights Platform

## Overview

This project models a Brand & Guest Insights workflow for **Brew & Bloom Coffee Co.** All inputs are **synthetic**, generated with a fixed random seed (`RANDOM_SEED = 42`) for reproducibility. The pipeline produces validated parquet files, CSV analytic tables, DuckDB SQL exports, and a Streamlit dashboard that reads precomputed outputs only.

```
generate_data → validate_data → classify_voc_themes → analyze_themes
    → driver_analysis → segment_analysis → opportunity_scoring → impact_model
```

---

## 1. Data Generation Logic

Implemented in `src/generate_data.py`. Five datasets are written to `data/raw/`:

| Dataset | Generator | Key logic |
|---------|-----------|-----------|
| **stores** | `build_stores()` | 90 locations across 4 regions and 6 store types; traffic and ticket drawn from type-specific ranges (mall/airport higher volume) |
| **guest_surveys** | `build_surveys()` | 12,000 responses; store selection weighted by `avg_daily_transactions`; segment/channel mix varies by store type |
| **guest_comments** | `build_comments()` | ~96% survey linkage; template-based text with embedded theme signals |
| **product_feedback** | `build_product_feedback()` | Product trial and rating records tied to surveys |
| **loyalty_behavior** | `build_loyalty_behavior()` | Visit frequency and spend proxies per guest |

### Survey outcome generation

1. **Experience ratings** (1–5): drawn from segment-specific baselines with adjustments for store type and channel (e.g. drive-thru and mall/airport locations depress wait-time and CSAT).
2. **NPS** (0–10): anchored to segment profile, penalized for low wait-time ratings.
3. **CSAT** (1–5): mean of experience ratings with staff-friendliness and store-type adjustments.
4. **Revisit intent** (1–5): derived from CSAT, drink quality, rewards satisfaction, and mobile-app experience by segment.

### Comment generation

- **Primary/secondary themes** sampled from weighted distributions (`_theme_weights`) that over-index speed/drive-thru themes at drive-thru stores, mobile themes for `mobile_first_guest` / `mobile_order`, price themes for `price_sensitive_guest`, etc.
- **Comment text** composed from theme-specific templates (`THEME_COMMENTS`) with optional secondary snippets; positive sentiment applies light text substitutions.
- **Sentiment label** sampled with higher negative probability for high-churn segments (`at_risk_guest`, `price_sensitive_guest`).

All records include `data_source = "synthetic"`.

---

## 2. Embedded Assumptions

| Area | Assumption |
|------|------------|
| **Traffic proxy** | `avg_daily_transactions` and `avg_ticket` stand in for POS revenue capacity |
| **Survey representativeness** | Store survey volume is proportional to traffic weight, not a census |
| **Comment coverage** | Not every survey produces a comment (~4% skip rate in generation) |
| **Theme weights in data** | Synthetic comment themes are biased by store type, segment, and channel to create realistic pain-point patterns |
| **Impact sizing** | 2% repeat-visit lift over 90 days at top 30 opportunity stores (see §7) |
| **High revisit intent** | Binary threshold: `revisit_intent >= 4` |
| **Standard NPS** | `(% promoters with nps ≥ 9 − % detractors with nps ≤ 6) × 100` |

---

## 3. Validation Approach

Implemented in `src/validate_data.py`. On each build:

1. **Schema checks** — required columns present for all five datasets.
2. **Row-count bounds** — compared to `EXPECTED_ROW_COUNTS` in `config.py`.
3. **Value ranges** — NPS 0–10, CSAT/revisit 1–5, experience ratings 1–5, valid enums for region/segment/channel/sentiment.
4. **Referential integrity** — survey and comment `store_id` values exist in stores; comment `survey_id` links to surveys.
5. **Duplicate detection** — unique IDs for stores, surveys, comments.
6. **Synthetic-only enforcement** — `data_source` must equal `"synthetic"`.
7. **Date coverage** — records fall within `STUDY_START`–`STUDY_END` (Jan–Jun 2024).
8. **Quality metrics** — brand NPS, average CSAT, revisit intent, comment linkage rate.

Outputs:

- `data/processed/validation_report.json` — pass/fail status, check counts, flagged records
- `data/processed/*_clean.parquet` — cleaned datasets for downstream steps
- `outputs/tables/validation_summary.csv` — tabular check log

Current run: **33 checks**, **0 failures**, **3 warnings**, **45 flagged records** (suspicious but retained).

---

## 4. Theme Classification Approach

Implemented in `src/classify_voc_themes.py` using keyword dictionaries in `config.THEME_KEYWORDS`.

### Rules (no ML, no paid NLP APIs)

1. Normalize comment text (lowercase, collapse whitespace).
2. Score each of **10 VoC themes** by counting keyword substring hits.
3. Rank themes by score; break ties by `VOC_THEMES` order.
4. Assign **primary_theme** = top scorer; **secondary_theme** = runner-up if score > 0.
5. If no keywords match → fallback `general_experience` with confidence **0.35**.
6. **theme_confidence** mapped from hit counts (0.60 for one hit, up to 0.95 with secondary support).
7. **is_negative_experience** — `True` if `sentiment_label == "negative"`, else compare negative vs positive language cue lists in the comment text.

Classified surveys are saved to `data/processed/guest_surveys_classified.parquet` and aggregated in `analyze_themes.py` to produce `theme_summary.csv`, `theme_impact.csv`, and `detractor_theme_analysis.csv`.

### Theme priority ranking (`impact_rank`)

Intervention priority is **not** comment volume alone. `theme_priority_score()` in `src/metrics.py` blends:

| Signal | Weight |
|--------|--------|
| Comment frequency (`share_of_comments`) | 15% |
| Negative sentiment (`negative_share`) | 25% |
| NPS drag below brand | 25% |
| CSAT drag below brand | 15% |
| Revisit-intent drag below brand | 20% |

`impact_rank` in `theme_impact.csv` sorts themes by this composite score (1 = highest priority).

---

## 5. Driver Model Approach

Implemented in `src/driver_analysis.py`.

| Element | Specification |
|---------|---------------|
| **Target** | `high_revisit_intent = 1` if `revisit_intent >= 4`, else `0` |
| **Features** | Eight experience ratings: wait time, drink quality, order accuracy, staff friendliness, cleanliness, mobile app, rewards satisfaction, price-value perception |
| **Preprocessing** | `StandardScaler` (features standardized before fitting) |
| **Model** | `LogisticRegression(max_iter=1000, class_weight="balanced", random_state=42)` |
| **Split** | 75/25 train/test, stratified |
| **Outputs** | `driver_importance.csv` (coefficients, odds ratios, rank, plain-English interpretation); `model_metrics.csv` |

**Interpretation:** Odds ratios express the multiplicative change in odds of high revisit intent per one standard-deviation increase in each rating. This is **associative**, not causal.

Current model metrics: accuracy **78.7%**, precision **69.3%**, recall **81.5%**, ROC-AUC **88.6%**.

---

## 6. Opportunity Score Formula

Implemented in `src/opportunity_scoring.py`. Each store receives:

### Component metrics

- `negative_theme_rate` — mean of `is_negative_experience` across store surveys
- `nps_gap` — store NPS minus brand NPS (`standard_nps`)
- `revisit_intent_gap` — store mean revisit intent minus brand mean
- `traffic_weight` — `avg_daily_transactions / max(avg_daily_transactions)` across portfolio
- `top_negative_theme` — most frequent primary theme among negative-experience comments

### Normalized indices (min–max to 0–1)

- `negative_theme_rate_index` = minmax(`negative_theme_rate`)
- `nps_gap_index` = minmax(`−nps_gap`) — worse NPS → higher index
- `revisit_intent_gap_index` = minmax(`−revisit_intent_gap`) — lower revisit → higher index

### Composite opportunity score

```
opportunity_score =
    0.35 × negative_theme_rate_index
  + 0.25 × nps_gap_index
  + 0.20 × revisit_intent_gap_index
  + 0.20 × traffic_weight
```

Stores are sorted descending; output in `outputs/tables/store_opportunity_ranking.csv` with store-level `recommended_action` mapped from `THEME_RECOMMENDED_ACTIONS`.

### Supplemental store upside (informational)

```
estimated_90_day_upside =
    avg_daily_transactions × avg_ticket × 90 × opportunity_score × 0.08
```

This is a relative sizing helper, distinct from the portfolio impact model in §7.

---

## 7. Impact Sizing

Implemented in `src/impact_model.py` using top stores from `store_opportunity_ranking.csv`.

```
estimated_incremental_revenue =
    target_store_count
  × avg_daily_transactions   (mean of top N stores)
  × avg_ticket                 (mean of top N stores)
  × improvement_window_days
  × expected_repeat_visit_lift
```

**Defaults** (`config.IMPACT_DEFAULTS`):

| Parameter | Value |
|-----------|-------|
| `target_store_count` | 30 |
| `improvement_window_days` | 90 |
| `expected_repeat_visit_lift` | 2% (0.02) |
| `min_incremental_revenue_usd` | $100,000 |

With current data: **~$400,209** incremental revenue — exceeds the $100K threshold.

`impact_sensitivity.csv` adds a simple scenario grid for 10, 20, and 30 target stores at 1%, 2%, and 3% repeat-visit lift. This makes the business case easier to pressure-test.

---

## 8. Measurement Plan

Defined in `config.measurement_plan()`. Before/after pilot tracking in treatment stores vs matched controls:

- NPS, CSAT, revisit intent
- Negative comment rate
- Speed-of-service theme frequency
- Drink consistency complaint rate
- Repeat visit behavior (reconciled to POS transaction counts weekly)

---

## 9. Limitations

1. **Synthetic data** — Patterns and magnitudes are designed for demonstration; they should not be treated as Brew & Bloom operational facts.
2. **Rule-based classification** — Explainable and auditable, but less nuanced than human coding, LLM labeling, or supervised NLP. Misses context, irony, and novel phrasing.
3. **Keyword collision** — Shared terms (e.g. "pickup shelf") can map to multiple themes; primary theme follows hit-count ranking only.
4. **Driver model association** — Logistic regression identifies covariation between experience ratings and revisit intent; it does not establish that changing one rating causes revisit behavior to change.
5. **No causal inference in impact model** — The 2% lift is an explicit assumption, not an econometric estimate from the data.
6. **Causal validation requires experimentation** — Credible attribution needs a controlled pilot (treatment vs matched control), not observational scoring alone.
7. **Store opportunity weighting** — The 35/25/20/20 score weights are judgment-based; sensitivity to alternative weights is not modeled here.

---

## Tools

| Tool | Role |
|------|------|
| pandas / numpy | Data wrangling and aggregation |
| scikit-learn | Logistic driver model |
| DuckDB | SQL validation and export layer (`sql/*.sql`) |
| matplotlib / plotly | Static charts and Streamlit visualizations |
| Streamlit | Executive exploration app (`app/streamlit_app.py`) |
| Faker | Synthetic store/market name generation |

---

*Code references: `src/generate_data.py`, `src/validate_data.py`, `src/classify_voc_themes.py`, `src/driver_analysis.py`, `src/opportunity_scoring.py`, `src/impact_model.py`, `src/config.py`.*
