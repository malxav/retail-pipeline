"""
Data cleaning and rule-based preprocessing for the retail dataset.

This module orchestrates a sequential data cleansing pipeline, enforcing 
strict business rules to remove invalid records, isolate customer-linked 
transactions, and construct the revenue engine required for downstream RFM analysis.
"""

import pandas as pd
from config import MIN_UNIT_PRICE, MIN_QUANTITY, MAX_QUANTITY
from utils.logger import get_logger

logger = get_logger(__name__)


def remove_null_customers(df: pd.DataFrame) -> pd.DataFrame:
    """
    Drops rows where CustomerID is null.
    
    These are guest transactions with no customer identity which is
    unusable for RFM analysis. We log the count because 24.9%
    is a significant data loss that a stakeholder should know about.
    """
    original = len(df)
    df = df.dropna(subset=['CustomerID']).copy()
    removed = original - len(df)
    logger.info(
        f'Removed {removed:,} rows with null CustomerID '
        f'({removed / original:.1%} of dataset)'
    )
    return df


def remove_cancelled_orders(df: pd.DataFrame) -> pd.DataFrame:
    """
    Removes cancelled invoices (InvoiceNo starting with 'C').
    
    Cancelled orders represent reversed transactions. Including them
    would undercount revenue and distort frequency metrics. We remove
    the entire invoice because a cancellation nullifies the purchase.
    """
    original = len(df)
    cancelled_mask = df['InvoiceNo'].str.startswith('C', na=False)
    cancelled_invoices = df.loc[cancelled_mask, 'InvoiceNo'].nunique()
    df = df[~cancelled_mask].copy()
    removed = original - len(df)
    logger.info(
        f'Removed {removed:,} rows from {cancelled_invoices:,} '
        f'cancelled invoices (InvoiceNo prefix "C")'
    )
    return df


def remove_invalid_quantities(df: pd.DataFrame) -> pd.DataFrame:
    """
    Removes rows where Quantity is below MIN_QUANTITY or above MAX_QUANTITY.
    
    Negative quantities on non-cancelled invoices are manual adjustments
    or stock corrections and are not considered to be real customer purchases.
    Extremely high quantities (>10,000) are almost certainly data entry
    errors and would skew monetary value calculations.

    This value is set in config.py! Go check it out
    """
    original = len(df)
    negative = (df['Quantity'] < MIN_QUANTITY).sum()
    extreme  = (df['Quantity'] > MAX_QUANTITY).sum()

    df = df[
        (df['Quantity'] >= MIN_QUANTITY) &
        (df['Quantity'] <= MAX_QUANTITY)
    ].copy()

    removed = original - len(df)
    logger.info(
        f'Removed {removed:,} rows with invalid quantities '
        f'({negative:,} negative, {extreme:,} extreme >10k)'
    )
    return df


def remove_invalid_prices(df: pd.DataFrame) -> pd.DataFrame:
    """
    Removes rows where UnitPrice is zero or negative.
    
    Zero-price rows are samples, internal transfers, or write-offs.
    They generate no revenue and including them will inflate order frequency
    without contributing to monetary value, which distorts RFM scores.
    """
    original = len(df)
    df = df[df['UnitPrice'] > MIN_UNIT_PRICE].copy()
    removed = original - len(df)
    logger.info(
        f'Removed {removed:,} rows with UnitPrice <= {MIN_UNIT_PRICE}'
    )
    return df


def remove_duplicates(df: pd.DataFrame) -> pd.DataFrame:
    """
    Removes exact duplicate rows.
    
    Keeps the first occurrence. Duplicates in this dataset appear to be
    system re-submissions which are almost certainly data entry artifacts.
    """
    original = len(df)
    df = df.drop_duplicates().copy()
    removed = original - len(df)
    logger.info(f'Removed {removed:,} exact duplicate rows')
    return df


def clean_description(df: pd.DataFrame) -> pd.DataFrame:
    """
    Standardizes the 'Description' column.
    
    Strips leading/trailing whitespace and converts to title case.
    Not required for RFM but keeps the product dimension clean
    for the Power BI dashboard layer.
    """
    df['Description'] = (
        df['Description']
        .str.strip()
        .str.title()
        .fillna('Unknown')
    )
    logger.debug('Cleaned Description column: stripped whitespace, title-cased')
    return df


def add_revenue_column(df: pd.DataFrame) -> pd.DataFrame:
    """
    Adds a LineRevenue column: Quantity x UnitPrice.
    
    We compute this after all cleaning so we're never multiplying
    on dirty data. This column will be used for the monetary dimension in RFM.
    """
    df['LineRevenue'] = df['Quantity'] * df['UnitPrice']
    logger.debug(
        f'Added LineRevenue column. '
        f'Total revenue in clean dataset: £{df["LineRevenue"].sum():,.2f}'
    )
    return df


def run_cleaning_pipeline(df: pd.DataFrame) -> pd.DataFrame:
    """
    Run the data cleaning pipeline in a strict logical order:

    1. Drop nulls first to avoid wasting compute on junk rows.
    2. Filter out cancellations (InvoiceNo 'C') before looking at quantities, 
    treating them as a business rule rather than a data anomaly.
    3. Drop negative quantities to catch remaining invalid non-cancellation rows.
    4. Drop invalid prices ($0 or less) to ensure the revenue column is accurate.
    5. Drop duplicates after filtering out the noise.
    6. Clean up text formatting (the cosmetic stuff comes last).
    7. Calculate the revenue column now that all rows are clean and valid.
    """
    logger.info('Starting cleaning pipeline')
    original_count = len(df)

    df = remove_null_customers(df)
    df = remove_cancelled_orders(df)
    df = remove_invalid_quantities(df)
    df = remove_invalid_prices(df)
    df = remove_duplicates(df)
    df = clean_description(df)
    df = add_revenue_column(df)

    final_count = len(df)
    logger.info(
        f'Cleaning complete. '
        f'{original_count:,} → {final_count:,} rows '
        f'({original_count - final_count:,} removed, '
        f'{final_count / original_count:.1%} retained)'
    )
    return df