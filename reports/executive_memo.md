# Executive Memo: Voice of Customer Analysis

**Brand:** Brew & Bloom Coffee Co.  
**Period:** January–June 2024 | **Coverage:** 90 U.S. stores | **Surveys:** 12,000  
**Data source:** Simulated portfolio dataset for analytics demonstration

---

## Business Question

What are the most important guest experience issues affecting satisfaction, loyalty, and repeat visit intent?

---

## Data and Methodology

This analysis combines five simulated datasets: guest surveys (NPS, CSAT, revisit intent, experience ratings), open-ended guest comments, product feedback, store metadata, and loyalty visit behavior. All inputs were validated through **33 automated checks** (row counts, referential integrity, score ranges, and date coverage) before analysis.

Guest comments were classified into **10 VoC themes** using a rule-based keyword classifier (`classify_voc_themes.py`). Theme performance was summarized by volume, negative comment share, and average NPS, CSAT, and revisit intent. Detractor comments were analyzed separately to identify themes that over-index among low-NPS guests.

A **logistic regression driver model** predicted high revisit intent (`revisit_intent >= 4`) from eight standardized experience ratings. Model performance: **78.7% accuracy**, **88.6% ROC-AUC**. Guests were segmented by behavioral profile; segment-level KPIs and theme pain points were cross-tabulated. **Store opportunity scores** (`store_opportunity_ranking.csv`) combined negative-theme rate, NPS gap, revisit-intent gap, and traffic weight to rank pilot locations. Financial impact was sized from the top-ranked stores using transaction volume, average ticket, a 90-day window, and an assumed 2% repeat-visit lift.

**Brand baseline:** NPS **-7.0**, CSAT **3.88**, revisit intent **3.17**.

---

## Key Insight 1: The most frequent issue is not always the most damaging issue

**Speed of service** is the most-mentioned theme (**1,586 comments**, **13.8%** of classified feedback) and carries a high negative share (**64.6%**). Guests citing wait-time friction average NPS **-14.5** and revisit intent **3.09** — below brand averages but not the deepest gap in the portfolio.

By contrast, **price/value** appears in only **425 comments** (**3.7%** share) yet shows the largest NPS drag (**-18.6**, **-11.9** points vs brand) and among the lowest revisit intent (**3.11**). **General experience** and **order accuracy** also punch above their weight: order accuracy ranks eighth in volume but **59.9%** of mentions are negative.

**Implication:** Volume-based prioritization alone would over-invest in throughput while under-addressing value perception and order execution — themes that disproportionately erode loyalty despite lower mention counts.

| Theme | Comment share | NPS gap vs brand | Revisit gap vs brand |
|-------|---------------|------------------|----------------------|
| Speed of service | 13.8% (highest) | -7.8 | -0.08 |
| Price/value | 3.7% | -11.9 (worst) | -0.06 |
| Order accuracy | 8.9% | +0.9 | -0.03 |
| Rewards value | 9.9% | +15.7 | +0.24 |

---

## Key Insight 2: Drink consistency and speed of service are the largest loyalty risks

**Driver analysis** ranks **drink quality rating** as the strongest predictor of high revisit intent (odds ratio **3.32** per one standard-deviation increase — roughly **3.3×** the odds of declaring intent to return). **Staff friendliness** (1.80×) and **mobile app experience** (1.57×) follow. Drink consistency in open text maps directly to this lever: **1,182 comments** with **34.8%** negative sentiment and NPS **-3.5**.

**Speed of service** is the operational counterpart. It is the top detractor theme by volume, over-indexes among detractors (**1.16×** vs all comments), and pairs with wait-time ratings in the driver model (8th-ranked but still material at **1.29×** odds). Together, inconsistent drinks and slow service create a compounding loyalty risk: guests who doubt product quality *and* wait longer are least likely to return.

---

## Key Insight 3: The highest-value opportunity is concentrated in high-traffic stores with elevated negative feedback

`store_opportunity_ranking.csv` ranks all **90** locations on a composite score blending negative experience rate, NPS gap, revisit-intent gap, and traffic weight. The top tier is dominated by **mall and airport** formats with high daily transactions and **speed of service** as the leading negative theme:

| Rank | Store | Type | Opportunity score | Avg daily txn | NPS | Top negative theme |
|------|-------|------|-------------------|---------------|-----|-------------------|
| 1 | Hartford Mall (BB-047) | mall | 0.79 | 955 | -14.9 | speed_of_service |
| 2 | Miami Mall (BB-068) | mall | 0.77 | 890 | -8.6 | speed_of_service |
| 3 | Portland Airport (BB-067) | airport | 0.76 | 980 | -12.7 | speed_of_service |
| 4 | Indianapolis Mall (BB-001) | mall | 0.72 | 808 | -6.3 | speed_of_service |
| 9 | Philadelphia Airport (BB-017) | airport | 0.69 | 813 | -9.6 | mobile_app_issues |

