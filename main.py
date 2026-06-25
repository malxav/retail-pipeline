"""
Main entry point and orchestrator for the retail data pipeline.

This module coordinates the complete lifecycle of the application, driving the 
system through ingestion, data cleaning, feature transformation, database 
loading, and final reporting visualization.
"""

from pipeline.ingest import load_raw_data
from pipeline.clean import run_cleaning_pipeline
from pipeline.transform import run_transform_pipeline
from pipeline.load import run_load_pipeline
from visualization.charts import run_visualization_pipeline
from utils.db import get_engine
from utils.logger import get_logger

logger = get_logger(__name__)


def main() -> None:
    logger.info('=' * 60)
    logger.info('RETAIL ANALYTICS PIPELINE — START')
    logger.info('=' * 60)

    # Stage 1: Ingest
    df_raw = load_raw_data()

    # Stage 2: Clean
    df_clean = run_cleaning_pipeline(df_raw)

    # Stage 3: Transform
    tables = run_transform_pipeline(df_clean)

    # Stage 4: Load to SQL Server
    engine = get_engine()
    run_load_pipeline(tables, engine)

    # Stage 5: Visualize
    run_visualization_pipeline(tables['rfm_customers'])

    logger.info('=' * 60)
    logger.info('PIPELINE COMPLETE')
    logger.info('=' * 60)


if __name__ == '__main__':
    # The if __name__ == '__main__' guard means this file can be imported
    # by tests without executing the pipeline. Without it, importing
    # anything from main.py in a test would trigger a full pipeline run.
    main()