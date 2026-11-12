import logging
from pathlib import Path
import pandas as pd

log = logging.getLogger(__name__)

FILES = {
    "orders": "olist_orders_dataset.csv",
    "items": "olist_order_items_dataset.csv",
    "customers": "olist_customers_dataset.csv",
    "products": "olist_products_dataset.csv",
    "sellers": "olist_sellers_dataset.csv",
    "reviews": "olist_order_reviews_dataset.csv",
    "trans": "product_category_name_translation.csv",
}

DATE_COLS = {
    "orders": ["order_purchase_timestamp", "order_approved_at",
               "order_delivered_carrier_date", "order_delivered_customer_date",
               "order_estimated_delivery_date"],
    "reviews": ["review_creation_date"],
}


def extract(raw_dir="data/raw"):
    """Read the raw CSV files into a dict of DataFrames."""
    raw = Path(raw_dir)
    tables = {}
    for name, filename in FILES.items():
        path = raw / filename
        if not path.exists():
            raise FileNotFoundError(f"Missing input file: {path}")
        tables[name] = pd.read_csv(path, parse_dates=DATE_COLS.get(name, []))
        log.info("Extracted %s: %d rows", name, len(tables[name]))
    return tables