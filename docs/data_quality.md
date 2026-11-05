# Data quality findings

Dataset: Olist Brazilian E-commerce public dataset (9 CSV files, Sept 2016 - Oct 2018).
All numbers below were produced by profiling the raw files in `explore.ipynb`.

## 1. customer_id is per order, not per person
- Observation: customers has [99,441] rows with a unique customer_id, but only [96,096] distinct customer_unique_id. [VERIFY]
- Impact: a repeat-purchase rate based on customer_id would be 0%.
- Decision: dim_customer uses customer_unique_id as its key.

## 2. Undelivered orders have missing dates
- Observation: order_approved_at has [160] nulls, order_delivered_carrier_date [1,783], order_delivered_customer_date [2,965]. [VERIFY]
  These are mostly canceled, unavailable and shipped orders.
- Impact: delivery_days and is_late are undefined for them. Filling nulls with 0 would distort averages.
- Decision: keep NULL and compute delivery metrics only for delivered orders.

## 3. Some delivered orders have no delivery date
- Observation: [8] orders have status "delivered" but no order_delivered_customer_date. [VERIFY]
- Impact: status and date contradict each other.
- Decision: keep the rows, exclude them from delivery-time metrics, and cover this with a test.

## 4. Orders without any items
- Observation: 98,666 distinct orders appear in order_items, while orders has [99,441] rows, so [775] orders have no items. [VERIFY]
- Impact: an inner join from orders to items silently drops them, and order counts differ depending on the table used.
- Decision: the fact table's grain is one row per order item, so these orders are excluded. Documented as a known limitation.

## 5. Duplicated review_id and multiple reviews per order
- Observation: reviews has 99,224 rows but only 98,410 distinct review_id, so review_id is not a unique key. 547 orders have more than one review.
- Impact: joining reviews directly to order items would duplicate item rows and inflate revenue.
- Decision: keep only the latest review per order (by review_creation_date) before joining. Verified by asserting that the fact table row count equals the order_items row count.

## 6. Missing product attributes and category translations
- Observation: 610 of 32,951 products have no category. 2 categories have no English translation: pc_gamer and portateis_cozinha_e_preparadores_de_alimentos. Some column names contain typos (product_name_lenght, product_description_lenght).
- Impact: category analysis would drop these products or show NULL.
- Decision: fill category_en with "unknown" and rename the typo columns in the transform step.

## 7. One order can have several payments, and some payment data is odd
- Observation: 2,961 orders have more than one payment row. 9 payments have a value of 0 and 3 have payment_type "not_defined". Payment types: credit_card 76,795, boleto 19,784, voucher 5,775, debit_card 1,529, not_defined 3.
- Impact: joining payments to orders would duplicate order rows.
- Decision: payments are not joined into the fact table. If needed, aggregate to one row per order first.

## 8. Geolocation table has heavy duplication
- Observation: 1,000,163 rows, of which 261,831 are exact duplicates, but only 19,015 distinct zip prefixes.
- Impact: joining on zip prefix would multiply rows.
- Decision: not used in the warehouse for now. If needed, reduce to one row per zip prefix (average lat/lng).

## 9. Uneven time coverage
- Observation: orders span 2016-09-04 to 2018-10-17. 2016 has only 329 orders in total (4 in Sept, 324 in Oct, 1 in Dec, none in Nov), and 2018-09 and 2018-10 have only 16 and 4. Full-volume months run from 2017-01 (800) to 2018-08 (6,512).
- Impact: month-over-month growth for the sparse months is misleading (for example, Dec 2016 to Jan 2017 looks like +80,000%).
- Decision: trend analysis uses 2017-01 to 2018-08 only, and the README states this range.

## 10. Order status mix
- Observation: delivered 96,478 of 99,441 orders (97.0%). Others: shipped 1,107, canceled 625, unavailable 609, invoiced 314, processing 301, created 5, approved 2.
- Impact: including canceled orders overstates revenue.
- Decision: revenue and delivery KPIs filter on order_status = 'delivered'.

## 11. Free shipping items
- Observation: 383 order items have freight_value = 0.
- Impact: not errors (likely free shipping), but they lower freight averages.
- Decision: keep them and do not treat 0 as missing. Tests allow freight >= 0.

## 12. Seasonality spike in Nov 2017
- Observation: orders jump from 4,631 (Oct 2017) to 7,544 (Nov 2017), then fall to 5,673 in Dec.
- Impact: this is likely Black Friday. Month-over-month growth in Nov and Dec 2017 reflects a seasonal event, not a trend.
- Decision: note it in the analysis and don't present it as organic growth.