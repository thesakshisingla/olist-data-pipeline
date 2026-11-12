# Olist Data Pipeline

A Python/SQL ETL pipeline that turns 7 raw CSV files from a Brazilian e-commerce marketplace
(~100K orders, 2016-2018) into a star-schema warehouse, with automated data quality tests.

## Architecture

```
CSV files -> extract.py -> transform.py -> load.py -> SQLite (star schema)
                                                   -> pytest quality checks
```

| Table | Type | Grain |
|---|---|---|
| fact_order_items | Fact | One row per order item (112,650 rows) |
| dim_customer | Dimension | One row per real customer (96,096) |
| dim_product, dim_seller, dim_date | Dimensions | |

## Data quality

Profiling found 12 issues, documented in [docs/data_quality.md](docs/data_quality.md). Examples:
- `customer_id` is per order, not per person: 99,441 IDs but only 96,096 real customers.
- 547 orders have multiple reviews; a naive join would duplicate rows and inflate revenue.
- 775 orders have no items and are excluded by the fact table's grain.

Each decision is implemented in `etl/transform.py`. The pipeline stops with an error if the fact
table's row count differs from the raw order items.

## Tests

10 pytest checks on the warehouse: key uniqueness, orphaned foreign keys, valid ranges,
NULL handling. I verified they catch regressions by temporarily keying the customer dimension
on `customer_id`; the uniqueness test failed (99,441 vs 96,096) and passed after the revert.

## Key findings (delivered orders)

- **Repeat purchases are rare:** only 2,801 of 93,358 customers (3.0%) ordered more than once, so the business depends on one-time buyers.
- **Late delivery hurts reviews:** 7.9% of items arrived late, and they average a review score of 2.55 vs 4.21 for on-time items.
- **Top category:** health_beauty leads with 1,233,132 BRL in revenue (avg review 4.19), followed by watches_gifts (1,166,177) and bed_bath_table (1,023,435).
- **Revenue trend:** monthly revenue grew from 111,798 BRL (Jan 2017) to roughly 840,000-980,000 BRL per month in 2018. November 2017 jumped 52.4% over October, likely a seasonal peak, then fell 26.5% in December.
- **Delivery time varies by region:** among states with at least 500 items, SP is fastest (8.3 days) and PA slowest (23.3 days).

Queries are in [sql/analysis.sql](sql/analysis.sql). Trend analysis uses 2017-01 to 2018-08 only,
because the other months have very few orders.

## How to run

1. Download the dataset from Kaggle ("Brazilian E-Commerce Public Dataset by Olist")
   and put the CSV files in `data/raw/`.
2. Install and run:
   ```bash
   python -m venv .venv
   .venv\Scripts\activate          # Mac/Linux: source .venv/bin/activate
   pip install -r requirements.txt
   python main.py
   pytest -v
   ```

## What I would improve next

- Add dbt for the transformations and built-in tests
- Orchestrate with Airflow
- Move from SQLite to PostgreSQL
- Add the payments table (aggregated to one row per order)