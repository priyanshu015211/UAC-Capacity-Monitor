"""
forecasting.py
==============
ML Forecasting Module — UAC Capacity Monitor

Model: Random Forest Regressor (sklearn)
Uses engineered lag features to predict future system load.

Author: UAC Analytics Team
Version: 3.0.0
"""

import warnings
import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

FORECAST_TARGETS = {
    "Total System Load": "total_system_load",
    "HHS Care":          "hhs_care",
    "CBP Custody":       "cbp_custody",
}

TEST_DAYS = 60
_LAGS = (1, 7, 14, 30)


def _prophet_available():
    return False


def _make_lag_features(series):
    df = pd.DataFrame({"y": series.values}, index=series.index)
    for lag in _LAGS:
        df[f"lag_{lag}"] = df["y"].shift(lag)
    df["roll_mean_7"]  = df["y"].rolling(7,  min_periods=1).mean().shift(1)
    df["roll_std_7"]   = df["y"].rolling(7,  min_periods=2).std().shift(1).fillna(0)
    df["roll_mean_14"] = df["y"].rolling(14, min_periods=1).mean().shift(1)
    df["dow"]   = df.index.dayofweek
    df["month"] = df.index.month
    return df.dropna()


def _feature_names():
    return (
        [f"lag_{l}" for l in _LAGS]
        + ["roll_mean_7", "roll_std_7", "roll_mean_14", "dow", "month"]
    )


def _recursive_forecast(model, history, horizon, last_date):
    h = list(history)
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
            "dow":   (last_date + pd.Timedelta(days=step + 1)).dayofweek,
            "month": (last_date + pd.Timedelta(days=step + 1)).month,
        }
        x = np.array([row[f] for f in _feature_names()]).reshape(1, -1)
        pred = max(0.0, float(model.predict(x)[0]))
        h.append(pred)
        dates.append(last_date + pd.Timedelta(days=step + 1))
        preds.append(pred)
    return pd.DataFrame({"date": dates, "forecast": preds})


def run_rf_forecast(df, target_col, horizon):
    from sklearn.ensemble import RandomForestRegressor
    from sklearn.metrics import mean_absolute_error, mean_squared_error

    series  = df.set_index("date")[target_col].dropna().asfreq("D").ffill()
    feat_df = _make_lag_features(series)

    X      = feat_df[_feature_names()].values
    y      = feat_df["y"].values
    dates  = feat_df.index
    split  = len(X) - TEST_DAYS

    X_train, X_test = X[:split], X[split:]
    y_train, y_test = y[:split], y[split:]
    dates_test      = dates[split:]

    model = RandomForestRegressor(
        n_estimators=300, max_depth=12, min_samples_leaf=3,
        max_features="sqrt", random_state=42, n_jobs=-1,
    )
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)

    mae   = mean_absolute_error(y_test, y_pred)
    rmse  = float(np.sqrt(mean_squared_error(y_test, y_pred)))
    mape  = float(np.mean(np.abs((y_test - y_pred) / np.maximum(y_test, 1))) * 100)
    ss_res = np.sum((y_test - y_pred) ** 2)
    ss_tot = np.sum((y_test - np.mean(y_test)) ** 2)
    r2    = float(1 - ss_res / ss_tot) if ss_tot > 0 else 0.0

    test_df = pd.DataFrame({
        "date": dates_test, "actual": y_test, "predicted": y_pred,
    })

    forecast_df  = _recursive_forecast(model, list(series.values), horizon, series.index[-1])
    residual_std = np.std(y_test - y_pred)
    steps        = np.arange(1, horizon + 1)
    uncertainty  = residual_std * np.sqrt(steps / TEST_DAYS + 1)
    forecast_df["lower"] = (forecast_df["forecast"] - 1.96 * uncertainty).clip(lower=0)
    forecast_df["upper"] =  forecast_df["forecast"] + 1.96 * uncertainty

    importances = pd.Series(
        model.feature_importances_,
        index=[f.replace("_", " ").title() for f in _feature_names()],
    ).sort_values(ascending=True)

    return {
        "forecast_df": forecast_df,
        "metrics":     {"MAE": round(mae, 1), "RMSE": round(rmse, 1),
                        "MAPE": round(mape, 1), "R²": round(r2, 3)},
        "importances": importances,
        "test_df":     test_df,
    }


def run_prophet_forecast(df, target_col, horizon):
    return None


def format_metrics_table(rf_metrics, prophet_metrics=None):
    rows = []
    for metric in ["MAE", "RMSE", "MAPE", "R²"]:
        rows.append({"Metric": metric, "Random Forest": rf_metrics.get(metric, "—")})
    return pd.DataFrame(rows)
