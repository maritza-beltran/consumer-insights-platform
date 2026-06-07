-- Theme-level impact on guest satisfaction metrics
WITH theme_mentions AS (
    SELECT
        survey_id,
        UNNEST(themes) AS theme,
        nps_score,
        csat_score,
        revisit_intent,
        comment_sentiment
    FROM guest_surveys
),
brand_avg AS (
    SELECT
        AVG(nps_score) AS brand_avg_nps,
        AVG(csat_score) AS brand_avg_csat,
        AVG(revisit_intent) AS brand_avg_revisit
    FROM guest_surveys
)
SELECT
    t.theme,
    COUNT(*) AS mention_count,
    ROUND(AVG(t.nps_score), 2) AS avg_nps,
    ROUND(AVG(t.csat_score), 2) AS avg_csat,
    ROUND(AVG(t.revisit_intent), 2) AS avg_revisit,
    ROUND(100.0 * AVG(CASE WHEN t.nps_score <= 6 THEN 1.0 ELSE 0.0 END), 1) AS detractor_pct,
    ROUND(100.0 * AVG(CASE WHEN t.comment_sentiment = 'negative' THEN 1.0 ELSE 0.0 END), 1) AS negative_sentiment_pct,
    ROUND(AVG(t.nps_score) - b.brand_avg_nps, 2) AS nps_gap_vs_brand
FROM theme_mentions t
CROSS JOIN brand_avg b
GROUP BY t.theme, b.brand_avg_nps, b.brand_avg_csat, b.brand_avg_revisit
ORDER BY mention_count DESC;
