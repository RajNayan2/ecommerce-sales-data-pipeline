import logging
from src.config import RAW_DIR, PROCESSED_DIR, REPORTS_DIR, DATABASE_URL
from src.extract import extract_all
from src.transform import transform_all
from src.database import create_db_engine
from src.load import load_tables
from src.report import generate_reports


def configure_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )


def run_pipeline():
    configure_logging()
    logger = logging.getLogger("ecommerce_pipeline")
    logger.info("Starting e-commerce sales data pipeline")

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    raw_tables = extract_all(RAW_DIR)
    valid_tables, rejected_tables = transform_all(raw_tables)

    for name, rejected in rejected_tables.items():
        output = PROCESSED_DIR / f"rejected_{name}.csv"
        if rejected.empty:
            output.unlink(missing_ok=True)
        else:
            rejected.to_csv(output, index=False)
            logger.warning("%s rejected rows saved to %s", len(rejected), output.name)

    for name, valid in valid_tables.items():
        logger.info("%s: %d valid rows", name, len(valid))

    engine = create_db_engine(DATABASE_URL)
    try:
        counts = load_tables(valid_tables, engine)
        daily, monthly = generate_reports(engine, REPORTS_DIR)
    finally:
        engine.dispose()

    logger.info("Load counts: %s", counts)
    logger.info("Generated %d daily and %d monthly report rows", len(daily), len(monthly))
    logger.info("Reports saved in %s", REPORTS_DIR)
    logger.info("Pipeline completed successfully")


if __name__ == "__main__":
    run_pipeline()
