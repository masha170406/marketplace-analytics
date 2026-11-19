-- VIEW: LISTING STATUS DISTRIBUTION

CREATE OR REPLACE VIEW vw_listing_status_distribution AS

SELECT
    ls.status_name,

    COUNT(*) AS listing_count,

    ROUND(
        COUNT(*) * 100.0
        / NULLIF(SUM(COUNT(*)) OVER (), 0),
        2
    ) AS listing_share_pct,

    ROUND(AVG(l.price), 2) AS average_listing_price

FROM listings l

JOIN listing_statuses ls
    ON l.listing_status_id = ls.listing_status_id

GROUP BY ls.status_name;

-- VIEW: LISTING INVENTORY SUMMARY

CREATE OR REPLACE VIEW vw_listing_inventory_summary AS

SELECT
    COUNT(*) AS total_listings,

    COUNT(*) FILTER (
        WHERE published_at IS NOT NULL
    ) AS published_listings,

    COUNT(*) FILTER (
        WHERE ls.status_name = 'active'
    ) AS active_listings,

    COUNT(*) FILTER (
        WHERE ls.status_name = 'reserved'
    ) AS reserved_listings,

    COUNT(*) FILTER (
        WHERE ls.status_name = 'sold'
    ) AS currently_sold_listings,

    COUNT(*) FILTER (
        WHERE ls.status_name = 'expired'
    ) AS expired_listings,

    COUNT(*) FILTER (
        WHERE ls.status_name = 'removed'
    ) AS removed_listings,

    ROUND(
        AVG(l.price),
        2
    ) AS average_listing_price

FROM listings l

JOIN listing_statuses ls
    ON l.listing_status_id = ls.listing_status_id;


-- VIEW: LISTING PERFORMANCE BY CATEGORY

CREATE OR REPLACE VIEW vw_listing_category_performance AS

SELECT
    c.category_id,

    c.category_name,

    COUNT(*) AS total_listings,

    COUNT(*) FILTER (
        WHERE l.published_at IS NOT NULL
    ) AS published_listings,

    COUNT(*) FILTER (
        WHERE ls.status_name = 'active'
    ) AS active_listings,

    COUNT(*) FILTER (
        WHERE ls.status_name = 'sold'
    ) AS currently_sold_listings,

    ROUND(
        AVG(l.price),
        2
    ) AS average_listing_price,

    ROUND(
        MIN(l.price),
        2
    ) AS minimum_listing_price,

    ROUND(
        MAX(l.price),
        2
    ) AS maximum_listing_price

FROM listings l

JOIN categories c
    ON l.category_id = c.category_id

JOIN listing_statuses ls
    ON l.listing_status_id = ls.listing_status_id

GROUP BY
    c.category_id,
    c.category_name;


-- VIEW: MONTHLY LISTING CREATION

CREATE OR REPLACE VIEW vw_monthly_listing_creation AS

SELECT
    DATE_TRUNC(
        'month',
        created_at
    )::date AS month,

    COUNT(*) AS created_listings,

    COUNT(*) FILTER (
        WHERE published_at IS NOT NULL
    ) AS published_listings,

    ROUND(
        AVG(price),
        2
    ) AS average_listing_price

FROM listings

GROUP BY 1;


-- VIEW: LISTING TIME TO SALE
-- Uses the first recorded transition to the sold status.
-- Only listings with a completed order are included.

CREATE OR REPLACE VIEW vw_listing_time_to_sale AS

WITH first_sold_event AS (

    SELECT
        lsh.listing_id,

        MIN(lsh.changed_at) AS sold_at

    FROM listing_status_history lsh

    JOIN listing_statuses ls
        ON lsh.listing_status_id = ls.listing_status_id

    WHERE ls.status_name = 'sold'

    GROUP BY lsh.listing_id

),

completed_listing_sales AS (

    SELECT
        oi.listing_id,

        MIN(o.completed_at) AS completed_at

    FROM order_items oi

    JOIN orders o
        ON oi.order_id = o.order_id

    JOIN order_statuses os
        ON o.order_status_id = os.order_status_id

    WHERE os.status_name = 'completed'
      AND o.completed_at IS NOT NULL

    GROUP BY oi.listing_id

)

SELECT
    l.listing_id,

    l.seller_id,

    l.category_id,

    l.price,

    l.published_at,

    fs.sold_at,

    cls.completed_at,

    ROUND(
        (
            EXTRACT(
                EPOCH FROM (fs.sold_at - l.published_at)
            ) / 86400.0
        )::numeric,
        2
    ) AS days_to_sold_status,

    ROUND(
        (
            EXTRACT(
                EPOCH FROM (cls.completed_at - l.published_at)
            ) / 86400.0
        )::numeric,
        2
    ) AS days_to_completed_sale

FROM listings l

JOIN first_sold_event fs
    ON l.listing_id = fs.listing_id

JOIN completed_listing_sales cls
    ON l.listing_id = cls.listing_id

WHERE l.published_at IS NOT NULL
  AND fs.sold_at >= l.published_at
  AND cls.completed_at >= l.published_at;


-- VIEW: TIME TO SALE BY CATEGORY

CREATE OR REPLACE VIEW vw_category_time_to_sale AS

SELECT
    c.category_id,

    c.category_name,

    COUNT(*) AS sold_listings,

    ROUND(
        AVG(ts.days_to_sold_status),
        2
    ) AS average_days_to_sold,

    ROUND(
        PERCENTILE_CONT(0.5)
        WITHIN GROUP (
            ORDER BY ts.days_to_sold_status
        )::numeric,
        2
    ) AS median_days_to_sold,

    ROUND(
        MIN(ts.days_to_sold_status),
        2
    ) AS minimum_days_to_sold,

    ROUND(
        MAX(ts.days_to_sold_status),
        2
    ) AS maximum_days_to_sold

FROM vw_listing_time_to_sale ts

JOIN categories c
    ON ts.category_id = c.category_id

GROUP BY
    c.category_id,
    c.category_name;


-- VIEW: LISTING PRICE DISTRIBUTION

CREATE OR REPLACE VIEW vw_listing_price_distribution AS

SELECT
    CASE
        WHEN price < 10 THEN 'Under 10 EUR'
        WHEN price < 25 THEN '10-24.99 EUR'
        WHEN price < 50 THEN '25-49.99 EUR'
        WHEN price < 100 THEN '50-99.99 EUR'
        WHEN price < 200 THEN '100-199.99 EUR'
        ELSE '200+ EUR'
    END AS price_range,

    COUNT(*) AS listing_count,

    ROUND(
        AVG(price),
        2
    ) AS average_price

FROM listings

WHERE published_at IS NOT NULL

GROUP BY 1;
