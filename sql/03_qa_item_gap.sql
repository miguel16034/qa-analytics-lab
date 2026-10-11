-- Where does one QA analyst differ from the team, item by item?
WITH item_rates AS (
    SELECT
        q.qa_name,
        f.item_name,
        f.is_critical,
        AVG(1 - ai.passed) * 100 AS fail_pct
    FROM audit_items AS ai
    JOIN audits      AS a ON ai.audit_id = a.audit_id
    JOIN qa_analysts AS q ON a.qa_id     = q.qa_id
    JOIN form_items  AS f ON ai.item_id  = f.item_id
    GROUP BY q.qa_name, f.item_name, f.is_critical
),
compared AS (
    SELECT
        qa_name,
        item_name,
        is_critical,
        fail_pct,
        AVG(fail_pct) OVER (PARTITION BY item_name) AS team_fail_pct
    FROM item_rates
)
SELECT
    item_name,
    is_critical,
    ROUND(fail_pct, 1)                 AS qa_fail_pct,
    ROUND(team_fail_pct, 1)            AS team_fail_pct,
    ROUND(fail_pct - team_fail_pct, 1) AS diff
FROM compared
WHERE qa_name = 'Juan Humberto Reyes'
ORDER BY diff DESC;