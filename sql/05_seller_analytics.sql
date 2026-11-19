-- VIEW: SELLER PERFORMANCE SUMMARY

CREATE OR REPLACE VIEW vw_seller_performance AS

WITH sales AS (

    SELECT
        o.seller_id,

        COUNT(*) AS completed_orders,

        SUM(o.item_subtotal) AS total_gmv,

        SUM(o.seller_fee) AS total_seller_fees,

        AVG(o.item_subtotal) AS average_order_value,

        COUNT(DISTINCT o.buyer_id) AS unique_buyers,

        MIN(o.completed_at) AS first_completed_sale,

        MAX(o.completed_at) AS last_completed_sale

    FROM orders o

    JOIN order_statuses os
        ON o.order_status_id = os.order_status_id

    WHERE os.status_name = 'completed'
      AND o.completed_at IS NOT NULL

    GROUP BY o.seller_id

),

review_metrics AS (

    SELECT
        reviewee_id AS seller_id,

        COUNT(*) AS total_reviews,

        ROUND(AVG(rating), 2) AS average_rating,

        COUNT(*) FILTER (
            WHERE rating >= 4
        ) AS positive_reviews,

        COUNT(*) FILTER (
            WHERE rating <= 2
        ) AS negative_reviews

    FROM reviews

    GROUP BY reviewee_id

),

seller_listings AS (

    SELECT
        seller_id,

        COUNT(*) AS total_listings,

        COUNT(*) FILTER (
            WHERE published_at IS NOT NULL
        ) AS published_listings,

        COUNT(*) FILTER (
            WHERE published_at IS NOT NULL
              AND listing_status_id = (
                  SELECT listing_status_id
                  FROM listing_statuses
                  WHERE status_name = 'sold'
              )
        ) AS sold_listings

    FROM listings

    GROUP BY seller_id

)

SELECT
    u.user_id AS seller_id,

    u.username,

    u.country,

    COALESCE(s.completed_orders, 0) AS completed_orders,

    COALESCE(s.total_gmv, 0) AS total_gmv,

    COALESCE(s.total_seller_fees, 0) AS total_seller_fees,

    ROUND(
        s.average_order_value,
        2
    ) AS average_order_value,

    COALESCE(s.unique_buyers, 0) AS unique_buyers,

    COALESCE(r.total_reviews, 0) AS total_reviews,

    r.average_rating,

    COALESCE(r.positive_reviews, 0) AS positive_reviews,

    COALESCE(r.negative_reviews, 0) AS negative_reviews,

    COALESCE(l.total_listings, 0) AS total_listings,

    COALESCE(l.published_listings, 0) AS published_listings,

    COALESCE(l.sold_listings, 0) AS sold_listings,

    s.first_completed_sale,

    s.last_completed_sale

FROM users u

LEFT JOIN sales s
    ON u.user_id = s.seller_id

LEFT JOIN review_metrics r
    ON u.user_id = r.seller_id

LEFT JOIN seller_listings l
    ON u.user_id = l.seller_id;


-- VIEW: TOP SELLERS BY GMV

CREATE OR REPLACE VIEW vw_top_sellers AS

SELECT
    seller_id,

    username,

    country,

    completed_orders,

    total_gmv,

    total_seller_fees,

    unique_buyers,

    total_reviews,

    average_rating,

    DENSE_RANK() OVER (
        ORDER BY total_gmv DESC
    ) AS gmv_rank

FROM vw_seller_performance

WHERE completed_orders > 0;

-- VIEW: SELLER PERFORMANCE BY COUNTRY

CREATE OR REPLACE VIEW vw_seller_country_performance AS

SELECT
    country,

    COUNT(*) AS total_sellers,

    COUNT(*) FILTER (
        WHERE completed_orders > 0
    ) AS sellers_with_sales,

    SUM(completed_orders) AS completed_orders,

    SUM(total_gmv) AS total_gmv,

    ROUND(
        AVG(total_gmv) FILTER (
            WHERE completed_orders > 0
        ),
        2
    ) AS average_gmv_per_selling_seller,

    ROUND(
        AVG(average_rating) FILTER (
            WHERE total_reviews > 0
        ),
        2
    ) AS average_seller_rating

FROM vw_seller_performance

GROUP BY country;


-- VIEW: MONTHLY SELLER PERFORMANCE

CREATE OR REPLACE VIEW vw_monthly_seller_performance AS

SELECT
    DATE_TRUNC(
        'month',
        o.completed_at
    )::date AS month,

    o.seller_id,

    COUNT(*) AS completed_orders,

    SUM(o.item_subtotal) AS gmv,

    SUM(o.seller_fee) AS seller_fees,

    COUNT(DISTINCT o.buyer_id) AS unique_buyers

FROM orders o

JOIN order_statuses os
    ON o.order_status_id = os.order_status_id

WHERE os.status_name = 'completed'
  AND o.completed_at IS NOT NULL

GROUP BY
    1,
    o.seller_id;


-- VIEW: SELLER RATING DISTRIBUTION

CREATE OR REPLACE VIEW vw_seller_rating_distribution AS

SELECT
    rating,

    COUNT(*) AS review_count,

    ROUND(
        COUNT(*) * 100.0
        / NULLIF(SUM(COUNT(*)) OVER (), 0),
        2
    ) AS review_share_pct

FROM reviews

GROUP BY rating;


-- VIEW: SELLER ACTIVITY SEGMENTS

CREATE OR REPLACE VIEW vw_seller_segments AS

SELECT
    CASE
        WHEN completed_orders = 0 THEN 'No completed sales'
        WHEN completed_orders BETWEEN 1 AND 2 THEN '1-2 sales'
        WHEN completed_orders BETWEEN 3 AND 5 THEN '3-5 sales'
        WHEN completed_orders BETWEEN 6 AND 10 THEN '6-10 sales'
        ELSE '10+ sales'
    END AS seller_segment,

    COUNT(*) AS seller_count,

    SUM(completed_orders) AS completed_orders,

    SUM(total_gmv) AS total_gmv

FROM vw_seller_performance

GROUP BY 1;
