import sqlite3
import pandas as pd
import pytest

DB = "olist.db"


@pytest.fixture(scope="module")
def con():
    c = sqlite3.connect(DB)
    yield c
    c.close()


def q(con, sql):
    return pd.read_sql(sql, con)


def test_fact_row_count_matches_raw_items(con):
    raw = pd.read_csv("data/raw/olist_order_items_dataset.csv")
    assert q(con, "SELECT COUNT(*) n FROM fact_order_items")["n"][0] == len(raw)


def test_fact_key_is_unique(con):
    dup = q(con, """SELECT COUNT(*) n FROM (
        SELECT order_id, order_item_id FROM fact_order_items
        GROUP BY 1, 2 HAVING COUNT(*) > 1)""")["n"][0]
    assert dup == 0


def test_customer_key_is_unique(con):
    df = q(con, "SELECT COUNT(*) n, COUNT(DISTINCT customer_unique_id) d FROM dim_customer")
    assert df["n"][0] == df["d"][0] == 96096


def test_no_null_foreign_keys(con):
    n = q(con, """SELECT COUNT(*) n FROM fact_order_items
        WHERE customer_unique_id IS NULL OR product_id IS NULL
           OR seller_id IS NULL OR purchase_date_key IS NULL""")["n"][0]
    assert n == 0


def test_foreign_keys_exist_in_dimensions(con):
    for col, dim in [("customer_unique_id", "dim_customer"), ("product_id", "dim_product"),
                     ("seller_id", "dim_seller"), ("purchase_date_key", "dim_date")]:
        dim_col = "date_key" if dim == "dim_date" else col
        n = q(con, f"""SELECT COUNT(*) n FROM fact_order_items f
            LEFT JOIN {dim} d ON f.{col} = d.{dim_col}
            WHERE d.{dim_col} IS NULL""")["n"][0]
        assert n == 0, f"{col} has orphans"


def test_prices_valid(con):
    assert q(con, "SELECT COUNT(*) n FROM fact_order_items WHERE price <= 0")["n"][0] == 0
    assert q(con, "SELECT COUNT(*) n FROM fact_order_items WHERE freight_value < 0")["n"][0] == 0


def test_review_scores_in_range(con):
    n = q(con, """SELECT COUNT(*) n FROM fact_order_items
        WHERE review_score IS NOT NULL AND review_score NOT BETWEEN 1 AND 5""")["n"][0]
    assert n == 0


def test_delivery_days_not_negative(con):
    n = q(con, "SELECT COUNT(*) n FROM fact_order_items WHERE delivery_days < 0")["n"][0]
    assert n == 0


def test_is_late_null_when_not_delivered(con):
    n = q(con, """SELECT COUNT(*) n FROM fact_order_items
        WHERE delivery_days IS NULL AND is_late IS NOT NULL""")["n"][0]
    assert n == 0


def test_dim_product_has_no_null_category(con):
    n = q(con, "SELECT COUNT(*) n FROM dim_product WHERE category_en IS NULL")["n"][0]
    assert n == 0