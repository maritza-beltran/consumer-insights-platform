# VoC Codebook — Brew & Bloom Coffee Co.

**Data type:** Synthetic (`data_source = synthetic`) | **Seed:** 42 | **Period:** Jan–Jun 2024

Each guest comment receives **one primary theme** and may receive **one optional secondary theme**. Themes are assigned via keyword classification on `comment_text` and validated against generation metadata in `guest_comments.csv`.

---

## speed_of_service

**Definition:** Guest feedback about queue length, counter throughput, or overall service speed during the visit.

**Inclusion criteria:** Comment mentions slow lines, long waits, rush-hour delays, or staffing unable to keep pace.

**Exclusion criteria:** Comments focused only on drive-thru lane mechanics (use `drive_thru_experience`) or only on drink taste (use `drink_consistency`).

**Example keywords:** `line took`, `took forever`, `slow`, `long line`, `waited`, `backed up`, `minutes`

**Example comments:**
- "The line took forever even though there were only three people ahead of me."
- "The latte tasted different than usual, and the line took forever."

---

## drink_consistency

**Definition:** Guest feedback about beverage quality, taste consistency, or variation from prior visits.

**Inclusion criteria:** Comment references drink tasting different, inconsistent preparation, burnt/weak espresso, or milk quality issues.

**Exclusion criteria:** Price complaints without quality mention (use `price_value`); seasonal curiosity without quality judgment (use `seasonal_menu_interest`).

**Example keywords:** `tasted different`, `different than usual`, `inconsistent`, `burnt`, `weak`, `not the same`, `latte tasted`

**Example comments:**
- "The latte tasted different than usual and did not match my last visit."
- "Drink quality feels inconsistent across visits to this location."

---

## order_accuracy

**Definition:** Guest feedback about incorrect orders, missing customizations, or confusing pickup/handoff.

**Inclusion criteria:** Comment mentions wrong item, missing modification, or pickup shelf confusion tied to order fulfillment.

**Exclusion criteria:** Pure wait-time complaints with no accuracy issue (use `speed_of_service`).

**Example keywords:** `order was wrong`, `wrong order`, `incorrect`, `missing`, `pickup shelf`, `confusing`

**Example comments:**
- "My order was wrong and the pickup shelf was confusing."
- "Customization notes were ignored on my mobile order."

---

## staff_friendliness

**Definition:** Guest feedback about employee warmth, helpfulness, greetings, and service recovery.

**Inclusion criteria:** Comment highlights barista/cashier attitude, helpful behavior, or friendly recovery during operational stress.

**Exclusion criteria:** Operational complaints with no staff mention (use speed/mobile/cleanliness themes).

**Example keywords:** `staff was friendly`, `cashier was helpful`, `barista`, `friendly`, `helpful`, `warm`

**Example comments:**
- "The staff was friendly even though the drive-thru was backed up."
- "The store was clean and the cashier was helpful."

---

## cleanliness

**Definition:** Guest feedback about store hygiene, restroom condition, seating area tidiness, and trash management.

**Inclusion criteria:** Comment references sticky tables, messy floors, restroom issues, or positive cleanliness callouts.

**Exclusion criteria:** Staff attitude without cleanliness mention (use `staff_friendliness`).

**Example keywords:** `clean`, `sticky`, `restroom`, `messy`, `trash`, `dirty`, `tidy`

**Example comments:**
- "Tables were sticky and the restroom needed attention."
- "The store was clean and well maintained during a busy afternoon."

---

## mobile_app_issues

**Definition:** Guest feedback about mobile ordering UX, app reliability, pickup timing, and ready notifications.

**Inclusion criteria:** Comment mentions app crashes, order-not-ready on arrival, confusing pickup flow, or notification timing.

**Exclusion criteria:** Drive-thru lane issues without app mention (use `drive_thru_experience`).

**Example keywords:** `mobile ordering`, `mobile order`, `app`, `not ready`, `pickup timing`, `arrived`, `crashed`

