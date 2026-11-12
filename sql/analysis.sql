-- Q1: Monthly revenue and growth (delivered orders, full-coverage months only, see finding 9)
WITH monthly AS (
  SELECT d.year, d.month, ROUND(SUM(f.price), 0) AS revenue
  FROM fact_order_items f
  JOIN dim_date d ON f.purchase_date_key = d.date_key
  WHERE f.order_status = 'delivered'
    AND d.date BETWEEN '2017-01-01' AND '2018-08-31'
  GROUP BY d.year, d.month
)
SELECT year, month, revenue,
       ROUND(100.0 * (revenue - LAG(revenue) OVER (ORDER BY year, month))
             / LAG(revenue) OVER (ORDER BY year, month), 1) AS mom_growth_pct
FROM monthly
ORDER BY year, month;

-- Q2: Repeat-purchase rate (finding 1: customer_unique_id, not customer_id)
WITH per_customer AS (
  SELECT customer_unique_id, COUNT(DISTINCT order_id) AS n_orders
  FROM fact_order_items
  WHERE order_status = 'delivered'
  GROUP BY customer_unique_id
)
SELECT COUNT(*) AS customers,
       SUM(CASE WHEN n_orders > 1 THEN 1 ELSE 0 END) AS repeat_customers,
       ROUND(100.0 * SUM(CASE WHEN n_orders > 1 THEN 1 ELSE 0 END) / COUNT(*), 2) AS repeat_rate_pct
FROM per_customer;

-- Q3: Top 10 categories by revenue, with average review score
SELECT p.category_en,
       ROUND(SUM(f.price), 0) AS revenue,
       ROUND(AVG(f.review_score), 2) AS avg_review,
       RANK() OVER (ORDER BY SUM(f.price) DESC) AS revenue_rank
FROM fact_order_items f
JOIN dim_product p ON f.product_id = p.product_id
WHERE f.order_status = 'delivered'
GROUP BY p.category_en
ORDER BY revenue DESC
LIMIT 10;

-- Q4: Late deliveries and review score
SELECT is_late,
       COUNT(*) AS items,
       ROUND(AVG(review_score), 2) AS avg_review
FROM fact_order_items
WHERE order_status = 'delivered' AND is_late IS NOT NULL
GROUP BY is_late;

-- Q5: Average delivery days by customer state
SELECT c.state,
       COUNT(*) AS items,
       ROUND(AVG(f.delivery_days), 1) AS avg_delivery_days
FROM fact_order_items f
JOIN dim_customer c ON f.customer_unique_id = c.customer_unique_id
WHERE f.delivery_days IS NOT NULL
GROUP BY c.state
HAVING COUNT(*) >= 500
ORDER BY avg_delivery_days DESC;