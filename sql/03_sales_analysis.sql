
-- VIEW: MONTHLY SALES TRENDS

CREATE OR REPLACE VIEW vw_monthly_sales AS

SELECT
    DATE_TRUNC('month', o.completed_at)::date AS month,

    COUNT(*) AS completed_orders,

    SUM(o.item_subtotal) AS gmv,

    SUM(o.buyer_fee + o.seller_fee) AS marketplace_revenue,

    ROUND(
        AVG(o.item_subtotal),
        2
    ) AS average_order_value,

    COUNT(DISTINCT o.buyer_id) AS unique_buyers,

    COUNT(DISTINCT o.seller_id) AS unique_sellers

FROM orders o

JOIN order_statuses os
    ON o.order_status_id = os.order_status_id

WHERE os.status_name = 'completed'
  AND o.completed_at IS NOT NULL

GROUP BY 1;


-- VIEW: CATEGORY PERFORMANCE

CREATE OR REPLACE VIEW vw_category_performance AS

SELECT
    c.category_id,
    c.category_name,

    COUNT(DISTINCT oi.order_id) AS completed_orders,

    COUNT(DISTINCT oi.listing_id) AS items_sold,

    SUM(oi.item_price) AS gmv,

    ROUND(
        AVG(oi.item_price),
        2
    ) AS average_item_price,

    ROUND(
        SUM(oi.item_price) * 100.0
        / NULLIF(
            SUM(SUM(oi.item_price)) OVER (),
            0
        ),
        2
    ) AS gmv_share_pct

FROM order_items oi

JOIN orders o
    ON oi.order_id = o.order_id

JOIN order_statuses os
    ON o.order_status_id = os.order_status_id

JOIN listings l
    ON oi.listing_id = l.listing_id

JOIN categories c
    ON l.category_id = c.category_id

WHERE os.status_name = 'completed'

GROUP BY
    c.category_id,
    c.category_name;


-- VIEW: CATEGORY PERFORMANCE BY MONTH

CREATE OR REPLACE VIEW vw_monthly_category_sales AS

SELECT
    DATE_TRUNC('month', o.completed_at)::date AS month,

    c.category_id,
    c.category_name,

    COUNT(DISTINCT o.order_id) AS completed_orders,

    COUNT(DISTINCT oi.listing_id) AS items_sold,

    SUM(oi.item_price) AS gmv,

    ROUND(
        AVG(oi.item_price),
        2
    ) AS average_item_price

FROM orders o

JOIN order_statuses os
    ON o.order_status_id = os.order_status_id

JOIN order_items oi
    ON o.order_id = oi.order_id

JOIN listings l
    ON oi.listing_id = l.listing_id

JOIN categories c
    ON l.category_id = c.category_id

WHERE os.status_name = 'completed'
  AND o.completed_at IS NOT NULL

GROUP BY
    1,
    c.category_id,
    c.category_name;


-- VIEW: ORDER VALUE DISTRIBUTION

CREATE OR REPLACE VIEW vw_order_value_distribution AS

SELECT
    CASE
        WHEN item_subtotal < 10 THEN 'Under 10 EUR'
        WHEN item_subtotal < 25 THEN '10-24.99 EUR'
        WHEN item_subtotal < 50 THEN '25-49.99 EUR'
        WHEN item_subtotal < 100 THEN '50-99.99 EUR'
        WHEN item_subtotal < 200 THEN '100-199.99 EUR'
        ELSE '200+ EUR'
    END AS order_value_range,

    COUNT(*) AS completed_orders,

    SUM(item_subtotal) AS gmv,

    ROUND(
        AVG(item_subtotal),
        2
    ) AS average_order_value

FROM orders o

JOIN order_statuses os
    ON o.order_status_id = os.order_status_id

WHERE os.status_name = 'completed'

GROUP BY 1;


-- VIEW: ORDER STATUS DISTRIBUTION

CREATE OR REPLACE VIEW vw_order_status_distribution AS

SELECT
    os.status_name,

    COUNT(*) AS order_count,

    ROUND(
        COUNT(*) * 100.0
        / NULLIF(SUM(COUNT(*)) OVER (), 0),
        2
    ) AS order_share_pct,

    SUM(o.item_subtotal) AS item_subtotal_value

FROM orders o

JOIN order_statuses os
    ON o.order_status_id = os.order_status_id

GROUP BY os.status_name;


-- VIEW: TOP SELLING CATEGORIES

CREATE OR REPLACE VIEW vw_top_selling_categories AS

SELECT
    c.category_name,

    COUNT(DISTINCT oi.listing_id) AS items_sold,

    SUM(oi.item_price) AS gmv,

    ROUND(
        AVG(oi.item_price),
        2
    ) AS average_item_price,

    COUNT(DISTINCT o.buyer_id) AS unique_buyers

FROM order_items oi

JOIN orders o
    ON oi.order_id = o.order_id

JOIN order_statuses os
    ON o.order_status_id = os.order_status_id

JOIN listings l
    ON oi.listing_id = l.listing_id

JOIN categories c
    ON l.category_id = c.category_id

WHERE os.status_name = 'completed'

GROUP BY c.category_id, c.category_name;
