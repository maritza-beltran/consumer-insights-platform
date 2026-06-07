WITH theme_mentions AS (
    SELECT
        survey_id,
        UNNEST(themes) AS theme,
        nps,
        csat,
        revisit_intent,
        sentiment_label
    FROM guest_surveys
),
brand_avg AS (
    SELECT AVG(nps) AS brand_avg_nps FROM guest_surveys
)
SELECT
    t.theme,
    COUNT(*) AS mention_count,
    ROUND(AVG(t.nps), 2) AS avg_nps,
    ROUND(AVG(t.csat), 2) AS avg_csat,
    ROUND(AVG(t.revisit_intent), 2) AS avg_revisit,
    ROUND(100.0 * AVG(CASE WHEN t.nps <= 6 THEN 1.0 ELSE 0.0 END), 1) AS detractor_pct,
    ROUND(100.0 * AVG(CASE WHEN t.sentiment_label = 'negative' THEN 1.0 ELSE 0.0 END), 1) AS negative_sentiment_pct,
    ROUND(AVG(t.nps) - b.brand_avg_nps, 2) AS nps_gap_vs_brand
FROM theme_mentions t
CROSS JOIN brand_avg b
GROUP BY t.theme, b.brand_avg_nps
ORDER BY mention_count DESC;
