"""
forecasting.py
==============
ML Forecasting Module — UAC Capacity Monitor

Two complementary models:
  1. Random Forest Regressor (sklearn)
     Uses engineered lag features to predict future system load.
     This is the primary ML model.

  2. Prophet (Facebook / Meta)
     Additive time-series model that captures trend + weekly +
     yearly seasonality automatically.
     Falls back gracefully if Prophet is not installed.

Usage
-----
    from forecasting import run_rf_forecast, run_prophet_forecast, FORECAST_TARGETS

Author: UAC Analytics Team
Version: 2.0.0
"""

import warnings
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error

warnings.filterwarnings("ignore")

# ── Targets exposed to the dashboard ─────────────────────────────────────────
FORECAST_TARGETS = {
    "Total System Load": "total_system_load",
    "HHS Care":          "hhs_care",
    "CBP Custody":       "cbp_custody",
}

# Shared test-set size for model evaluation
TEST_DAYS = 60


# ─────────────────────────────────────────────────────────────────────────────
# Feature Engineering
# ─────────────────────────────────────────────────────────────────────────────

_LAGS = (1, 7, 14, 30)

def _make_lag_features(series: pd.Series) -> pd.DataFrame:
    """
    Build a feature matrix from a time series using:
      - Lag values at 1, 7, 14, 30 days
      - 7-day rolling mean and std (lagged by 1 to avoid leakage)
      - 14-day rolling mean (lagged by 1)
      - Day-of-week and month (calendar signals)

    Returns a DataFrame with columns [y, lag_1, lag_7, ..., dow, month]
    after dropping rows with NaN (the first max(lag) rows).
    """
    df = pd.DataFrame({"y": series.values}, index=series.index)

    for lag in _LAGS:
        df[f"lag_{lag}"] = df["y"].shift(lag)

    df["roll_mean_7"]  = df["y"].rolling(7,  min_periods=1).mean().shift(1)
    df["roll_std_7"]   = df["y"].rolling(7,  min_periods=2).std().shift(1).fillna(0)
    df["roll_mean_14"] = df["y"].rolling(14, min_periods=1).mean().shift(1)
    df["dow"]          = df.index.dayofweek
    df["month"]        = df.index.month

    return df.dropna()


def _feature_names() -> list[str]:
    return (
        [f"lag_{l}" for l in _LAGS]
        + ["roll_mean_7", "roll_std_7", "roll_mean_14", "dow", "month"]
    )


def _recursive_forecast(model: RandomForestRegressor,
                         history: list[float],
                         horizon: int,
                         last_date: pd.Timestamp) -> pd.DataFrame:
    """
    Multi-step recursive forecast: each predicted value is appended to
    history and used as a feature for the next step.
    """
    h = list(history)          # mutable copy
    dates, preds = [], []

    for step in range(horizon):
        row = {
            "lag_1":        h[-1],
            "lag_7":        h[-7]  if len(h) >= 7  else h[0],
            "lag_14":       h[-14] if len(h) >= 14 else h[0],
            "lag_30":       h[-30] if len(h) >= 30 else h[0],
            "roll_mean_7":  np.mean(h[-7:]),
            "roll_std_7":   np.std(h[-7:]) if len(h) >= 7 else 0.0,
            "roll_mean_14": np.mean(h[-14:]) if len(h) >= 14 else np.mean(h),
            "dow":          (last_date + pd.Timedelta(days=step + 1)).dayofweek,
            "month":        (last_date + pd.Timedelta(days=step + 1)).month,
        }
        x = np.array([row[f] for f in _feature_names()]).reshape(1, -1)
        pred = float(model.predict(x)[0])
        pred = max(0.0, pred)
        h.append(pred)

        dates.append(last_date + pd.Timedelta(days=step + 1))
        preds.append(pred)

    return pd.DataFrame({"date": dates, "forecast": preds})


# ─────────────────────────────────────────────────────────────────────────────
# Model 1 — Random Forest
# ─────────────────────────────────────────────────────────────────────────────

