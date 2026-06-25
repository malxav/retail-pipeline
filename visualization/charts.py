"""
Data visualization and reporting engine for customer analytics.

This module generates diagnostic plots and stakeholder charts, converting raw 
RFM metrics into clear visual trends, heatmaps, and distribution maps that 
validate the customer segmentation models.
"""

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns
from pathlib import Path
from config import OUTPUT_DIR
from utils.logger import get_logger

logger = get_logger(__name__)

# Global style
sns.set_theme(style='whitegrid', palette='Blues_d')
PALETTE = {
    'Champion':           '#1B3A6B',
    'Loyal Customer':     '#2E6DB4',
    'Potential Loyalist': '#5B9BD5',
    'Recent Customer':    '#2ECC71',
    'Need Attention':     '#F39C12',
    'About to Sleep':     '#E67E22',
    'At Risk':            '#E74C3C',
    'Cannot Lose Them':   '#C0392B',
    'Hibernating':        '#95A5A6',
    'Lost':               '#7F8C8D',
    'Undefined':          '#BDC3C7',
}


def _save(fig: plt.Figure, filename: str) -> None:
    # Saves figure to the output directory and closes it to free memory.
    path = OUTPUT_DIR / filename
    fig.savefig(path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    logger.info(f'Saved chart: {path}')


def plot_segment_distribution(rfm: pd.DataFrame) -> None:
    """
    Horizontal bar chart of customer count per segment.
    Ordered by RFM_Combined score so high-value segments will appear at the top.
    """
    order = (
        rfm.groupby('Segment')['RFM_Combined']
        .mean()
        .sort_values(ascending=True)
        .index
    )
    counts = rfm['Segment'].value_counts().reindex(order)
    colors = [PALETTE.get(s, '#BDC3C7') for s in counts.index]

    fig, ax = plt.subplots(figsize=(10, 6))
    bars = ax.barh(counts.index, counts.values, color=colors, edgecolor='white')

    # Add value labels on bars
    for bar, val in zip(bars, counts.values):
        ax.text(
            bar.get_width() + 10, bar.get_y() + bar.get_height() / 2,
            f'{val:,}', va='center', fontsize=9
        )

    ax.set_xlabel('Number of Customers', fontsize=11)
    ax.set_title('Customer Segment Distribution', fontsize=14, fontweight='bold', pad=15)
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'{x:,.0f}'))
    fig.tight_layout()
    _save(fig, 'segment_distribution.png')


def plot_rfm_heatmap(rfm: pd.DataFrame) -> None:
    """
    Heatmap of average Monetary value by R_Score x F_Score.
    The shows which score combinations drive the most revenue at a glance.
    """
    pivot = rfm.pivot_table(
        values='Monetary',
        index='R_Score',
        columns='F_Score',
        aggfunc='mean'
    ).sort_index(ascending=False)

    fig, ax = plt.subplots(figsize=(8, 6))
    sns.heatmap(
        pivot,
        annot=True,
        fmt=',.0f',
        cmap='Blues',
        linewidths=0.5,
        ax=ax,
        cbar_kws={'label': 'Avg Monetary Value (£)'}
    )
    ax.set_title('Average Revenue by R × F Score', fontsize=14, fontweight='bold', pad=15)
    ax.set_xlabel('Frequency Score', fontsize=11)
    ax.set_ylabel('Recency Score', fontsize=11)
    fig.tight_layout()
    _save(fig, 'rfm_heatmap.png')


def plot_monetary_distribution(rfm: pd.DataFrame) -> None:
    """
    Box plot of monetary value per segment. Reveals spread and outliers within each segment.
    Two segments can have the same average but very different distributions..
    """
    order = (
        rfm.groupby('Segment')['Monetary']
        .median()
        .sort_values(ascending=False)
        .index
    )

    fig, ax = plt.subplots(figsize=(12, 6))
    sns.boxplot(
        data=rfm,
        x='Segment',
        y='Monetary',
        order=order,
        hue='Segment',
        palette=PALETTE,
        legend=False,
        ax=ax,
        flierprops={'marker': 'o', 'markersize': 3, 'alpha': 0.3}
    )
    ax.set_yscale('log')    # IMPORTANT! log scale because monetary is heavily right-skewed
    ax.set_xlabel('')
    ax.set_ylabel('Total Customer Spend (£, log scale)', fontsize=11)
    ax.set_title('Monetary Value Distribution by Segment', fontsize=14, fontweight='bold', pad=15)
    plt.xticks(rotation=35, ha='right')
    fig.tight_layout()
    _save(fig, 'monetary_distribution.png')


def plot_recency_frequency_scatter(rfm: pd.DataFrame) -> None:
    """
    Scatter plot of Recency vs Frequency coloured by Segment.
    Shows clustering visually and validates that segmentation
    logic is producing well-separated groups.
    """
    fig, ax = plt.subplots(figsize=(11, 7))

    for segment, group in rfm.groupby('Segment'):
        ax.scatter(
            group['Recency'],
            group['Frequency'],
            c=PALETTE.get(segment, '#BDC3C7'),
            label=segment,
            alpha=0.5,
            s=15,
            edgecolors='none'
        )

    ax.set_xlabel('Recency (days since last purchase)', fontsize=11)
    ax.set_ylabel('Frequency (number of orders)', fontsize=11)
    ax.set_title('Customer Recency vs Frequency by Segment', fontsize=14, fontweight='bold', pad=15)
    ax.legend(
        title='Segment',
        bbox_to_anchor=(1.01, 1),
        loc='upper left',
        fontsize=8,
        title_fontsize=9
    )
    fig.tight_layout()
    _save(fig, 'recency_frequency_scatter.png')


def run_visualization_pipeline(rfm: pd.DataFrame) -> None:
    # Generates all charts.
    logger.info('Generating visualisations')
    plot_segment_distribution(rfm)
    plot_rfm_heatmap(rfm)
    plot_monetary_distribution(rfm)
    plot_recency_frequency_scatter(rfm)
    logger.info(f'All charts saved to {OUTPUT_DIR}')