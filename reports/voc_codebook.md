# VoC Codebook — Brew & Bloom Coffee Co.

**Data type:** Synthetic (`data_source = synthetic`) | **Seed:** 42 | **Period:** Jan–Jun 2024

## Datasets

| File | Rows (approx) | Grain |
|------|---------------|-------|
| `stores.csv` | 90 | Store |
| `guest_surveys.csv` | 12,000 | Survey response |
| `guest_comments.csv` | ~11,500 | Comment (linked to survey) |
| `product_feedback.csv` | ~8,000 | Product trial per survey |
| `loyalty_behavior.csv` | 12,000 | Guest |

## Guest Segments

`loyalty_regular` · `occasional_guest` · `mobile_first_guest` · `price_sensitive_guest` · `seasonal_product_explorer` · `at_risk_guest`

## Visit Channels

`in_store` · `drive_thru` · `mobile_order` · `delivery`

## Experience Ratings (1–5)

`wait_time_rating` · `drink_quality_rating` · `order_accuracy_rating` · `staff_friendliness_rating` · `cleanliness_rating` · `mobile_app_experience_rating` · `rewards_satisfaction` · `price_value_perception`

## VoC Theme Taxonomy

`wait_time` · `drink_quality` · `order_accuracy` · `staff_friendliness` · `cleanliness` · `mobile_app` · `rewards_program` · `price_value` · `seasonal_menu` · `food_quality` · `general_experience`

## Score Ranges

- **nps:** 0–10
- **csat / revisit_intent / experience ratings:** 1–5
- **sentiment_label:** positive · neutral · negative