def run_rf_forecast(
    df: pd.DataFrame,
    target_col: str,
    horizon: int,
) -> dict:
    """
    Train a Random Forest Regressor on lag-engineered features and
    produce a multi-step recursive forecast.

    Parameters
    ----------
    df         : processed DataFrame with a 'date' column
    target_col : column to forecast (e.g. 'total_system_load')
    horizon    : days to forecast forward

    Returns
    -------
    dict with keys:
      forecast_df  : pd.DataFrame  [date, forecast, lower, upper]
      metrics      : dict          {MAE, RMSE, MAPE, R2}
      importances  : pd.Series     feature importances (sorted asc)
      test_df      : pd.DataFrame  [date, actual, predicted] on hold-out
    """
    series = df.set_index("date")[target_col].dropna().asfreq("D").ffill()
    feat_df = _make_lag_features(series)

    X = feat_df[_feature_names()].values
    y = feat_df["y"].values
    dates = feat_df.index

    split = len(X) - TEST_DAYS
    X_train, X_test = X[:split], X[split:]
    y_train, y_test = y[:split], y[split:]
    dates_test       = dates[split:]

    # Train
    model = RandomForestRegressor(
        n_estimators=300,
        max_depth=12,
        min_samples_leaf=3,
        max_features="sqrt",
        random_state=42,
        n_jobs=-1,
    )
    model.fit(X_train, y_train)

    # Evaluate on held-out test set
    y_pred = model.predict(X_test)
    mae    = mean_absolute_error(y_test, y_pred)
    rmse   = np.sqrt(mean_squared_error(y_test, y_pred))
    mape   = float(np.mean(np.abs((y_test - y_pred) / np.maximum(y_test, 1))) * 100)
    ss_res = np.sum((y_test - y_pred) ** 2)
    ss_tot = np.sum((y_test - np.mean(y_test)) ** 2)
    r2     = 1 - ss_res / ss_tot if ss_tot > 0 else 0.0

    test_df = pd.DataFrame({
        "date":      dates_test,
        "actual":    y_test,
        "predicted": y_pred,
    })

    # Future forecast (recursive)
    forecast_df = _recursive_forecast(
        model, list(series.values), horizon, series.index[-1]
    )

    # Confidence band: ±1.96 × residual std, widening with horizon
    residual_std = np.std(y_test - y_pred)
    steps = np.arange(1, horizon + 1)
    uncertainty = residual_std * np.sqrt(steps / TEST_DAYS + 1)   # grows over time
    forecast_df["lower"] = (forecast_df["forecast"] - 1.96 * uncertainty).clip(lower=0)
    forecast_df["upper"] =  forecast_df["forecast"] + 1.96 * uncertainty

    # Feature importances
    importances = pd.Series(
        model.feature_importances_,
        index=[f.replace("_", " ").title() for f in _feature_names()],
    ).sort_values(ascending=True)

    return {
        "forecast_df":  forecast_df,
        "metrics":      {"MAE": round(mae, 1), "RMSE": round(rmse, 1),
                         "MAPE": round(mape, 1), "R²": round(r2, 3)},
        "importances":  importances,
        "test_df":      test_df,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Model 2 — Prophet
# ─────────────────────────────────────────────────────────────────────────────

def _prophet_available() -> bool:
    try:
        import prophet  # noqa: F401
        return True
    except ImportError:
        return False


def run_prophet_forecast(
    df: pd.DataFrame,
    target_col: str,
    horizon: int,
) -> dict | None:
    """
    Train a Prophet model and produce a horizon-day forecast.

    Returns None if Prophet is not installed (dashboard will show
    an install prompt and fall back to Random Forest).
    """
    if not _prophet_available():
        return None

    from prophet import Prophet  # type: ignore

    prophet_df = (
        df[["date", target_col]]
        .rename(columns={"date": "ds", target_col: "y"})
        .dropna()
    )

    train = prophet_df.iloc[:-TEST_DAYS].copy()
    test  = prophet_df.iloc[-TEST_DAYS:].copy()

    model = Prophet(
        changepoint_prior_scale=0.05,
        seasonality_mode="additive",
        yearly_seasonality=True,
        weekly_seasonality=True,
        daily_seasonality=False,
        interval_width=0.95,
    )
    model.fit(train, verbose=False)

    # Evaluate
    test_forecast = model.predict(test[["ds"]])
    y_test  = test["y"].values
    y_pred  = test_forecast["yhat"].values.clip(min=0)
    mae     = mean_absolute_error(y_test, y_pred)
    rmse    = np.sqrt(mean_squared_error(y_test, y_pred))
    mape    = float(np.mean(np.abs((y_test - y_pred) / np.maximum(y_test, 1))) * 100)
    ss_res  = np.sum((y_test - y_pred) ** 2)
    ss_tot  = np.sum((y_test - np.mean(y_test)) ** 2)
    r2      = 1 - ss_res / ss_tot if ss_tot > 0 else 0.0

    test_df = pd.DataFrame({
        "date":      test["ds"].values,
        "actual":    y_test,
        "predicted": y_pred,
    })

    # Full future forecast
    future   = model.make_future_dataframe(periods=horizon)
    full_fc  = model.predict(future)
    n_hist   = len(prophet_df)
    fc_slice = full_fc.iloc[n_hist:][["ds", "yhat", "yhat_lower", "yhat_upper"]].copy()
    fc_slice.columns = ["date", "forecast", "lower", "upper"]
    fc_slice["date"] = pd.to_datetime(fc_slice["date"])
    for col in ["forecast", "lower", "upper"]:
        fc_slice[col] = fc_slice[col].clip(lower=0)

    return {
        "forecast_df": fc_slice.reset_index(drop=True),
        "metrics":     {"MAE": round(mae, 1), "RMSE": round(rmse, 1),
                        "MAPE": round(mape, 1), "R²": round(r2, 3)},
        "test_df":     test_df,
        "model":       model,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Shared evaluation helper
# ─────────────────────────────────────────────────────────────────────────────

def format_metrics_table(rf_metrics: dict, prophet_metrics: dict | None) -> pd.DataFrame:
    """Return a side-by-side metrics comparison DataFrame."""
    rows = []
    for metric in ["MAE", "RMSE", "MAPE", "R²"]:
        row = {"Metric": metric, "Random Forest": rf_metrics.get(metric, "—")}
        if prophet_metrics:
            row["Prophet"] = prophet_metrics.get(metric, "—")
        rows.append(row)
    return pd.DataFrame(rows)
