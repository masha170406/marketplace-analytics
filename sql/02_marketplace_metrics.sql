-- VIEW : ALL-TIME MARKETPLACE KPIs

CREATE OR REPLACE VIEW vw_marketplace_kpis AS

SELECT
    COUNT(*) AS total_orders,

    COUNT(*) FILTER (
        WHERE os.status_name = 'completed'
    ) AS completed_orders,

    COUNT(*) FILTER (
        WHERE os.status_name = 'cancelled'
    ) AS cancelled_orders,

    COUNT(*) FILTER (
        WHERE os.status_name = 'refunded'
    ) AS refunded_orders,

    COUNT(DISTINCT o.buyer_id) AS total_buyers,

    COUNT(DISTINCT o.seller_id) AS total_sellers,

    COALESCE(
        SUM(o.item_subtotal) FILTER (
            WHERE os.status_name = 'completed'
        ), 0
    ) AS total_gmv,

    COALESCE(
        SUM(o.buyer_fee + o.seller_fee) FILTER (
            WHERE os.status_name = 'completed'
        ), 0
    ) AS marketplace_revenue,

    ROUND(
        (
            SUM(o.item_subtotal) FILTER (
                WHERE os.status_name = 'completed'
            )
            /
            NULLIF(
                COUNT(*) FILTER (
                    WHERE os.status_name = 'completed'
                ), 0
            )
        )::numeric,
        2
    ) AS average_order_value,

    ROUND(
        COUNT(*) FILTER (
            WHERE os.status_name = 'cancelled'
        ) * 100.0 / NULLIF(COUNT(*), 0),
        2
    ) AS cancellation_rate_pct,

    ROUND(
        COUNT(*) FILTER (
            WHERE os.status_name = 'refunded'
        ) * 100.0 / NULLIF(COUNT(*), 0),
        2
    ) AS refund_rate_pct

FROM orders o
JOIN order_statuses os
    ON o.order_status_id = os.order_status_id;


-- VIEW : MONTHLY MARKETPLACE METRICS
-- Order activity, buyers and sellers are attributed to the order creation month.
-- GMV, revenue and AOV are attributed to the completion month.

CREATE OR REPLACE VIEW vw_monthly_marketplace_metrics AS

WITH date_range AS (

    SELECT
        DATE_TRUNC('month', MIN(created_at)) AS first_month,
        DATE_TRUNC('month', MAX(created_at)) AS last_month
    FROM orders

),

months AS (

    SELECT
        GENERATE_SERIES(
            first_month,
            last_month,
            INTERVAL '1 month'
        )::date AS month
    FROM date_range
    WHERE first_month IS NOT NULL

),

monthly_order_activity AS (

    SELECT
        DATE_TRUNC('month', o.created_at)::date AS month,

        COUNT(*) AS total_orders,

        COUNT(*) FILTER (
            WHERE os.status_name = 'cancelled'
        ) AS cancelled_orders,

        COUNT(*) FILTER (
            WHERE os.status_name = 'refunded'
        ) AS refunded_orders,

        COUNT(DISTINCT o.buyer_id) AS active_buyers,

        COUNT(DISTINCT o.seller_id) AS active_sellers

    FROM orders o
    JOIN order_statuses os
        ON o.order_status_id = os.order_status_id

    GROUP BY 1

),

monthly_completed_sales AS (

    SELECT
        DATE_TRUNC('month', o.completed_at)::date AS month,

        COUNT(*) AS completed_orders,

        SUM(o.item_subtotal) AS gmv,

        SUM(o.buyer_fee + o.seller_fee) AS marketplace_revenue,

        ROUND(
            (
                SUM(o.item_subtotal)
                / NULLIF(COUNT(*), 0)
            )::numeric,
            2
        ) AS average_order_value

    FROM orders o
    JOIN order_statuses os
        ON o.order_status_id = os.order_status_id

    WHERE os.status_name = 'completed'
      AND o.completed_at IS NOT NULL

    GROUP BY 1

)

SELECT
    m.month,

    COALESCE(a.total_orders, 0) AS total_orders,

    COALESCE(s.completed_orders, 0) AS completed_orders,

    COALESCE(a.cancelled_orders, 0) AS cancelled_orders,

    COALESCE(a.refunded_orders, 0) AS refunded_orders,

    COALESCE(a.active_buyers, 0) AS active_buyers,

    COALESCE(a.active_sellers, 0) AS active_sellers,

    COALESCE(s.gmv, 0) AS gmv,

    COALESCE(s.marketplace_revenue, 0) AS marketplace_revenue,

    COALESCE(s.average_order_value, 0) AS average_order_value,

    ROUND(
        COALESCE(a.cancelled_orders, 0) * 100.0
        / NULLIF(a.total_orders, 0),
        2
    ) AS cancellation_rate_pct,

    ROUND(
        COALESCE(a.refunded_orders, 0) * 100.0
        / NULLIF(a.total_orders, 0),
        2
    ) AS refund_rate_pct

FROM months m

LEFT JOIN monthly_order_activity a
    ON m.month = a.month

LEFT JOIN monthly_completed_sales s
    ON m.month = s.month

ORDER BY m.month;
