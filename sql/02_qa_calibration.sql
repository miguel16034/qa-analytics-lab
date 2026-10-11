-- Which QA analysts score far from the team average?
WITH qa_stats AS (
    SELECT
        q.qa_name,
        COUNT(*)               AS audits,
        AVG(a.score)           AS avg_score,
        AVG(a.has_critical_error) * 100 AS critical_pct
    FROM audits AS a
    JOIN qa_analysts AS q ON a.qa_id = q.qa_id
    GROUP BY q.qa_name
),
team AS (
    SELECT AVG(score) AS team_avg FROM audits
)
SELECT
    s.qa_name,
    s.audits,
    ROUND(s.avg_score, 1)                AS avg_score,
    ROUND(s.avg_score - t.team_avg, 1)   AS diff_vs_team,
    ROUND(s.critical_pct, 1)             AS critical_pct
FROM qa_stats AS s
CROSS JOIN team AS t
ORDER BY diff_vs_team;