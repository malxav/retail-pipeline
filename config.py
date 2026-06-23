"""
Global configuration settings and environment setup for the ETL pipeline.

This module initializes project file paths, builds the database connection string, 
and defines business logic thresholds for data validation and RFM scoring.
"""

from pathlib import Path
import os
from dotenv import load_dotenv

# Load .env file into environment variables
load_dotenv()

# ── Paths ──────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / 'data'
LOG_DIR  = BASE_DIR / 'logs'
OUTPUT_DIR = BASE_DIR / 'output' / 'reports'

RAW_FILE = DATA_DIR / 'online_retail.xlsx'

# Create directories if the dirs don't exist yet
LOG_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# ── Database ───────────────────────────────────────────────────────────────
DB_CONFIG = {
    'server':   os.getenv('DB_SERVER', 'localhost'),
    'database': os.getenv('DB_NAME', 'RetailPipeline'),
    'driver':   os.getenv('DB_DRIVER', 'ODBC Driver 17 for SQL Server'),
}

# Build the SQLAlchemy connection string
# Note!! fast_executemany=True is a pyodbc flag that makes bulk inserts 
# dramatically faster — instead of sending one row at a time it batches them. 
# On 500K rows this is the difference between 30 seconds and 3 minutes.
DB_CONNECTION_STRING = (
    f"mssql+pyodbc://{DB_CONFIG['server']}/{DB_CONFIG['database']}"
    f"?driver={DB_CONFIG['driver'].replace(' ', '+')}"
    f"&trusted_connection=yes"
    f"&fast_executemany=True"
)

# ── Data Quality Thresholds ────────────────────────────────────────────────
# These are explicit business rules, not magic numbers buried in code.
# If the business changes the definition of "valid", you change it here.
MIN_UNIT_PRICE = 0.0        # rows at or below this are removed
MIN_QUANTITY   = 1          # rows below this are removed after cancellations
MAX_QUANTITY   = 10_000     # absurd quantities flagged as likely data errors

# ── RFM Configuration ─────────────────────────────────────────────────────
# Snapshot date: the "as of" date for recency calculation.
# In production this would be date.today(). For a historical dataset
# we set it to the day after the last transaction so recency is meaningful
# rather than every customer appearing to have bought "years ago".
from datetime import date
RFM_SNAPSHOT_DATE = date(2011, 12, 10)   # one day after last transaction

# RFM scoring bins — quintiles (1-5).
# Score of 5 = best (most recent, most frequent, highest spend)
# Score of 1 = worst
RFM_BINS = 5