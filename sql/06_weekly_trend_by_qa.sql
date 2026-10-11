-- Weekly quality trend for one QA analyst
WITH weekly AS (
    SELECT
        q.qa_name,
        DATE(a.audit_date, 'weekday 0', '-6 days') AS week_start,
        COUNT(*)                                   AS audits,
        AVG(a.score)                               AS avg_score,
        AVG(a.has_critical_error) * 100            AS critical_pct
    FROM audits AS a
    JOIN qa_analysts AS q ON a.qa_id = q.qa_id
    GROUP BY q.qa_name, week_start
)
SELECT
    qa_name,
    week_start,
    audits,
    ROUND(avg_score, 1) AS avg_score,
    ROUND(avg_score - LAG(avg_score) OVER (PARTITION BY qa_name ORDER BY week_start), 1) AS wow_change,
    ROUND(critical_pct, 1) AS critical_pct
FROM weekly
WHERE qa_name = 'Juan Humberto Reyes'
ORDER BY week_start;