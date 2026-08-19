"""
Burn Rate & Monthly Spending Extrapolation using Linear Regression

NOTE: Core logic moved to app/services/forecast.py (multi-method).
This module re-exports predict_month_end for backward compatibility.
"""

from app.services.forecast import predict_linear as predict_month_end  # re-export

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression


def predict_month_end(
    daily_df: pd.DataFrame,
    days_in_month: int = 30,
    date_col: str = "ds",
    amount_col: str = "y",
    verbose: bool = True,
) -> dict:
    """
    Predict total month-end spending via Linear Regression on cumulative trend.

    Parameters
    ----------
    daily_df : pd.DataFrame
        Daily time-series with columns:
        - date_col: timestamp (datetime64) or day index
        - amount_col: total expenditure for that day
        Must be sorted ascending by date.
    days_in_month : int, default 30
        Total days in the target month (28/29/30/31).
    date_col : str, default "ds"
        Name of date column.
    amount_col : str, default "y"
        Name of daily amount column.
    verbose : bool, default True
        Print burn-rate diagnostics.

    Returns
    -------
    dict
        {
            "burn_rate": float,        # slope: avg spend/day from trend
            "intercept": float,        # baseline offset
            "predicted_total": float,  # extrapolated end-of-month total
            "days_observed": int,      # n days of data seen
            "last_day_index": int,     # max day index used
            "model": LinearRegression  # fitted model (for reuse)
        }
    """
    # 1. Sort & derive day-of-month index (X)
    df = daily_df.copy().sort_values(date_col).reset_index(drop=True)

    # If date_col is datetime, extract day number; else treat value as index
    if pd.api.types.is_datetime64_any_dtype(df[date_col]):
        df["day_index"] = df[date_col].dt.day
    else:
        # Assume already sequential day numbers (1,2,3...) or use position
        df["day_index"] = range(1, len(df) + 1)

    # 2. Cumulative spending (y) — smoother trajectory
    df["cumulative"] = df[amount_col].cumsum()

    # 3. Prepare X (2D: n×1) and y (1D)
    X = df["day_index"].values.reshape(-1, 1)
    y = df["cumulative"].values

    # 4. Fit Linear Regression: y = slope * day + intercept
    model = LinearRegression()
    model.fit(X, y)

    burn_rate = float(model.coef_[0])      # slope = VND/day (burn rate)
    intercept = float(model.intercept_)

    # 5. Extrapolate to final day of month
    final_day = np.array([[days_in_month]])
    predicted_total = float(model.predict(final_day)[0])

    if verbose:
        print(f"[Burn Rate] Slope (avg spend/day): {burn_rate:,.2f} VND")
        print(f"[Baseline] Intercept: {intercept:,.2f} VND")
        print(f"[Observed] Days seen: {len(df)} (from day {int(X.min())} to {int(X.max())})")
        print(f"[Forecast] Predicted total by day {days_in_month}: {predicted_total:,.2f} VND")

    return {
        "burn_rate": burn_rate,
        "intercept": intercept,
        "predicted_total": predicted_total,
        "days_observed": len(df),
        "last_day_index": int(X.max()),
        "model": model,
    }


# ---------------------------------------------------------------------------
# Example execution
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    np.random.seed(42)

    # Simulate data STARTING FROM DAY 24 (mid-month, as in curriculum)
    # Volatile daily amounts, but cumulative trend is what we model
    day_start = 24
    days_in_month = 30
    n_days = days_in_month - day_start + 1  # days 24..30 inclusive

    dates = pd.date_range("2026-08-24", periods=n_days, freq="D")
    # Daily spend with noise around a ~200k/day burn rate
    daily_amounts = np.random.normal(loc=200_000, scale=40_000, size=n_days).round(2)
    daily_amounts = np.abs(daily_amounts)  # no negative spend

    daily_df = pd.DataFrame({"ds": dates, "y": daily_amounts})

    print("=== Raw daily spending (starting day 24) ===")
    print(daily_df.to_string(index=False))
    print()

    # Run prediction
    result = predict_month_end(daily_df, days_in_month=days_in_month, verbose=True)

    print("\n=== Summary ===")
    print(f"Estimated month-end total: {result['predicted_total']:,.2f} VND")
    print(f"Average burn rate: {result['burn_rate']:,.2f} VND/day")
