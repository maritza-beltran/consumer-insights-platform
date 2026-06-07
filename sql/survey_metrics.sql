-- Brand and dimensional survey KPIs (standard NPS formula).
WITH overall AS (
    SELECT
        ROUND(
            100.0 * (
                AVG(CASE WHEN nps >= 9 THEN 1.0 ELSE 0.0 END)
                - AVG(CASE WHEN nps <= 6 THEN 1.0 ELSE 0.0 END)
            ),
            1
        ) AS overall_nps,
        ROUND(AVG(csat), 2) AS overall_csat,
        ROUND(AVG(revisit_intent), 2) AS avg_revisit_intent
    FROM guest_surveys
),
nps_by_region AS (
    SELECT
        region,
        COUNT(*) AS survey_count,
        ROUND(
            100.0 * (
                AVG(CASE WHEN nps >= 9 THEN 1.0 ELSE 0.0 END)
                - AVG(CASE WHEN nps <= 6 THEN 1.0 ELSE 0.0 END)
            ),
            1
        ) AS nps
    FROM guest_surveys
    GROUP BY region
),
csat_by_store_type AS (
    SELECT
        store_type,
        COUNT(*) AS survey_count,
        ROUND(AVG(csat), 2) AS csat
    FROM guest_surveys
    GROUP BY store_type
),
revisit_by_segment AS (
    SELECT
        guest_segment,
        COUNT(*) AS survey_count,
        ROUND(AVG(revisit_intent), 2) AS revisit_intent
    FROM guest_surveys
    GROUP BY guest_segment
)
SELECT 'overall_nps' AS metric_name, 'all' AS dimension_value, overall_nps AS metric_value
FROM overall
UNION ALL
SELECT 'overall_csat', 'all', overall_csat FROM overall
UNION ALL
SELECT 'avg_revisit_intent', 'all', avg_revisit_intent FROM overall
UNION ALL
SELECT 'nps_by_region', region, nps FROM nps_by_region
UNION ALL
SELECT 'csat_by_store_type', store_type, csat FROM csat_by_store_type
UNION ALL
SELECT 'revisit_intent_by_guest_segment', guest_segment, revisit_intent FROM revisit_by_segment
ORDER BY metric_name, dimension_value;
