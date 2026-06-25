"""
Customer segmentation feature engineering via RFM analysis.

This module aggregates line-item transaction records into customer-level profile 
metrics and assigns automated quintile scores across the Recency, Frequency, 
and Monetary dimensions to isolate behavioral segments.

The values for the importance of the RFM dimensions can be modified below.
"""

# analysis/rfm.py
import pandas as pd
import numpy as np
from datetime import date
from config import RFM_SNAPSHOT_DATE, RFM_BINS # set as relative to December 10, 2011
from utils.logger import get_logger

logger = get_logger(__name__)


def compute_rfm_base(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregates transaction-level data to customer-level RFM metrics.

    This is the most important aggregation in the project. We go from
    392,690 rows (one per line item) to one row per customer.

    Three decisions worth understanding here are:
    1. Recency uses max(InvoiceDate) - most recent purchase, not first
    2. Frequency uses nunique(InvoiceNo) - distinct orders, not line items (aggregate to invoice-level)
    3. Monetary uses sum(LineRevenue) - total spend, not average order value
       Average order value is a separate metric; monetary for RFM is cumulative.
    """
    logger.info('Computing RFM base metrics')

    snapshot = pd.Timestamp(RFM_SNAPSHOT_DATE)

    rfm = (
        df.groupby('CustomerID')
        .agg(
            LastPurchaseDate=('InvoiceDate', 'max'),
            Frequency=('InvoiceNo', 'nunique'),
            Monetary=('LineRevenue', 'sum')
        )
        .reset_index()
    )

    # Recency = days between last purchase and snapshot
    # We use .dt.normalize() from Pandas to strip the time component so that
    # two purchases on the same day but different times both count as 0 days ago
    rfm['Recency'] = (
        snapshot - rfm['LastPurchaseDate'].dt.normalize()
    ).dt.days

    logger.info(f'RFM base computed for {len(rfm):,} unique customers')
    logger.debug(f'Recency range: {rfm["Recency"].min()} – {rfm["Recency"].max()} days')
    logger.debug(f'Frequency range: {rfm["Frequency"].min()} – {rfm["Frequency"].max()} orders')
    logger.debug(f'Monetary range: £{rfm["Monetary"].min():.2f} – £{rfm["Monetary"].max():.2f}')

    return rfm


def score_rfm(rfm: pd.DataFrame) -> pd.DataFrame:
    """
    This assigns quintile scores (1-5) to each RFM dimension.

    Recency is scored INVERSELY, so lower days = higher score.
    A customer who bought 1 day ago is better than one who bought 365 days ago.
    pd.qcut handles the quintile boundaries automatically.

    The labels=[5,4,3,2,1] for recency and [1,2,3,4,5] for F and M

    duplicates='drop' handles cases where many customers have identical values
    (e.g. many customers with Frequency=1) which would create duplicate bin edges.
    When that happens qcut merges those bins, so you may get fewer than 5 distinct
    scores on some dimensions. This is statistically honest; forcing 5 equal bins
    when the data doesn't support it would be misleading.
    """
    logger.info(f'Scoring RFM using {RFM_BINS} quantile bins')

    # 1. Recency: High days = Low score (Needs to be inverted)
    # We use labels=False, then invert the resulting integers
    r_bins = pd.qcut(rfm['Recency'], q=RFM_BINS, duplicates='drop', labels=False)
    rfm['R_Score'] = (RFM_BINS - 1) - r_bins + 1  # Inverts the 0-indexed bins and adds 1

    # 2. Frequency: Low orders = Low score
    rfm['F_Score'] = pd.qcut(rfm['Frequency'], q=RFM_BINS, duplicates='drop', labels=False) + 1

    # 3. Monetary: Low spend = Low score
    rfm['M_Score'] = pd.qcut(rfm['Monetary'], q=RFM_BINS, duplicates='drop', labels=False) + 1

    # Force everything to integer type just to be safe
    rfm['R_Score'] = rfm['R_Score'].astype(int)
    rfm['F_Score'] = rfm['F_Score'].astype(int)
    rfm['M_Score'] = rfm['M_Score'].astype(int)

    # Composite RFM score (e.g. '555', '312')
    rfm['RFM_Score'] = (
        rfm['R_Score'].astype(str) +
        rfm['F_Score'].astype(str) +
        rfm['M_Score'].astype(str)
    )

    # Combined numeric score for sorting and visualisation
    # Weighted: R slightly more important than F, F more than M
    # Reflecting the industry consensus that recency is 
    # the strongest predictor of future purchase behaviour
    rfm['RFM_Combined'] = (
        rfm['R_Score'] * 0.4 +
        rfm['F_Score'] * 0.35 +
        rfm['M_Score'] * 0.25
    )

    logger.info('RFM scoring complete')
    return rfm