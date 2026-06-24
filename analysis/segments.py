"""
Strategic customer segmentation and marketing playbook assignment.

This module maps raw RFM scores to human-readable behavioral segments using 
a simplified two-dimensional grid, attaches actionable marketing strategies, 
and aggregates performance metrics for reporting and dashboard visualization.
"""

import pandas as pd
from utils.logger import get_logger

logger = get_logger(__name__)

# Segment definitions based on R and F scores only.
# Monetary is intentionally excluded from segmentation logic 
# since it correlates strongly with frequency and adds complexity (3d matrix)
# without meaningfully changing the strategic recommendation per segment.
# Marketing can target "recent customer" and "at risk" users using the
# same playbook, regardless whether they spent $50 or $55.
#
# Each tuple is (R_Score, F_Score): Segment Name
# We use R and F as the primary axes because:
# - R tells you if they're still engaged
# - F tells you if engagement is habitual or one-off
SEGMENT_MAP = {
    (5, 5): 'Champion',
    (5, 4): 'Champion',
    (4, 5): 'Loyal Customer',
    (4, 4): 'Loyal Customer',
    (5, 3): 'Potential Loyalist',
    (4, 3): 'Potential Loyalist',
    (5, 2): 'Potential Loyalist',
    (5, 1): 'Recent Customer',
    (4, 1): 'Recent Customer',
    (4, 2): 'Recent Customer',
    (3, 5): 'At Risk',
    (3, 4): 'At Risk',
    (2, 5): 'Cannot Lose Them',
    (2, 4): 'Cannot Lose Them',
    (1, 5): 'Cannot Lose Them',
    (3, 3): 'Need Attention',
    (3, 2): 'About to Sleep',
    (3, 1): 'About to Sleep',
    (2, 3): 'Hibernating',
    (2, 2): 'Hibernating',
    (2, 1): 'Hibernating',
    (1, 4): 'Hibernating',
    (1, 3): 'Hibernating',
    (1, 2): 'Hibernating',
    (1, 1): 'Lost',
}

# Business strategies per segment
# Making the dashboard actionable rather than just descriptive
SEGMENT_STRATEGY = {
    'Champion':           'Reward them. They can become brand ambassadors.',
    'Loyal Customer':     'Upsell higher value products. Ask for reviews.',
    'Potential Loyalist': 'Offer loyalty programmes. Increase purchase frequency.',
    'Recent Customer':    'Provide onboarding support. Build the relationship early.',
    'Need Attention':     'Reactivate with limited-time offers.',
    'About to Sleep':     'Send win-back campaigns before it is too late.',
    'At Risk':            'Send personalised reactivation. Reconnect with value.',
    'Cannot Lose Them':   'Win them back immediately. High-value lapsed customers.',
    'Hibernating':        'Offer relevant products. Low-cost reactivation attempt.',
    'Lost':               'Revive interest with a strong offer or accept as churned.',
}


def assign_segments(rfm: pd.DataFrame) -> pd.DataFrame:
    """
    Map RFM scores to human-readable segments and adds strategy guidance.

    Uses a tuple key (R_Score, F_Score) for the lookup.
    Any combination not in SEGMENT_MAP falls back to 'Undefined' -
    this catches edge cases from duplicates='drop' in scoring which
    may produce scores outside the expected 1-5 range.
    """
    logger.info('Assigning customer segments')

    rfm['Segment'] = rfm.apply(
        lambda row: SEGMENT_MAP.get(
            (row['R_Score'], row['F_Score']), 'Undefined'
        ),
        axis=1
    )

    rfm['Strategy'] = rfm['Segment'].map(SEGMENT_STRATEGY)

    # Log segment distribution — this is the output a stakeholder cares about
    segment_counts = rfm['Segment'].value_counts()
    segment_pcts   = rfm['Segment'].value_counts(normalize=True) * 100

    logger.info('Segment distribution:')
    for seg in segment_counts.index:
        logger.info(
            f'  {seg:<22} {segment_counts[seg]:>5,} customers '
            f'({segment_pcts[seg]:.1f}%)'
        )

    undefined = (rfm['Segment'] == 'Undefined').sum()
    if undefined > 0:
        logger.warning(f'{undefined} customers could not be mapped to a segment')

    return rfm


def get_segment_summary(rfm: pd.DataFrame) -> pd.DataFrame:
    """
    Produces an aggregated segment-level summary DataFrame.
    This is what gets written to SQL Server as a separate table
    and used in Power BI for the segment overview visuals.
    """
    summary = (
        rfm.groupby('Segment')
        .agg(
            CustomerCount=('CustomerID', 'count'),
            AvgRecency=('Recency', 'mean'),
            AvgFrequency=('Frequency', 'mean'),
            AvgMonetary=('Monetary', 'mean'),
            TotalRevenue=('Monetary', 'sum'),
            AvgRFMScore=('RFM_Combined', 'mean')
        )
        .round(2)
        .reset_index()
    )

    summary['Strategy'] = summary['Segment'].map(SEGMENT_STRATEGY)
    summary = summary.sort_values('AvgRFMScore', ascending=False)

    logger.info(f'Segment summary built: {len(summary)} segments')
    return summary