
-- VIEW: OVERALL REVIEW METRICS

CREATE OR REPLACE VIEW vw_review_metrics AS

SELECT
    COUNT(*) AS total_reviews,

    ROUND(AVG(rating), 2) AS average_rating,

    COUNT(*) FILTER (
        WHERE rating = 5
    ) AS five_star_reviews,

    COUNT(*) FILTER (
        WHERE rating = 4
    ) AS four_star_reviews,

    COUNT(*) FILTER (
        WHERE rating = 3
    ) AS three_star_reviews,

    COUNT(*) FILTER (
        WHERE rating = 2
    ) AS two_star_reviews,

    COUNT(*) FILTER (
        WHERE rating = 1
    ) AS one_star_reviews,

    ROUND(
        COUNT(*) FILTER (
            WHERE rating >= 4
        ) * 100.0 / NULLIF(COUNT(*), 0),
        2
    ) AS positive_review_rate_pct

FROM reviews;


-- VIEW: RATING DISTRIBUTION

CREATE OR REPLACE VIEW vw_review_rating_distribution AS

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


-- VIEW: SELLER REPUTATION

CREATE OR REPLACE VIEW vw_seller_reputation AS

SELECT
    u.user_id AS seller_id,

    u.username,

    u.country,

    COUNT(r.review_id) AS total_reviews,

    ROUND(
        AVG(r.rating),
        2
    ) AS average_rating,

    COUNT(r.review_id) FILTER (
        WHERE r.rating >= 4
    ) AS positive_reviews,

    COUNT(r.review_id) FILTER (
        WHERE r.rating <= 2
    ) AS negative_reviews,

    ROUND(
        COUNT(r.review_id) FILTER (
            WHERE r.rating >= 4
        ) * 100.0
        / NULLIF(COUNT(r.review_id), 0),
        2
    ) AS positive_review_rate_pct

FROM users u

LEFT JOIN reviews r
    ON u.user_id = r.reviewee_id

GROUP BY
    u.user_id,
    u.username,
    u.country;


-- VIEW: TOP RATED SELLERS
-- Minimum review threshold: 5

CREATE OR REPLACE VIEW vw_top_rated_sellers AS

SELECT
    seller_id,

    username,

    country,

    total_reviews,

    average_rating,

    positive_review_rate_pct,

    DENSE_RANK() OVER (
        ORDER BY average_rating DESC
    ) AS rating_rank

FROM vw_seller_reputation

WHERE total_reviews >= 5;


-- VIEW: MONTHLY REVIEW TRENDS

CREATE OR REPLACE VIEW vw_monthly_review_trends AS

SELECT
    DATE_TRUNC(
        'month',
        created_at
    )::date AS month,

    COUNT(*) AS total_reviews,

    ROUND(
        AVG(rating),
        2
    ) AS average_rating,

    COUNT(*) FILTER (
        WHERE rating >= 4
    ) AS positive_reviews,

    COUNT(*) FILTER (
        WHERE rating <= 2
    ) AS negative_reviews,

    ROUND(
        COUNT(*) FILTER (
            WHERE rating >= 4
        ) * 100.0
        / NULLIF(COUNT(*), 0),
        2
    ) AS positive_review_rate_pct

FROM reviews

GROUP BY 1;


-- VIEW: REVIEW PERFORMANCE BY COUNTRY

CREATE OR REPLACE VIEW vw_review_country_performance AS

SELECT
    u.country,

    COUNT(r.review_id) AS total_reviews,

    ROUND(
        AVG(r.rating),
        2
    ) AS average_rating,

    COUNT(r.review_id) FILTER (
        WHERE r.rating >= 4
    ) AS positive_reviews,

    COUNT(r.review_id) FILTER (
        WHERE r.rating <= 2
    ) AS negative_reviews,

    ROUND(
        COUNT(r.review_id) FILTER (
            WHERE r.rating >= 4
        ) * 100.0
        / NULLIF(COUNT(r.review_id), 0),
        2
    ) AS positive_review_rate_pct

FROM reviews r

JOIN users u
    ON r.reviewee_id = u.user_id

GROUP BY u.country;


-- VIEW: REVIEW RESPONSE TIME
-- Measures time between order completion and review creation

CREATE OR REPLACE VIEW vw_review_response_time AS

SELECT
    r.review_id,

    r.order_id,

    r.reviewer_id,

    r.reviewee_id,

    r.rating,

    o.completed_at,

    r.created_at AS review_created_at,

    ROUND(
        (
            EXTRACT(
                EPOCH FROM (r.created_at - o.completed_at)
            ) / 86400.0
        )::numeric,
        2
    ) AS days_until_review

FROM reviews r

JOIN orders o
    ON r.order_id = o.order_id

WHERE o.completed_at IS NOT NULL;


-- VIEW: REVIEW RESPONSE TIME SUMMARY

CREATE OR REPLACE VIEW vw_review_response_summary AS

SELECT
    COUNT(*) AS total_reviews,

    ROUND(
        AVG(days_until_review),
        2
    ) AS average_days_until_review,

    ROUND(
        PERCENTILE_CONT(0.5)
        WITHIN GROUP (
            ORDER BY days_until_review
        )::numeric,
        2
    ) AS median_days_until_review,

    ROUND(
        MIN(days_until_review),
        2
    ) AS minimum_days_until_review,

    ROUND(
        MAX(days_until_review),
        2
    ) AS maximum_days_until_review

FROM vw_review_response_time;
