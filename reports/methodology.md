# Methodology — Consumer Insights Platform

## Overview

This project models a Brand & Guest Insights workflow for a multi-location coffee brand. All inputs are **synthetic** and generated with a fixed random seed (42) for reproducibility.

## Pipeline

```
generate_data → validate_data → classify_voc_themes → analyze_themes
    → driver_analysis → segment_analysis → opportunity_scoring → impact_model
```

DuckDB SQL queries re-aggregate key metrics for auditability.

## 1. Data Generation

- **Stores:** 20–30 locations across four U.S. regions with transaction and ticket proxies
- **Surveys:** 6,000 guest responses with realistic segment/channel skew
- **Comments:** Template-based open text with embedded theme signals

## 2. Data Validation

Checks include schema completeness, value ranges, referential integrity to stores, duplicate IDs, and synthetic-only enforcement. Outputs a JSON validation report and clean parquet files.

## 3. VoC Theme Classification

Rule-based keyword classifier (no paid NLP APIs). Each comment may map to multiple themes; the first match becomes `primary_theme`.

## 4. Theme Impact Analysis

Computes mention volume, average NPS/CSAT/revisit by theme, and gaps vs brand baseline. Priority score blends volume, detractor rate, and NPS gap.

## 5. Satisfaction Driver Modeling

Logistic regression predicts promoter status (NPS ≥ 9) from theme presence and guest context (segment, channel, region, store type). Coefficients indicate directional drivers.

## 6. Segment & Store Analysis

- Segment profiles: NPS, CSAT, theme mix
- Store opportunity scoring: detractor rate, negative sentiment, survey volume, revenue weight

## 7. Impact Sizing

Financial model translates theme-level NPS gaps into revisit lift and recoverable revenue:

- NPS-to-revisit elasticity: 1.8% revisit lift per NPS point
- Recovery rate: 60% of observed NPS gap
- Implementation cost: $85K (staffing + mobile pickup workflow)

Net impact = recoverable revenue − implementation cost. Target threshold: **$100K+**.

## Tools

| Tool | Role |
|------|------|
| pandas / numpy | Data wrangling and aggregation |
| scikit-learn | Driver modeling |
| DuckDB | SQL validation layer |
| matplotlib / plotly | Static and interactive charts |
| Streamlit | Executive exploration app |

## Limitations

- Synthetic data; coefficients and dollar estimates are illustrative
- Keyword classifier will miss nuance vs human coding or LLM labeling
- Impact model uses stated assumptions, not observed causal inference
