"""
Unit tests for the data cleaning and preprocessing pipeline.

This module validates that the transformation and cleaning operations properly 
enforce explicit data thresholds, discard bad records, and correctly compute 
derived fields like customer transaction revenue.
"""

import pandas as pd
import pytest
from pipeline.clean import (
    remove_null_customers,
    remove_cancelled_orders,
    remove_invalid_quantities,
    remove_invalid_prices,
    add_revenue_column
)


@pytest.fixture
def sample_df():
    """
    Creates a temporary, fake dataset to use across all the data tests.

    This mock data contains intentional errors—like missing customer IDs, 
    negative numbers, and extreme values—so we can verify that our cleaning 
    functions successfully catch and isolate them.
    """
    return pd.DataFrame({
        'InvoiceNo':  ['536365', '536366', 'C536367', '536368', '536369'],
        'CustomerID': ['17850',  None,     '17851',   '17852',  '17853'],
        'Quantity':   [6,        3,        -2,        5,        10000],
        'UnitPrice':  [2.55,     1.00,     3.00,      0.00,     1.50],
        'LineRevenue':[0,        0,        0,         0,        0],
        'InvoiceDate': pd.to_datetime(['2011-01-01'] * 5),
        'Description': ['Item A'] * 5,
        'StockCode':   ['001'] * 5,
        'Country':     ['United Kingdom'] * 5
    })


def test_remove_null_customers(sample_df):
    # Verifies that rows missing a Customer ID are completely dropped.
    result = remove_null_customers(sample_df)
    assert result['CustomerID'].isnull().sum() == 0
    assert len(result) == 4


def test_remove_cancelled_orders(sample_df):
    # Verifies that receipts starting with a 'C' (cancellations) are filtered out.
    result = remove_cancelled_orders(sample_df)
    assert not result['InvoiceNo'].str.startswith('C').any()
    assert len(result) == 4


def test_remove_invalid_quantities(sample_df):
    # Verifies that negative counts and extreme order sizes are deleted.
    result = remove_invalid_quantities(sample_df)
    assert (result['Quantity'] >= 1).all()
    assert (result['Quantity'] <= 10_000).all()


def test_remove_invalid_prices(sample_df):
    # Verifies that items marked with free or negative prices are excluded.
    result = remove_invalid_prices(sample_df)
    assert (result['UnitPrice'] > 0).all()


def test_add_revenue_column(sample_df):
    # Verifies that line-item revenue calculates exactly to (Quantity × UnitPrice).
    sample_df['Quantity'] = 6
    sample_df['UnitPrice'] = 2.55
    result = add_revenue_column(sample_df)
    assert result['LineRevenue'].iloc[0] == pytest.approx(15.30)