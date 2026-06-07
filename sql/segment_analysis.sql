SELECT
    guest_segment,
    COUNT(*) AS survey_count,
    ROUND(AVG(nps), 2) AS avg_nps,
    ROUND(AVG(csat), 2) AS avg_csat,
    ROUND(AVG(revisit_intent), 2) AS avg_revisit_intent,
    ROUND(100.0 * AVG(CASE WHEN nps >= 9 THEN 1.0 ELSE 0.0 END), 1) AS promoter_pct,
    ROUND(100.0 * AVG(CASE WHEN nps <= 6 THEN 1.0 ELSE 0.0 END), 1) AS detractor_pct,
    ROUND(
        100.0 * (
            AVG(CASE WHEN nps >= 9 THEN 1.0 ELSE 0.0 END)
            - AVG(CASE WHEN nps <= 6 THEN 1.0 ELSE 0.0 END)
        ),
        1
    ) AS nps,
    ROUND(100.0 * AVG(CASE WHEN sentiment_label = 'negative' THEN 1.0 ELSE 0.0 END), 1) AS negative_comment_pct
FROM guest_surveys
GROUP BY guest_segment
ORDER BY nps ASC;
