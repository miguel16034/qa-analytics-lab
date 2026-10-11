-- Weekly quality trend with week-over-week change
WITH weekly AS (
    SELECT
        DATE(audit_date, 'weekday 0', '-6 days') AS week_start,
        COUNT(*)                                 AS audits,
        AVG(score)                               AS avg_score,
        AVG(has_critical_error) * 100            AS critical_pct
    FROM audits
    GROUP BY week_start
)
SELECT
    week_start,
    audits,
    ROUND(avg_score, 1)                                             AS avg_score,
    ROUND(avg_score - LAG(avg_score) OVER (ORDER BY week_start), 1) AS wow_change,
    ROUND(critical_pct, 1)                                          AS critical_pct
FROM weekly
ORDER BY week_start;