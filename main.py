import logging
from etl.extract import extract
from etl.transform import transform
from etl.load import load

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger("main")


def main():
    log.info("Pipeline started")
    raw = extract()
    tables = transform(raw)
    load(tables)
    log.info("Pipeline finished")


if __name__ == "__main__":
    main()