-- Segment-level satisfaction metrics and dominant VoC theme.
WITH segment_metrics AS (
    SELECT
        guest_segment,
        COUNT(*) AS survey_count,
        ROUND(
            100.0 * (
                AVG(CASE WHEN nps >= 9 THEN 1.0 ELSE 0.0 END)
                - AVG(CASE WHEN nps <= 6 THEN 1.0 ELSE 0.0 END)
            ),
            1
        ) AS segment_nps,
        ROUND(AVG(csat), 2) AS segment_csat,
        ROUND(AVG(revisit_intent), 2) AS segment_revisit_intent
    FROM guest_surveys
    GROUP BY guest_segment
),
theme_by_segment AS (
    SELECT
        guest_segment,
        primary_theme,
        COUNT(*) AS comment_count,
        ROW_NUMBER() OVER (
            PARTITION BY guest_segment
            ORDER BY COUNT(*) DESC
        ) AS theme_rank
    FROM guest_surveys
    WHERE comment_text IS NOT NULL AND TRIM(comment_text) <> ''
    GROUP BY guest_segment, primary_theme
)
SELECT
    m.guest_segment,
    m.survey_count,
    m.segment_nps,
    m.segment_csat,
    m.segment_revisit_intent,
    t.primary_theme AS top_theme
FROM segment_metrics m
LEFT JOIN theme_by_segment t
    ON m.guest_segment = t.guest_segment
   AND t.theme_rank = 1
ORDER BY m.segment_nps ASC;
