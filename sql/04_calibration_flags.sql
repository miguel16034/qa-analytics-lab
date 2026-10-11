-- Flag QA analysts who score too far from the team
WITH qa_stats AS (
    SELECT
        q.qa_name,
        AVG(a.score)                    AS avg_score,
        AVG(a.has_critical_error) * 100 AS critical_pct
    FROM audits AS a
    JOIN qa_analysts AS q ON a.qa_id = q.qa_id
    GROUP BY q.qa_name
),
scored AS (
    SELECT
        qa_name,
        avg_score,
        critical_pct,
        avg_score - AVG(avg_score) OVER () AS diff_vs_team,
        RANK() OVER (ORDER BY avg_score)   AS strictness_rank
    FROM qa_stats
)
SELECT
    strictness_rank,
    qa_name,
    ROUND(avg_score, 1)    AS avg_score,
    ROUND(diff_vs_team, 1) AS diff_vs_team,
    ROUND(critical_pct, 1) AS critical_pct,
    CASE
        WHEN diff_vs_team <= -3 THEN 'Too strict'
        WHEN diff_vs_team >=  3 THEN 'Too lenient'
        ELSE 'OK'
    END AS calibration_flag
FROM scored
ORDER BY strictness_rank;