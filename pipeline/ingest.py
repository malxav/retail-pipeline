"""
Data ingestion and early-stage diagnostics for the raw retail dataset.

This module handles the initial loading of the source Excel data into memory, 
enforcing strict data types for critical identifiers while generating diagnostic 
summaries for pipeline development and auditing.
"""

import pandas as pd
from pathlib import Path
from config import RAW_FILE
from utils.logger import get_logger

logger = get_logger(__name__)


def load_raw_data(filepath: Path = RAW_FILE) -> pd.DataFrame:
    """
    Loads the raw Online Retail Excel file into a DataFrame.

    Key decisions made here:
    - dtype={'CustomerID': str} prevents pandas from reading CustomerID
      as float64, which would silently convert 17850 to 17850.0 and
      then to '17850.0' when cast back to string. THIS COULD BREAK JOINS!

    - We load InvoiceDate as-is (datetime64) since pandas handles it correctly.

    - We don't do ANY cleaning here. Ingest does one thing: load the file.
      For cleaning logic, check clean.py
    """
    logger.info(f'Loading raw data from {filepath}')

    if not filepath.exists():
        logger.error(f'Raw data file not found: {filepath}')
        raise FileNotFoundError(
            f'Expected raw data at {filepath}. '
            f'Download the UCI Online Retail Dataset and place it in /data/'
        )

    try:
        df = pd.read_excel(
            filepath,
            dtype={'CustomerID': str},
            engine='openpyxl'
        )
        logger.info(f'Loaded {len(df):,} rows × {len(df.columns)} columns')
        logger.debug(f'Columns: {list(df.columns)}')
        logger.debug(f'Memory usage: {df.memory_usage(deep=True).sum() / 1e6:.1f} MB')
        return df

    except Exception as e:
        logger.error(f'Failed to read Excel file: {e}')
        raise


def get_data_summary(df: pd.DataFrame) -> None:
    """
    Logs a diagnostic summary of the raw dataset.
    Called once after ingest, never in production pipeline runs.
    Useful during development and when onboarding new data.
    """
    logger.info('=== Raw Data Summary ===')
    logger.info(f'Shape: {df.shape}')
    logger.info(f'Date range: {df["InvoiceDate"].min()} to {df["InvoiceDate"].max()}')
    logger.info(f'Unique invoices: {df["InvoiceNo"].nunique():,}')
    logger.info(f'Unique customers: {df["CustomerID"].nunique():,}')
    logger.info(f'Unique countries: {df["Country"].nunique():,}')

    null_counts = df.isnull().sum()
    nulls = null_counts[null_counts > 0]
    if len(nulls) > 0:
        logger.warning(f'Null values found:\n{nulls}')
    else:
        logger.info('No null values in raw data')