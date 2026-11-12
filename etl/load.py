import logging
from sqlalchemy import create_engine

log = logging.getLogger(__name__)


def load(tables, db_url="sqlite:///olist.db"):
    engine = create_engine(db_url)
    for name, df in tables.items():
        df.to_sql(name, engine, if_exists="replace", index=False)
        log.info("Loaded %s: %d rows", name, len(df))