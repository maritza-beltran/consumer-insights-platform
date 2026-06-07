-- Store-level NPS, complaint rate, top negative theme, and opportunity score.
WITH brand AS (
    SELECT
        ROUND(
            100.0 * (
                AVG(CASE WHEN nps >= 9 THEN 1.0 ELSE 0.0 END)
                - AVG(CASE WHEN nps <= 6 THEN 1.0 ELSE 0.0 END)
            ),
            1
        ) AS brand_nps,
        ROUND(AVG(revisit_intent), 4) AS brand_revisit_intent
    FROM guest_surveys
),
store_base AS (
    SELECT
        g.store_id,
        g.store_name,
        g.market,
        g.region,
        g.store_type,
        st.avg_daily_transactions,
        st.avg_ticket,
        COUNT(*) AS survey_count,
        ROUND(
            100.0 * (
                AVG(CASE WHEN g.nps >= 9 THEN 1.0 ELSE 0.0 END)
                - AVG(CASE WHEN g.nps <= 6 THEN 1.0 ELSE 0.0 END)
            ),
            1
        ) AS store_nps,
        ROUND(AVG(g.csat), 4) AS store_csat,
        ROUND(AVG(g.revisit_intent), 4) AS store_revisit_intent,
        ROUND(AVG(CASE WHEN g.is_negative_experience THEN 1.0 ELSE 0.0 END), 4) AS complaint_rate
    FROM guest_surveys g
    JOIN stores st ON g.store_id = st.store_id
    GROUP BY
        g.store_id, g.store_name, g.market, g.region, g.store_type,
        st.avg_daily_transactions, st.avg_ticket
),
negative_theme AS (
    SELECT
        store_id,
        primary_theme AS top_negative_theme,
        ROW_NUMBER() OVER (
            PARTITION BY store_id
            ORDER BY COUNT(*) DESC
        ) AS theme_rank
    FROM guest_surveys
    WHERE is_negative_experience
    GROUP BY store_id, primary_theme
),
scored AS (
    SELECT
        s.*,
        b.brand_nps,
        b.brand_revisit_intent,
        ROUND(s.store_nps - b.brand_nps, 4) AS nps_gap,
        ROUND(s.store_revisit_intent - b.brand_revisit_intent, 4) AS revisit_intent_gap,
        ROUND(
            s.avg_daily_transactions::DOUBLE
            / MAX(s.avg_daily_transactions) OVER (),
            4
        ) AS traffic_weight,
        COALESCE(nt.top_negative_theme, 'general_experience') AS top_negative_theme
    FROM store_base s
    CROSS JOIN brand b
    LEFT JOIN negative_theme nt
        ON s.store_id = nt.store_id
       AND nt.theme_rank = 1
),
indexed AS (
    SELECT
        *,
        CASE
            WHEN MAX(complaint_rate) OVER () = MIN(complaint_rate) OVER () THEN 0.5
            ELSE (complaint_rate - MIN(complaint_rate) OVER ())
                / (MAX(complaint_rate) OVER () - MIN(complaint_rate) OVER ())
        END AS negative_theme_rate_index,
        CASE
            WHEN MAX(-nps_gap) OVER () = MIN(-nps_gap) OVER () THEN 0.5
            ELSE ((-nps_gap) - MIN(-nps_gap) OVER ())
                / (MAX(-nps_gap) OVER () - MIN(-nps_gap) OVER ())
        END AS nps_gap_index,
        CASE
            WHEN MAX(-revisit_intent_gap) OVER () = MIN(-revisit_intent_gap) OVER () THEN 0.5
            ELSE ((-revisit_intent_gap) - MIN(-revisit_intent_gap) OVER ())
                / (MAX(-revisit_intent_gap) OVER () - MIN(-revisit_intent_gap) OVER ())
        END AS revisit_intent_gap_index
    FROM scored
)
SELECT
    store_id,
    store_name,
    market,
    region,
    store_type,
    avg_daily_transactions,
    avg_ticket,
    survey_count,
    store_nps,
    store_csat,
    store_revisit_intent,
    complaint_rate,
    top_negative_theme,
    nps_gap,
    revisit_intent_gap,
    traffic_weight,
    ROUND(
        0.35 * negative_theme_rate_index
        + 0.25 * nps_gap_index
        + 0.20 * revisit_intent_gap_index
        + 0.20 * traffic_weight,
        4
    ) AS opportunity_score
FROM indexed
ORDER BY opportunity_score DESC;
