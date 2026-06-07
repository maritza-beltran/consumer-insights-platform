WITH store_metrics AS (
    SELECT
        s.store_id,
        s.store_name,
        s.region,
        s.store_type,
        COUNT(*) AS survey_count,
        ROUND(AVG(g.nps), 2) AS avg_nps,
        ROUND(AVG(g.csat), 2) AS avg_csat,
        ROUND(100.0 * AVG(CASE WHEN g.nps <= 6 THEN 1.0 ELSE 0.0 END), 1) AS detractor_pct,
        ROUND(100.0 * AVG(CASE WHEN g.sentiment_label = 'negative' THEN 1.0 ELSE 0.0 END), 1) AS negative_sentiment_pct,
        ROUND(
            100.0 * (
                AVG(CASE WHEN g.nps >= 9 THEN 1.0 ELSE 0.0 END)
                - AVG(CASE WHEN g.nps <= 6 THEN 1.0 ELSE 0.0 END)
            ),
            1
        ) AS store_nps
    FROM guest_surveys g
    JOIN stores s ON g.store_id = s.store_id
    GROUP BY s.store_id, s.store_name, s.region, s.store_type
)
SELECT
    m.*,
    st.avg_daily_transactions,
    st.avg_ticket,
    ROUND(st.avg_daily_transactions * 30 * st.avg_ticket, 2) AS monthly_revenue_usd,
    ROUND(
        m.detractor_pct / 100.0 * 0.4
        + m.negative_sentiment_pct / 100.0 * 0.35
        + (m.survey_count::DOUBLE / MAX(m.survey_count) OVER ()) * 0.25,
        4
    ) AS opportunity_score
FROM store_metrics m
JOIN stores st ON m.store_id = st.store_id
ORDER BY opportunity_score DESC;
