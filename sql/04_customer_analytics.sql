
-- VIEW: CUSTOMER PURCHASE SUMMARY

CREATE OR REPLACE VIEW vw_customer_purchase_summary AS

WITH customer_orders AS (

    SELECT
        o.buyer_id,
        o.order_id,
        o.item_subtotal,
        o.completed_at,

        ROW_NUMBER() OVER (
            PARTITION BY o.buyer_id
            ORDER BY o.completed_at
        ) AS purchase_number

    FROM orders o

    JOIN order_statuses os
        ON o.order_status_id = os.order_status_id

    WHERE os.status_name = 'completed'
      AND o.completed_at IS NOT NULL

)

SELECT
    u.user_id,

    COUNT(co.order_id) AS completed_orders,

    COALESCE(SUM(co.item_subtotal), 0) AS total_spend,

    ROUND(
        AVG(co.item_subtotal),
        2
    ) AS average_order_value,

    MIN(co.completed_at) AS first_purchase_date,

    MAX(co.completed_at) AS last_purchase_date,

    CASE
        WHEN COUNT(co.order_id) = 0 THEN 'No purchases'
        WHEN COUNT(co.order_id) = 1 THEN 'One-time buyer'
        ELSE 'Repeat buyer'
    END AS customer_segment,

    MAX(co.purchase_number) AS purchase_number

FROM users u

LEFT JOIN customer_orders co
    ON u.user_id = co.buyer_id

GROUP BY u.user_id;


-- VIEW: CUSTOMER SEGMENT DISTRIBUTION

CREATE OR REPLACE VIEW vw_customer_segments AS

SELECT
    customer_segment,

    COUNT(*) AS customer_count,

    ROUND(
        COUNT(*) * 100.0
        / NULLIF(SUM(COUNT(*)) OVER (), 0),
        2
    ) AS customer_share_pct

FROM vw_customer_purchase_summary

GROUP BY customer_segment;


-- VIEW: REPEAT PURCHASE RATE

CREATE OR REPLACE VIEW vw_repeat_purchase_metrics AS

SELECT
    COUNT(*) FILTER (
        WHERE completed_orders > 0
    ) AS customers_with_purchases,

    COUNT(*) FILTER (
        WHERE completed_orders > 1
    ) AS repeat_customers,

    COUNT(*) FILTER (
        WHERE completed_orders = 1
    ) AS one_time_customers,

    ROUND(
        COUNT(*) FILTER (
            WHERE completed_orders > 1
        ) * 100.0
        / NULLIF(
            COUNT(*) FILTER (
                WHERE completed_orders > 0
            ), 0
        ),
        2
    ) AS repeat_purchase_rate_pct

FROM vw_customer_purchase_summary;

-- VIEW: FIRST PURCHASE COHORT

CREATE OR REPLACE VIEW vw_customer_cohorts AS

SELECT
    buyer_id,

    MIN(completed_at) AS first_purchase_date,

    DATE_TRUNC(
        'month',
        MIN(completed_at)
    )::date AS cohort_month

FROM orders o

JOIN order_statuses os
    ON o.order_status_id = os.order_status_id

WHERE os.status_name = 'completed'
  AND completed_at IS NOT NULL

GROUP BY buyer_id;


-- VIEW: MONTHLY CUSTOMER COHORT ACTIVITY

CREATE OR REPLACE VIEW vw_cohort_activity AS

WITH customer_activity AS (

    SELECT DISTINCT
        o.buyer_id,

        DATE_TRUNC(
            'month',
            o.completed_at
        )::date AS activity_month

    FROM orders o

    JOIN order_statuses os
        ON o.order_status_id = os.order_status_id

    WHERE os.status_name = 'completed'
      AND o.completed_at IS NOT NULL

),

cohort_activity AS (

    SELECT
        c.cohort_month,

        a.activity_month,

        (
            EXTRACT(YEAR FROM a.activity_month)
            - EXTRACT(YEAR FROM c.cohort_month)
        ) * 12
        +
        (
            EXTRACT(MONTH FROM a.activity_month)
            - EXTRACT(MONTH FROM c.cohort_month)
        ) AS cohort_index,

        COUNT(DISTINCT a.buyer_id) AS active_customers

    FROM vw_customer_cohorts c

    JOIN customer_activity a
        ON c.buyer_id = a.buyer_id

    GROUP BY
        c.cohort_month,
        a.activity_month

)

SELECT
    cohort_month,
    activity_month,
    cohort_index,
    active_customers

FROM cohort_activity;


-- VIEW: COHORT RETENTION

CREATE OR REPLACE VIEW vw_cohort_retention AS

WITH cohort_sizes AS (

    SELECT
        cohort_month,
        COUNT(*) AS cohort_size

    FROM vw_customer_cohorts

    GROUP BY cohort_month

)

SELECT
    ca.cohort_month,
    ca.activity_month,
    ca.cohort_index,

    ca.active_customers,

    cs.cohort_size,

    ROUND(
        ca.active_customers * 100.0
        / NULLIF(cs.cohort_size, 0),
        2
    ) AS retention_rate_pct

FROM vw_cohort_activity ca

JOIN cohort_sizes cs
    ON ca.cohort_month = cs.cohort_month;


-- VIEW: MONTHLY CUSTOMER ACQUISITION

CREATE OR REPLACE VIEW vw_monthly_customer_acquisition AS

SELECT
    cohort_month AS month,

    COUNT(*) AS new_customers

FROM vw_customer_cohorts

GROUP BY cohort_month;


-- VIEW: CUSTOMER LIFETIME VALUE
-- Historical completed-order spend per customer

CREATE OR REPLACE VIEW vw_customer_lifetime_value AS

SELECT
    user_id,

    completed_orders,

    total_spend,

    average_order_value,

    first_purchase_date,

    last_purchase_date,

    customer_segment,

    ROUND(
        total_spend / NULLIF(completed_orders, 0),
        2
    ) AS lifetime_average_order_value

FROM vw_customer_purchase_summary

WHERE completed_orders > 0;
