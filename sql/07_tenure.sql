-- Does tenure affect quality?
WITH audit_tenure AS (
    SELECT
        a.score,
        a.has_critical_error,
        JULIANDAY(a.audit_date) - JULIANDAY(g.hire_date) AS tenure_days
    FROM audits AS a
    JOIN agents AS g ON a.agent_id = g.agent_id
)
SELECT
    CASE
        WHEN tenure_days <  30 THEN '1. 0-29 days'
        WHEN tenure_days <  90 THEN '2. 30-89 days'
        WHEN tenure_days < 180 THEN '3. 90-179 days'
        WHEN tenure_days < 365 THEN '4. 180-364 days'
        ELSE                        '5. 1 year+'
    END                                     AS tenure_group,
    COUNT(*)                                AS audits,
    ROUND(AVG(score), 1)                    AS avg_score,
    ROUND(AVG(has_critical_error) * 100, 1) AS critical_pct
FROM audit_tenure
GROUP BY tenure_group
ORDER BY tenure_group;