**Example comments:**
- "Mobile ordering was easy, but my drink was not ready when I arrived."
- "Pickup timing was off and the ready notification came late."

---

## rewards_value

**Definition:** Guest feedback about loyalty program perceived value, points posting, tier benefits, and redemption ease.

**Inclusion criteria:** Comment references rewards feeling less valuable, points not posting, or member perk satisfaction.

**Exclusion criteria:** General price complaints unrelated to loyalty (use `price_value`).

**Example keywords:** `rewards program`, `points`, `not as valuable`, `redeem`, `tier`, `member`

**Example comments:**
- "The rewards program does not feel as valuable as it used to."
- "Birthday reward made me feel valued as a member."

---

## price_value

**Definition:** Guest feedback about menu pricing, portion size vs cost, and promotional value perception.

**Inclusion criteria:** Comment mentions high prices, poor value for size, or positive deal/promo satisfaction.

**Exclusion criteria:** Loyalty-specific value complaints (use `rewards_value`).

**Example keywords:** `price feels`, `expensive`, `high for the size`, `deal`, `discount`, `value`

**Example comments:**
- "I like the seasonal drinks, but the price feels high for the size."
- "Prices feel high for the cup size I received."

---

## seasonal_menu_interest

**Definition:** Guest feedback about seasonal beverage curiosity, trial intent, menu variety, and repeat interest in LTO items.

**Inclusion criteria:** Comment references seasonal drinks, limited-time offers, menu exploration, or repeat intent for seasonal items.

**Exclusion criteria:** Sweetness or quality complaints on seasonal items without menu-interest framing (use `drink_consistency` or product feedback).

**Example keywords:** `seasonal`, `seasonal drink`, `seasonal cold brew`, `pumpkin`, `limited`, `new drink`

**Example comments:**
- "I like the seasonal drinks and wanted to try the new cold brew."
- "Loved the new seasonal drink and would order again."

---

## drive_thru_experience

**Definition:** Guest feedback specific to drive-thru lane flow, speaker clarity, window handoff, and lane backup.

**Inclusion criteria:** Comment explicitly references drive-thru lane, window, speaker, or drive-thru handoff experience.

**Exclusion criteria:** Generic speed complaints at counter (use `speed_of_service`).

**Example keywords:** `drive-thru`, `drive thru`, `window`, `lane`, `speaker`, `handoff`, `backed up`

**Example comments:**
- "Drive-thru lane was backed up and the speaker was hard to hear."
- "The staff was friendly even though the drive-thru was backed up."

---

## general_experience (fallback)

**Definition:** Neutral or ambiguous comments that do not match any theme keyword rules.

**Inclusion criteria:** No keyword match above threshold.

**Exclusion criteria:** Any comment with a clear theme signal.

**Example comments:**
- "Standard coffee visit with no major issues."

---

## Embedded Synthetic Patterns

| Pattern | Signal in data |
|---------|----------------|
| Drive-thru stores → speed complaints | Higher `speed_of_service` + `drive_thru_experience` theme weights |
| Mobile-first guests → app/pickup complaints | Higher `mobile_app_issues` weights; lower `mobile_app_experience_rating` |
| Loyalty regulars → rewards sensitivity | Higher `rewards_value` weights; `rewards_satisfaction` drives revisit |
| Price-sensitive guests → price/value complaints | Higher `price_value` weights; lower `price_value_perception` |
| Seasonal explorers → trial + mixed repeat | High seasonal product trial; variable `repeat_purchase_intent` |
| Airport/mall → lower CSAT, higher traffic | Higher `avg_daily_transactions`; CSAT penalty in surveys |
| Drink consistency → lower revisit | Low `drink_quality_rating` strongly reduces `revisit_intent` |
| Wait time → lower NPS/CSAT | Low `wait_time_rating` penalizes NPS and CSAT |
| Staff friendliness → CSAT lift | High `staff_friendliness_rating` boosts CSAT despite ops issues |
| Sweetness complaints → lower seasonal repeat | `too_sweet` on seasonal products reduces `repeat_purchase_intent` |
