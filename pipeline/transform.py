"""
Orchestration layer for analytical features and segmentation data models.

This module acts as the bridge between clean data and final reports, pulling 
together the calculation of RFM metrics, scoring bins, and business playbooks 
into a structured collection of output tables.
"""

import pandas as pd
from analysis.rfm import compute_rfm_base, score_rfm
from analysis.segments import assign_segments, get_segment_summary
from utils.logger import get_logger

logger = get_logger(__name__)


def run_transform_pipeline(df: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """
    Runs all calculations to turn a clean transaction list into final analysis tables.
    """
    logger.info('Starting transform pipeline')

    # Call from rfm.py
    # Aggregates transaction-level data to customer-level RFM metrics.
    rfm = compute_rfm_base(df)
    # Assigns quintile scores (1-5) to each RFM dimension
    rfm = score_rfm(rfm)

    # Call from segments.py
    # Map RFM scores to segments
    rfm = assign_segments(rfm)
    # Produces an aggregated segment-level summary DataFrame
    segment_summary = get_segment_summary(rfm)

    logger.info(
        f'Transform complete. '
        f'Produced {len(rfm):,} customer RFM records '
        f'across {rfm["Segment"].nunique()} segments'
    )

    return {
        'transactions': df,
        'rfm_customers': rfm,
        'segment_summary': segment_summary
    }