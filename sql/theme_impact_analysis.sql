-- Theme prevalence, negative share, satisfaction gaps, and detractor over-index.
WITH commented AS (
    SELECT *
    FROM guest_surveys
    WHERE comment_text IS NOT NULL AND TRIM(comment_text) <> ''
),
brand AS (
    SELECT
        COUNT(*) AS total_comments,
        ROUND(
            100.0 * (
                AVG(CASE WHEN nps >= 9 THEN 1.0 ELSE 0.0 END)
                - AVG(CASE WHEN nps <= 6 THEN 1.0 ELSE 0.0 END)
            ),
            1
        ) AS brand_nps,
        ROUND(AVG(csat), 2) AS brand_csat,
        ROUND(AVG(revisit_intent), 2) AS brand_revisit_intent
    FROM commented
),
theme_stats AS (
    SELECT
        primary_theme,
        COUNT(*) AS theme_count,
        ROUND(AVG(CASE WHEN is_negative_experience THEN 1.0 ELSE 0.0 END), 4) AS negative_share,
        ROUND(
            100.0 * (
                AVG(CASE WHEN nps >= 9 THEN 1.0 ELSE 0.0 END)
                - AVG(CASE WHEN nps <= 6 THEN 1.0 ELSE 0.0 END)
            ),
            1
        ) AS theme_nps,
        ROUND(AVG(csat), 2) AS theme_csat,
        ROUND(AVG(revisit_intent), 2) AS theme_revisit_intent,
        ROUND(AVG(CASE WHEN nps <= 6 THEN 1.0 ELSE 0.0 END), 4) AS detractor_share
    FROM commented
    GROUP BY primary_theme
),
detractor_totals AS (
    SELECT
        primary_theme,
        COUNT(*) AS detractor_theme_count
    FROM commented
    WHERE nps <= 6
    GROUP BY primary_theme
)
SELECT
    t.primary_theme,
    t.theme_count,
    ROUND(t.theme_count::DOUBLE / b.total_comments, 4) AS share_of_comments,
    t.negative_share,
    t.theme_nps,
    t.theme_csat,
    t.theme_revisit_intent,
    ROUND(t.theme_nps - b.brand_nps, 2) AS nps_gap_vs_brand,
    ROUND(t.theme_csat - b.brand_csat, 2) AS csat_gap_vs_brand,
    ROUND(t.theme_revisit_intent - b.brand_revisit_intent, 2) AS revisit_gap_vs_brand,
    COALESCE(d.detractor_theme_count, 0) AS detractor_comment_count,
    ROUND(
        COALESCE(d.detractor_theme_count, 0)::DOUBLE
        / NULLIF((SELECT COUNT(*) FROM commented WHERE nps <= 6), 0),
        4
    ) AS share_of_detractor_comments,
    ROUND(
        (
            COALESCE(d.detractor_theme_count, 0)::DOUBLE
            / NULLIF((SELECT COUNT(*) FROM commented WHERE nps <= 6), 0)
        )
        / NULLIF(t.theme_count::DOUBLE / b.total_comments, 0),
        4
    ) AS detractor_over_index
FROM theme_stats t
CROSS JOIN brand b
LEFT JOIN detractor_totals d ON t.primary_theme = d.primary_theme
ORDER BY t.theme_count DESC;
