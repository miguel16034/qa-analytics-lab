-- Average score and critical error rate by line
SELECT
    l.line_name,
    COUNT(*)                                  AS audits,
    ROUND(AVG(a.score), 1)                    AS avg_score,
    ROUND(AVG(a.has_critical_error) * 100, 1) AS critical_pct
FROM audits AS a
JOIN agents AS g ON a.agent_id = g.agent_id
JOIN lines  AS l ON g.line_id  = l.line_id
GROUP BY l.line_name
ORDER BY avg_score DESC;