import logging
from pathlib import Path
import pandas as pd

logger = logging.getLogger(__name__)


def extract_csv(file_path: Path) -> pd.DataFrame:
    """Extract one CSV file into a Pandas DataFrame."""
    logger.info("Extracting %s", file_path.name)
    try:
        frame = pd.read_csv(file_path)
    except FileNotFoundError:
        logger.exception("Source file not found: %s", file_path)
        raise
    except pd.errors.EmptyDataError:
        logger.exception("Source file is empty: %s", file_path)
        raise
    logger.info("Extracted %d rows from %s", len(frame), file_path.name)
    return frame


def extract_all(raw_dir: Path) -> dict:
    """Read all source files required by this project."""
    names = ["customers", "products", "orders", "order_items"]
    return {name: extract_csv(raw_dir / f"{name}.csv") for name in names}
