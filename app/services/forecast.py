"""
Forecast Service - Multiple models for monthly spending extrapolation

Methods:
  1. linear    : Linear Regression on CUMULATIVE spending (baseline, burn_rate.py logic)
  2. seasonal  : Weekday/weekend-aware projection (captures weekly seasonality)
  3. arima     : ARIMA on daily amounts (captures trend + seasonality, robust to noise)

All return a dict with: predicted_total, burn_rate_per_day (approx),
days_observed, last_day_index, method.
"""

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from datetime import date

try:
    from statsmodels.tsa.arima.model import ARIMA
    HAS_ARIMA = True
except ImportError:
    HAS_ARIMA = False


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _prepare(df, date_col="ds", amount_col="y"):
    df = df.copy().sort_values(date_col).reset_index(drop=True)
    if pd.api.types.is_datetime64_any_dtype(df[date_col]):
        df["day_index"] = df[date_col].dt.day
        year = int(df[date_col].dt.year.iloc[0])
        month = int(df[date_col].dt.month.iloc[0])
    else:
        df["day_index"] = range(1, len(df) + 1)
        year = month = None
    df["cumulative"] = df[amount_col].cumsum()
    return df, year, month


# ---------------------------------------------------------------------------
# Method 1: LINEAR (cumulative) — baseline
# ---------------------------------------------------------------------------
def predict_linear(daily_df, days_in_month=30, date_col="ds", amount_col="y", verbose=False):
    df, _, _ = _prepare(daily_df, date_col, amount_col)
    X = df["day_index"].values.reshape(-1, 1)
    y = df["cumulative"].values

    model = LinearRegression()
    model.fit(X, y)
    burn_rate = float(model.coef_[0])
    final_day = np.array([[days_in_month]])
    predicted_total = float(model.predict(final_day)[0])

    if verbose:
        print(f"[Linear] burn_rate={burn_rate:,.2f} VND/day | predicted={predicted_total:,.2f}")
    return {
        "method": "linear",
        "burn_rate_per_day": round(burn_rate, 2),
        "predicted_total": round(predicted_total, 2),
        "days_observed": len(df),
        "last_day_index": int(df["day_index"].max()),
        "observed_total": round(float(df[amount_col].sum()), 2),
    }


# ---------------------------------------------------------------------------
# Method 2: SEASONAL (weekday / weekend aware)
# ---------------------------------------------------------------------------
def predict_seasonal(daily_df, days_in_month=30, year=None, month=None,
                     date_col="ds", amount_col="y", verbose=False):
    df, y_inf, m_inf = _prepare(daily_df, date_col, amount_col)
    if year is None:
        year, month = y_inf, m_inf
    if year is None:
        # fallback: assume current month pattern using day-of-week of given dates
        year, month = 2026, 8

    df["dow"] = df[date_col].dt.dayofweek
    df["is_weekend"] = (df["dow"] >= 5).astype(int)

    weekday_vals = df.loc[df["is_weekend"] == 0, amount_col]
    weekend_vals = df.loc[df["is_weekend"] == 1, amount_col]

    weekday_avg = float(weekday_vals.mean()) if len(weekday_vals) else float(df[amount_col].mean())
    weekend_avg = float(weekend_vals.mean()) if len(weekend_vals) else float(df[amount_col].mean())

    observed_total = float(df[amount_col].sum())
    last_day = int(df["day_index"].max())

    # Project remaining days using their actual weekday type
    projected = 0.0
    for d in range(last_day + 1, days_in_month + 1):
        dt = date(year, month, d)
        is_wknd = 1 if dt.weekday() >= 5 else 0
        projected += weekend_avg if is_wknd else weekday_avg

    predicted_total = observed_total + projected
    approx_burn = predicted_total / days_in_month

    if verbose:
        print(f"[Seasonal] weekday_avg={weekday_avg:,.2f} | weekend_avg={weekend_avg:,.2f}")
        print(f"[Seasonal] predicted={predicted_total:,.2f}")
    return {
        "method": "seasonal",
        "burn_rate_per_day": round(approx_burn, 2),
        "weekday_avg": round(weekday_avg, 2),
        "weekend_avg": round(weekend_avg, 2),
        "predicted_total": round(predicted_total, 2),
        "days_observed": len(df),
        "last_day_index": last_day,
        "observed_total": round(observed_total, 2),
    }


# ---------------------------------------------------------------------------
# Method 3: ARIMA (on daily amounts)
# ---------------------------------------------------------------------------
def predict_arima(daily_df, days_in_month=30, date_col="ds", amount_col="y", verbose=False):
    df, _, _ = _prepare(daily_df, date_col, amount_col)
    y = df[amount_col].values.astype(float)
    observed_total = float(y.sum())
    n = len(y)
    remaining = days_in_month - n

    # Fallback to linear if ARIMA unavailable or too little data
    if not HAS_ARIMA or n < 5 or remaining <= 0:
        return predict_linear(daily_df, days_in_month, date_col, amount_col, verbose)

    try:
        # order (p,d,q): d=1 removes trend -> good for increasing/decreasing
        model = ARIMA(y, order=(1, 1, 1))
        fit = model.fit()
        if remaining > 0:
            fc = fit.forecast(steps=remaining)
            forecast_sum = float(np.sum(fc))
        else:
            forecast_sum = 0.0
        predicted_total = observed_total + forecast_sum
    except Exception as e:
        if verbose:
            print(f"[ARIMA] fallback to linear: {e}")
        return predict_linear(daily_df, days_in_month, date_col, amount_col, verbose)

    if verbose:
        print(f"[ARIMA] forecast_remaining={forecast_sum:,.2f} | predicted={predicted_total:,.2f}")
    return {
        "method": "arima",
        "burn_rate_per_day": round(predicted_total / days_in_month, 2),
        "predicted_total": round(predicted_total, 2),
        "days_observed": n,
        "last_day_index": int(df["day_index"].max()),
        "observed_total": round(observed_total, 2),
    }


# ---------------------------------------------------------------------------
# Dispatcher
# ---------------------------------------------------------------------------
def forecast_total(method="linear", daily_df=None, days_in_month=30,
                   year=None, month=None, date_col="ds", amount_col="y", verbose=False):
    if method == "seasonal":
        return predict_seasonal(daily_df, days_in_month, year, month, date_col, amount_col, verbose)
    elif method == "arima":
        return predict_arima(daily_df, days_in_month, date_col, amount_col, verbose)
    else:
        return predict_linear(daily_df, days_in_month, date_col, amount_col, verbose)