High traffic amplifies even modest experience gaps into large guest-volume exposure. Among **drive-thru** locations, **Seattle Drive Thru (BB-043)** shows the deepest NPS underperformance in the portfolio (NPS **-23.2**, **-16.2** points vs brand), followed by **Philadelphia Drive Thru (BB-041)** (NPS **-22.1**).

---

## Recommended Actions

Prioritized using `store_opportunity_ranking.csv`, segment pain points, and driver importance:

1. **Improve speed of service in priority drive-thru stores.** Deploy peak-hour staffing and queue-management pilots at ranked drive-thru locations where **speed_of_service** is the top negative theme — including **Phoenix Drive Thru** (NPS **-17.9**), **Boston Drive Thru** (NPS **-17.4**), and **Chicago Drive Thru** (NPS **-16.0**). Align to the store-level recommended action: *Pilot peak-hour staffing and queue management in priority stores.*

2. **Standardize drink consistency in low-NPS markets.** Launch recipe-adherence audits and barista retraining in markets with the steepest NPS gaps and drink-quality friction — e.g. **Seattle Drive Thru** (NPS **-23.2**, top theme **drink_consistency**), **Indianapolis Airport** (NPS **-14.0**), and **Phoenix Mall** locations (NPS **-14.4** / **-10.8**). This targets the #1 revisit-intent driver (drink quality, **3.32×** odds).

3. **Improve mobile order pickup reliability for mobile-first guests.** **Mobile-first guests** over-index on **mobile_app_issues** (NPS **-1.4**, revisit **3.10**). Prioritize airport and high-digital stores where mobile is the dominant pain theme — **Philadelphia Airport (BB-017)** ranks **9th** with **mobile_app_issues** as top negative theme. Action: *Review mobile pickup timing and app-to-store handoff.*

---

## Estimated Impact

Using default assumptions from `impact_summary.csv` and the top **30** stores in `store_opportunity_ranking.csv`:

| Parameter | Default |
|-----------|---------|
| Target stores | 30 (highest opportunity score) |
| Mean daily transactions | 796 |
| Mean average ticket | $9.31 |
| Improvement window | 90 days |
| Expected repeat-visit lift | 2.0% |

**Estimated incremental revenue: ~$400,209** over the 90-day window.

This exceeds the **$100K+** decision threshold and supports a funded pilot. Upside scales with store count, traffic, ticket size, and realized visit-lift — adjustable in the Streamlit impact calculator on Page 4. Scenario grids are in `impact_sensitivity.csv`.

---

## Measurement Plan

Run a **before/after pilot** in target stores with **matched control** locations for the 90-day improvement window. Track weekly:

- **NPS**, **CSAT**, and **revisit intent** (survey outcomes)
- **Negative comment rate** (share of classified comments flagged as negative experience)
- **Speed-of-service theme frequency** (share of comments classified to `speed_of_service`)
- **Drink consistency complaint rate** (negative share among `drink_consistency` comments)
- **Repeat visit behavior** (loyalty visit counts reconciled to POS transaction data)

Compare pilot vs control deltas at weeks 4, 8, and 12. Reconcile survey-based metrics against store-level transaction volume to confirm whether experience improvements translate into visit frequency.

---

## Assumptions and Limitations

- **Data is simulated.** All guest, comment, and transaction inputs are synthetically generated with a fixed random seed for reproducibility. Dollar estimates and theme distributions are illustrative, not observed operational results.
- **Rule-based theme classification is explainable but less nuanced than human coding or advanced NLP.** Keyword matching may miss sarcasm, multi-issue comments, or emerging language. Confidence scores reflect keyword hit counts, not probabilistic model certainty.
- **Logistic regression identifies association, not causality.** Driver coefficients show which experience ratings co-occur with high revisit intent; they do not prove that improving a rating will cause more repeat visits.
- **Causal impact requires a controlled pilot or test/control design.** The $400K estimate assumes a 2% repeat-visit lift from experience improvements. Validating that lift — and attributing it to specific interventions — requires the measurement plan above with matched controls, not observational modeling alone.

---

*Supporting tables: `outputs/tables/store_opportunity_ranking.csv`, `theme_summary.csv`, `theme_impact.csv`, `driver_importance.csv`, `impact_summary.csv`, `impact_sensitivity.csv`. Methodology detail: `reports/methodology.md`.*
