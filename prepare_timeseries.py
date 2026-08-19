"""
Time-Series Data Preparation Script for Transaction Data

This script converts raw transaction data into a clean time-series DataFrame
suitable for forecasting models (ARIMA, Prophet, LSTM, etc.).

Usage:
    from prepare_timeseries import prepare_timeseries
    df_ts = prepare_timeseries(transactions_df)
"""

import pandas as pd
import numpy as np
from typing import Union, Optional


def prepare_timeseries(
    df: pd.DataFrame,
    date_col: str = "date",
    amount_col: str = "amount",
    min_days_for_daily: int = 30,
    freq: str = "W",
    fill_value: float = 0.0
) -> pd.DataFrame:
    """
    Prepare time-series data from transaction records.

    Parameters
    ----------
    df : pd.DataFrame
        Raw transaction data with at least date and amount columns.
    date_col : str, default "date"
        Name of the date column (string or datetime-like).
    amount_col : str, default "amount"
        Name of the numeric amount column.
    min_days_for_daily : int, default 30
        Threshold: if number of unique days <= this, resample to weekly.
        If more days, keep daily frequency.
    freq : str, default "W"
        Resampling frequency when condition is met (e.g., "W", "M", "D").
        Pandas offset aliases: https://pandas.pydata.org/docs/user_guide/timeseries.html#offset-aliases
    fill_value : float, default 0.0
        Value to fill for timestamps with no transactions.

    Returns
    -------
    pd.DataFrame
        Clean time-series DataFrame with columns:
        - 'ds': timestamp (datetime64[ns])
        - 'y': total expenditure (float64)
        Sorted by 'ds', no missing timestamps in the range.
    """
    # 1. Validate input
    if df.empty:
        raise ValueError("Input DataFrame is empty.")
    if date_col not in df.columns or amount_col not in df.columns:
        raise KeyError(f"Required columns '{date_col}' and/or '{amount_col}' not found.")

    # 2. Copy & convert date column to datetime
    df = df.copy()
    df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
    df = df.dropna(subset=[date_col])

    # 3. Group by date -> daily total expenditure
    daily = (
        df.groupby(date_col)[amount_col]
        .sum()
        .reset_index()
        .rename(columns={date_col: "ds", amount_col: "y"})
        .sort_values("ds")
        .reset_index(drop=True)
    )

    # 4. Determine frequency & resample if needed
    n_unique_days = daily["ds"].nunique()
    date_min, date_max = daily["ds"].min(), daily["ds"].max()

    if n_unique_days <= min_days_for_daily:
        # Create complete date range at target frequency
        full_range = pd.date_range(start=date_min, end=date_max, freq=freq, name="ds")
        # Reindex to fill missing timestamps
        daily = daily.set_index("ds").reindex(full_range, fill_value=fill_value).reset_index()
        daily.columns = ["ds", "y"]
    else:
        # Keep daily: ensure no gaps in daily range
        full_range = pd.date_range(start=date_min, end=date_max, freq="D", name="ds")
        daily = daily.set_index("ds").reindex(full_range, fill_value=fill_value).reset_index()
        daily.columns = ["ds", "y"]

    # 5. Ensure correct dtypes
    daily["ds"] = pd.to_datetime(daily["ds"])
    daily["y"] = daily["y"].astype(float)

    return daily


def load_transactions_from_csv(path: str, **kwargs) -> pd.DataFrame:
    """Convenience loader for CSV files."""
    return pd.read_csv(path, **kwargs)


def load_transactions_from_db(engine, table: str = "transactions") -> pd.DataFrame:
    """Convenience loader from SQL database."""
    query = f"SELECT date, amount FROM {table}"
    return pd.read_sql(query, engine)


# Example usage & quick test
if __name__ == "__main__":
    # Synthetic test data
    np.random.seed(42)
    dates = pd.date_range("2026-01-01", periods=15, freq="2D")  # 15 days over ~30 days
    amounts = np.random.uniform(50, 500, size=len(dates)).round(2)
    test_df = pd.DataFrame({"date": dates, "amount": amounts})

    print("=== Raw Transactions ===")
    print(test_df.to_string(index=False))

    # Prepare time-series
    ts_df = prepare_timeseries(test_df, min_days_for_daily=30)
    print("\n=== Prepared Time-Series (Weekly resampled, 15 days <= 30) ===")
    print(ts_df.to_string(index=False))

    # Test with more days (daily kept)
    dates_long = pd.date_range("2026-01-01", periods=60, freq="D")
    amounts_long = np.random.uniform(50, 500, size=len(dates_long)).round(2)
    test_df_long = pd.DataFrame({"date": dates_long, "amount": amounts_long})

    ts_df_daily = prepare_timeseries(test_df_long, min_days_for_daily=30)
    print(f"\n=== Daily kept (60 days > 30): {len(ts_df_daily)} rows, freq={pd.infer_freq(ts_df_daily['ds'])} ===")
    print(ts_df_daily.head(10).to_string(index=False))