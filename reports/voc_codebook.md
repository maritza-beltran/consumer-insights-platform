# VoC Codebook — Brew & Bloom Coffee Co.

**Data type:** Synthetic (clearly labeled `data_source = synthetic`)  
**Brand:** Brew & Bloom Coffee Co.  
**Random seed:** 42

## Files

| File | Description |
|------|-------------|
| `data/raw/stores.csv` | Store master with region, type, and revenue proxies |
| `data/raw/guest_surveys.csv` | Guest survey responses with open-ended comments |
| `data/processed/guest_surveys_classified.parquet` | Surveys with VoC theme tags |

## Survey Fields

| Field | Type | Description |
|-------|------|-------------|
| `survey_id` | string | Unique survey identifier |
| `guest_id` | string | Anonymized guest identifier |
| `survey_date` | date | Survey response date |
| `store_id` | string | FK to stores |
| `region` | string | Northeast, Southeast, Midwest, West |
| `store_type` | string | urban flagship, suburban, airport, campus, drive-thru focused |
| `channel` | string | in-store, drive-thru, mobile order |
| `segment` | string | loyalist, occasional, new_guest, at_risk |
| `nps_score` | int | 0–10 Net Promoter Score item |
| `csat_score` | int | 1–5 overall satisfaction |
| `revisit_intent` | int | 1–5 likelihood to revisit |
| `comment_text` | string | Open-ended guest feedback |
| `data_source` | string | Always `synthetic` |

## VoC Theme Taxonomy

| Theme | Definition | Example cues |
|-------|------------|--------------|
| `speed_of_service` | Throughput and line speed | slow, line, rush |
| `product_quality` | Beverage and food quality | burnt, stale, taste |
| `cleanliness` | Store hygiene | restroom, messy, sticky |
| `staff_friendliness` | Service warmth | barista, greet, friendly |
| `value_for_money` | Price perception | price, deal, expensive |
| `ambiance` | In-store environment | music, seating, lighting |
| `mobile_app` | Digital ordering UX | app, crashed, pickup |
| `loyalty_program` | Rewards program | points, tier, redeem |
| `menu_variety` | Menu breadth | dairy-free, seasonal, options |
| `wait_time` | Order fulfillment delay | minutes, staffing, handoff |
| `general_experience` | No specific theme matched | neutral comments |

## Sentiment Labels

- **positive:** net positive language cues in comment
- **negative:** net negative language cues in comment
- **neutral:** balanced or ambiguous language

## NPS Categories

- **promoter:** score 9–10
- **passive:** score 7–8
- **detractor:** score 0–6
