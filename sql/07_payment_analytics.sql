
-- VIEW: OVERALL PAYMENT PERFORMANCE

CREATE OR REPLACE VIEW vw_payment_performance AS

SELECT
    COUNT(*) AS total_payment_attempts,

    COUNT(*) FILTER (
        WHERE ps.status_name = 'successful'
    ) AS successful_payments,

    COUNT(*) FILTER (
        WHERE ps.status_name = 'failed'
    ) AS failed_payments,

    COUNT(*) FILTER (
        WHERE ps.status_name = 'pending'
    ) AS pending_payments,

    COUNT(*) FILTER (
        WHERE ps.status_name = 'refunded'
    ) AS refund_transactions,

    ROUND(
        COUNT(*) FILTER (
            WHERE ps.status_name = 'successful'
        ) * 100.0 / NULLIF(COUNT(*), 0),
        2
    ) AS payment_success_rate_pct,

    COALESCE(
        SUM(p.amount) FILTER (
            WHERE ps.status_name = 'successful'
        ), 0
    ) AS successful_payment_value,

    COALESCE(
        SUM(p.amount) FILTER (
            WHERE ps.status_name = 'refunded'
        ), 0
    ) AS refunded_payment_value

FROM payments p

JOIN payment_statuses ps
    ON p.payment_status_id = ps.payment_status_id;


-- VIEW: PAYMENT METHOD PERFORMANCE

CREATE OR REPLACE VIEW vw_payment_method_performance AS

SELECT
    p.payment_method,

    COUNT(*) AS total_attempts,

    COUNT(*) FILTER (
        WHERE ps.status_name = 'successful'
    ) AS successful_payments,

    COUNT(*) FILTER (
        WHERE ps.status_name = 'failed'
    ) AS failed_payments,

    COUNT(*) FILTER (
        WHERE ps.status_name = 'pending'
    ) AS pending_payments,

    ROUND(
        COUNT(*) FILTER (
            WHERE ps.status_name = 'successful'
        ) * 100.0 / NULLIF(
            COUNT(*) FILTER (
                WHERE ps.status_name IN (
                    'successful', 'failed'
                )
            ), 0
        ),
        2
    ) AS resolved_payment_success_rate_pct,

    COALESCE(
        SUM(p.amount) FILTER (
            WHERE ps.status_name = 'successful'
        ), 0
    ) AS successful_payment_value

FROM payments p

JOIN payment_statuses ps
    ON p.payment_status_id = ps.payment_status_id

GROUP BY p.payment_method;


-- VIEW: MONTHLY PAYMENT TRENDS

CREATE OR REPLACE VIEW vw_monthly_payment_trends AS

SELECT
    DATE_TRUNC(
        'month',
        p.created_at
    )::date AS month,

    COUNT(*) AS total_attempts,

    COUNT(*) FILTER (
        WHERE ps.status_name = 'successful'
    ) AS successful_payments,

    COUNT(*) FILTER (
        WHERE ps.status_name = 'failed'
    ) AS failed_payments,

    COUNT(*) FILTER (
        WHERE ps.status_name = 'pending'
    ) AS pending_payments,

    COUNT(*) FILTER (
        WHERE ps.status_name = 'refunded'
    ) AS refund_transactions,

    COALESCE(
        SUM(p.amount) FILTER (
            WHERE ps.status_name = 'successful'
        ), 0
    ) AS successful_payment_value,

    COALESCE(
        SUM(p.amount) FILTER (
            WHERE ps.status_name = 'refunded'
        ), 0
    ) AS refunded_payment_value,

    ROUND(
        COUNT(*) FILTER (
            WHERE ps.status_name = 'successful'
        ) * 100.0 / NULLIF(
            COUNT(*) FILTER (
                WHERE ps.status_name IN (
                    'successful', 'failed'
                )
            ), 0
        ),
        2
    ) AS resolved_payment_success_rate_pct

FROM payments p

JOIN payment_statuses ps
    ON p.payment_status_id = ps.payment_status_id

GROUP BY 1;


-- VIEW: PAYMENT ATTEMPTS PER ORDER

CREATE OR REPLACE VIEW vw_payment_attempts_per_order AS

SELECT
    p.order_id,

    COUNT(*) AS total_attempts,

    COUNT(*) FILTER (
        WHERE ps.status_name = 'successful'
    ) AS successful_attempts,

    COUNT(*) FILTER (
        WHERE ps.status_name = 'failed'
    ) AS failed_attempts,

    COUNT(*) FILTER (
        WHERE ps.status_name = 'pending'
    ) AS pending_attempts,

    COUNT(*) FILTER (
        WHERE ps.status_name = 'refunded'
    ) AS refund_transactions,

    BOOL_OR(
        ps.status_name = 'successful'
    ) AS has_successful_payment

FROM payments p

JOIN payment_statuses ps
    ON p.payment_status_id = ps.payment_status_id

GROUP BY p.order_id;


-- VIEW: PAYMENT ATTEMPT DISTRIBUTION

CREATE OR REPLACE VIEW vw_payment_attempt_distribution AS

SELECT
    total_attempts AS attempts_per_order,

    COUNT(*) AS order_count,

    ROUND(
        COUNT(*) * 100.0
        / NULLIF(SUM(COUNT(*)) OVER (), 0),
        2
    ) AS order_share_pct

FROM vw_payment_attempts_per_order

GROUP BY total_attempts;


-- VIEW: REFUND ANALYSIS

CREATE OR REPLACE VIEW vw_refund_analysis AS

SELECT
    o.order_id,

    o.buyer_id,

    o.seller_id,

    o.item_subtotal,

    o.total_amount,

    o.created_at AS order_created_at,

    p.created_at AS refund_created_at,

    p.amount AS refund_amount,

    p.payment_method

FROM payments p

JOIN payment_statuses ps
    ON p.payment_status_id = ps.payment_status_id

JOIN orders o
    ON p.order_id = o.order_id

WHERE ps.status_name = 'refunded';

-- VIEW: ORDER PAYMENT RECONCILIATION

CREATE OR REPLACE VIEW vw_order_payment_reconciliation AS

SELECT
    o.order_id,

    os.status_name AS order_status,

    o.total_amount AS order_total,

    COALESCE(
        SUM(p.amount) FILTER (
            WHERE ps.status_name = 'successful'
        ), 0
    ) AS successful_payment_amount,

    COALESCE(
        SUM(p.amount) FILTER (
            WHERE ps.status_name = 'refunded'
        ), 0
    ) AS refunded_amount,

    COALESCE(
        BOOL_OR(ps.status_name = 'successful'),
        FALSE
    ) AS has_successful_payment,

    COALESCE(
        BOOL_OR(ps.status_name = 'refunded'),
        FALSE
    ) AS has_refund

FROM orders o

JOIN order_statuses os
    ON o.order_status_id = os.order_status_id

LEFT JOIN payments p
    ON o.order_id = p.order_id

LEFT JOIN payment_statuses ps
    ON p.payment_status_id = ps.payment_status_id

GROUP BY
    o.order_id,
    os.status_name,
    o.total_amount;
