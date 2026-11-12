import logging
import pandas as pd

log = logging.getLogger(__name__)


def build_dim_customer(customers):
    # customer_id is per order; the real person is customer_unique_id
    return (customers.drop_duplicates("customer_unique_id")
            [["customer_unique_id", "customer_city", "customer_state"]]
            .rename(columns={"customer_city": "city", "customer_state": "state"}))


def build_dim_product(products, trans):
    df = products.merge(trans, on="product_category_name", how="left")
    df = df.rename(columns={"product_category_name_english": "category_en"})
    df["category_en"] = df["category_en"].fillna("unknown")
    return df[["product_id", "category_en", "product_weight_g",
               "product_length_cm", "product_height_cm", "product_width_cm"]]


def build_dim_seller(sellers):
    return (sellers.rename(columns={"seller_city": "city", "seller_state": "state"})
            [["seller_id", "city", "state"]])


def build_dim_date(orders):
    start = orders["order_purchase_timestamp"].min().normalize()
    end = orders["order_purchase_timestamp"].max().normalize()
    df = pd.DataFrame({"date": pd.date_range(start, end)})
    df["date_key"] = df["date"].dt.strftime("%Y%m%d").astype(int)
    df["year"] = df["date"].dt.year
    df["quarter"] = df["date"].dt.quarter
    df["month"] = df["date"].dt.month
    df["month_name"] = df["date"].dt.month_name()
    df["day_of_week"] = df["date"].dt.day_name()
    df["is_weekend"] = (df["date"].dt.dayofweek >= 5).astype(int)
    return df


def build_fact(orders, items, customers, reviews):
    # keep only the latest review per order (finding 5)
    reviews_latest = (reviews.sort_values("review_creation_date")
                      .drop_duplicates("order_id", keep="last")
                      [["order_id", "review_score"]])

    order_cols = ["order_id", "customer_id", "order_status",
                  "order_purchase_timestamp", "order_delivered_customer_date",
                  "order_estimated_delivery_date"]
    fact = (items
            .merge(orders[order_cols], on="order_id", how="left")
            .merge(customers[["customer_id", "customer_unique_id"]],
                   on="customer_id", how="left")
            .merge(reviews_latest, on="order_id", how="left"))

    fact["purchase_date_key"] = fact["order_purchase_timestamp"].dt.strftime("%Y%m%d").astype(int)
    delivered = fact["order_delivered_customer_date"]
    fact["delivery_days"] = (delivered - fact["order_purchase_timestamp"]).dt.days
    # NULL (not 0) when there is no delivery date (finding 2)
    fact["is_late"] = (delivered > fact["order_estimated_delivery_date"]).astype("float").where(delivered.notna())

    cols = ["order_id", "order_item_id", "customer_unique_id", "product_id",
            "seller_id", "purchase_date_key", "order_status", "price",
            "freight_value", "delivery_days", "is_late", "review_score"]
    fact = fact[cols]

    # sanity check: joins must not duplicate or drop rows
    if len(fact) != len(items):
        raise ValueError(f"Fact has {len(fact)} rows but order_items has {len(items)}")
    log.info("Built fact_order_items: %d rows", len(fact))
    return fact


def transform(t):
    return {
        "dim_customer": build_dim_customer(t["customers"]),
        "dim_product": build_dim_product(t["products"], t["trans"]),
        "dim_seller": build_dim_seller(t["sellers"]),
        "dim_date": build_dim_date(t["orders"]),
        "fact_order_items": build_fact(t["orders"], t["items"], t["customers"], t["reviews"]),
    }