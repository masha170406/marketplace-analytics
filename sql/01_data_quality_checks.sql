-- TABLE ROW COUNTS

SELECT 'users' AS table_name, COUNT(*) AS row_count FROM users
UNION ALL
SELECT 'categories', COUNT(*) FROM categories
UNION ALL
SELECT 'listings', COUNT(*) FROM listings
UNION ALL
SELECT 'listing_status_history', COUNT(*) FROM listing_status_history
UNION ALL
SELECT 'orders', COUNT(*) FROM orders
UNION ALL
SELECT 'order_items', COUNT(*) FROM order_items
UNION ALL
SELECT 'order_status_history', COUNT(*) FROM order_status_history
UNION ALL
SELECT 'payments', COUNT(*) FROM payments
UNION ALL
SELECT 'reviews', COUNT(*) FROM reviews
ORDER BY table_name;


-- ORDERS WITHOUT ORDER ITEMS

SELECT COUNT(*) AS orders_without_items
FROM orders o
LEFT JOIN order_items oi
    ON o.order_id = oi.order_id
WHERE oi.order_id IS NULL;


-- ORDER SUBTOTAL VALIDATION

SELECT
    o.order_id,
    o.item_subtotal,
    SUM(oi.item_price) AS calculated_subtotal
FROM orders o
JOIN order_items oi
    ON o.order_id = oi.order_id
GROUP BY o.order_id, o.item_subtotal
HAVING o.item_subtotal <> SUM(oi.item_price);


-- ORDER TOTAL VALIDATION

SELECT
    order_id,
    item_subtotal,
    buyer_fee,
    shipping_fee,
    total_amount,
    item_subtotal + buyer_fee + shipping_fee AS calculated_total
FROM orders
WHERE total_amount <> (
    item_subtotal + buyer_fee + shipping_fee
);


-- INVALID BUYER / SELLER RELATIONSHIPS

SELECT COUNT(*) AS invalid_orders
FROM orders
WHERE buyer_id = seller_id;


-- COMPLETED ORDERS WITHOUT SUCCESSFUL PAYMENTS

SELECT COUNT(*) AS completed_orders_without_payment
FROM orders o
JOIN order_statuses os
    ON o.order_status_id = os.order_status_id
WHERE os.status_name IN (
    'paid',
    'shipped',
    'delivered',
    'completed',
    'refunded'
)
AND NOT EXISTS (
    SELECT 1
    FROM payments p
    JOIN payment_statuses ps
        ON p.payment_status_id = ps.payment_status_id
    WHERE p.order_id = o.order_id
      AND ps.status_name = 'successful'
);


-- INVALID REVIEWS

SELECT COUNT(*) AS invalid_reviews
FROM reviews r
JOIN orders o
    ON r.order_id = o.order_id
JOIN order_statuses os
    ON o.order_status_id = os.order_status_id
WHERE os.status_name <> 'completed'
   OR r.reviewer_id <> o.buyer_id
   OR r.reviewee_id <> o.seller_id;


-- DUPLICATE LISTING PURCHASES

SELECT
    listing_id,
    COUNT(*) AS purchase_count
FROM order_items
GROUP BY listing_id
HAVING COUNT(*) > 1;


-- DATE RANGE CHECK

SELECT
    MIN(created_at) AS first_order,
    MAX(created_at) AS last_order,
    COUNT(*) AS total_orders
FROM orders;


-- ORDER STATUS DISTRIBUTION

SELECT
    os.status_name,
    COUNT(*) AS order_count,
    ROUND(
        COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (),
        2
    ) AS percentage
FROM orders o
JOIN order_statuses os
    ON o.order_status_id = os.order_status_id
GROUP BY os.status_name
ORDER BY order_count DESC;
