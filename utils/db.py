"""
Database connectivity and schema validation utilities.

This module initializes the SQLAlchemy engine, verifies connection stability, 
and provides helper functions to check database state during the pipeline execution.
"""

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from config import DB_CONNECTION_STRING
from utils.logger import get_logger

logger = get_logger(__name__)


def get_engine() -> Engine:
    """
    Creates and returns a SQLAlchemy engine connected to SQL Server.
    
    Chose to use SQLAlchemy rather than raw pyodbc because it gives us:
    - A clean ORM-compatible interface
    - pandas .to_sql() integration (write DataFrames directly to tables)
    - Connection pooling handled automatically
    - Database-agnostic syntax for future portability
    """
    try:
        engine = create_engine(DB_CONNECTION_STRING)
        # Test the connection immediately so we fail fast here
        with engine.connect() as conn:
            conn.execute(text('SELECT 1'))
        logger.info(f'Database connection established: {DB_CONNECTION_STRING.split("?")[0]}')
        return engine
    except Exception as e:
        logger.error(f'Failed to connect to database: {e}')
        raise


def table_exists(engine: Engine, table_name: str) -> bool:
    """Check if a table exists in the database."""
    with engine.connect() as conn:
        result = conn.execute(text(
            f"SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES "
            f"WHERE TABLE_NAME = '{table_name}'"
        ))
        return result.scalar() > 0