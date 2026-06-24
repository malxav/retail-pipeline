"""
Database schema definition and high-speed data loading utilities.

This module sets up explicit table structures in SQL Server and uploads 
the transformed DataFrames in optimized batches to ensure data integrity.
"""

import pandas as pd
from sqlalchemy.engine import Engine
from sqlalchemy import text
from utils.logger import get_logger

logger = get_logger(__name__)

# Column definitions for each table.
# We define these explicitly rather than letting pandas infer them
# because pandas will sometimes choose NVARCHAR(MAX) for all strings,
# which wastes storage and slows queries on large tables.
TABLE_SCHEMAS = {
    'transactions': """
        CREATE TABLE transactions (
            InvoiceNo    NVARCHAR(20),
            StockCode    NVARCHAR(20),
            Description  NVARCHAR(255),
            Quantity     INT,
            InvoiceDate  DATETIME2,
            UnitPrice    DECIMAL(10,4),
            CustomerID   NVARCHAR(20),
            Country      NVARCHAR(100),
            LineRevenue  DECIMAL(10,4)
        )
    """,
    'rfm_customers': """
        CREATE TABLE rfm_customers (
            CustomerID      NVARCHAR(20) PRIMARY KEY,
            LastPurchaseDate DATE,
            Frequency        INT,
            Monetary         DECIMAL(12,2),
            Recency          INT,
            R_Score          TINYINT,
            F_Score          TINYINT,
            M_Score          TINYINT,
            RFM_Score        NVARCHAR(3),
            RFM_Combined     DECIMAL(5,2),
            Segment          NVARCHAR(50),
            Strategy         NVARCHAR(255)
        )
    """,
    'segment_summary': """
        CREATE TABLE segment_summary (
            Segment         NVARCHAR(50) PRIMARY KEY,
            CustomerCount   INT,
            AvgRecency      DECIMAL(8,2),
            AvgFrequency    DECIMAL(8,2),
            AvgMonetary     DECIMAL(12,2),
            TotalRevenue    DECIMAL(14,2),
            AvgRFMScore     DECIMAL(5,2),
            Strategy        NVARCHAR(255)
        )
    """
}


def create_table(engine: Engine, table_name: str) -> None:
    """Drops and recreates a table using the explicit schema definition."""
    with engine.begin() as conn:
        conn.execute(text(f'DROP TABLE IF EXISTS {table_name}'))
        conn.execute(text(TABLE_SCHEMAS[table_name]))
    logger.debug(f'Created table: {table_name}')


def write_dataframe(
    engine: Engine,
    df: pd.DataFrame,
    table_name: str,
    chunksize: int = 1000
) -> None:
    """
    Writes a pandas DataFrame directly into a SQL Server table in small batches.

    We use chunksize=1000 to split the upload into smaller groups of rows. 
    This prevents overloading the database with too much data all at once, 
    keeping the upload safe and fast.

    We use 'append' because the table framework was already built by the previous 
    function, and we turn off index tracking because the basic spreadsheet row 
    numbers are not needed in the database.
    """
    logger.info(f'Writing {len(df):,} rows to [{table_name}]')
    try:
        df.to_sql(
            name=table_name,
            con=engine,
            if_exists='append',
            index=False,
            chunksize=chunksize
        )
        logger.info(f'Successfully wrote {len(df):,} rows to [{table_name}]')
    except Exception as e:
        logger.error(f'Failed to write to [{table_name}]: {e}')
        raise


def run_load_pipeline(
    tables: dict[str, pd.DataFrame],
    engine: Engine
) -> None:
    """
    Creates tables and loads all DataFrames into SQL Server.
    It runs in a specific order: it creates and populates the large raw sales 
    table first, followed by the smaller calculated customer and group tables.
    """
    logger.info('Starting load pipeline')

    for table_name, df in tables.items():
        create_table(engine, table_name)
        write_dataframe(engine, df, table_name)

    logger.info('Load pipeline complete. All tables written to SQL Server.')