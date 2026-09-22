"""
Machine learning layer.

Reads raw ingested records (via the HDFS-sim client) and produces:
  1. Trend prediction: a linear regression per group (station/region/sensor)
     over time, forecasting the next value.
  2. Anomaly detection: IsolationForest over the metric values, independent of
     the z-score anomalies already flagged by the MapReduce job -- this gives
     a second, model-based signal (correlation/pattern-based rather than
     purely statistical).

Both are intentionally lightweight (scikit-learn's LinearRegression /
IsolationForest) so they run fast on demo-sized data; swapping in a heavier
model later only touches this file.
"""
import json
import os
from datetime import datetime, timedelta

import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

from app.config import Config
from app.hdfs_sim.client import list_all_blocks, read_blocks_as_dicts
from app.mapreduce.jobs import METRIC_BY_SOURCE, GROUP_KEY_BY_SOURCE

ML_OUT_DIR = os.path.join(Config.HDFS_PROCESSED, "_ml")


def _load_clean_rows(source_type: str) -> list[dict]:
    metric_field = METRIC_BY_SOURCE[source_type]
    blocks = list_all_blocks(source_type)
    if not blocks:
        raise ValueError(f"No ingested data found for source_type={source_type}")

    rows = read_blocks_as_dicts(blocks)
    clean = []
    for row in rows:
        raw_value = row.get(metric_field, "").strip()
        if raw_value == "" or row.get("timestamp", "") == "":
            continue
        try:
            value = float(raw_value)
        except ValueError:
            continue
        clean.append({
            "group_key": row.get(GROUP_KEY_BY_SOURCE[source_type], "unknown"),
            "timestamp": row["timestamp"],
            "value": value,
        })

    if not clean:
        raise ValueError(f"No usable numeric rows for source_type={source_type}")

    return clean


def predict_trends(source_type: str) -> dict:
    """Fit a per-group linear regression (value ~ time order) and predict the next value."""
    rows = _load_clean_rows(source_type)

    by_group: dict[str, list[dict]] = {}
    for r in rows:
        by_group.setdefault(r["group_key"], []).append(r)

    predictions = []
    for group_key, group_rows in by_group.items():
        group_rows.sort(key=lambda r: r["timestamp"])
        n = len(group_rows)

        if n < 3:
            predictions.append({
                "group_key": group_key,
                "samples": n,
                "predicted_next": None,
                "trend": "insufficient_data",
            })
            continue

        X = np.arange(n).reshape(-1, 1)
        y = np.array([r["value"] for r in group_rows])

        model = LinearRegression()
        model.fit(X, y)
        predicted_next = float(model.predict([[n]])[0])
        slope = float(model.coef_[0])

        trend = "rising" if slope > 0.01 else "falling" if slope < -0.01 else "stable"

        metrics = None
        if n >= 5:
            split = max(int(n * 0.8), n - 5)
            X_train, X_test = X[:split], X[split:]
            y_train, y_test = y[:split], y[split:]
            if len(X_test) > 0:
                eval_model = LinearRegression()
                eval_model.fit(X_train, y_train)
                y_pred = eval_model.predict(X_test)
                metrics = {
                    "mae": round(float(mean_absolute_error(y_test, y_pred)), 3),
                    "rmse": round(float(mean_squared_error(y_test, y_pred) ** 0.5), 3),
                    "r2": round(float(r2_score(y_test, y_pred)), 3) if len(y_test) > 1 else None,
                    "test_samples": len(y_test),
                }

        predictions.append({
            "group_key": group_key,
            "samples": n,
            "last_value": round(group_rows[-1]["value"], 2),
            "predicted_next": round(predicted_next, 2),
            "slope_per_sample": round(slope, 4),
            "trend": trend,
            "metrics": metrics,
        })

    predictions.sort(key=lambda p: p["group_key"])

    result = {
        "source_type": source_type,
        "metric": METRIC_BY_SOURCE[source_type],
        "generated_at": datetime.utcnow().isoformat(),
        "predictions": predictions,
    }
    _write_ml_result(source_type, "trend", result)
    return result


def forecast_7day(source_type: str, group_key: str | None = None) -> dict:
    """
    Build a daily-averaged time series (optionally filtered to one group/location)
    from ingested data, fit a linear regression on day-index -> daily mean value,
    and forecast the next 7 days. Reports MAE/RMSE/R2 from a held-out tail of the
    real series so accuracy is measured, not invented.
    """
    rows = _load_clean_rows(source_type)
    if group_key:
        rows = [r for r in rows if r["group_key"] == group_key]
        if not rows:
            raise ValueError(f"No data found for group_key={group_key}")

    daily = {}
    for r in rows:
        try:
            day = datetime.fromisoformat(r["timestamp"]).date().isoformat()
        except ValueError:
            continue
        daily.setdefault(day, []).append(r["value"])

    if len(daily) >= 3:
        days_sorted = sorted(daily.keys())
        daily_means = [sum(daily[d]) / len(daily[d]) for d in days_sorted]
        step = timedelta(days=1)
        last_point = datetime.fromisoformat(days_sorted[-1])
    else:
        # Not enough distinct calendar days (e.g. all records ingested today via
        # the real-time simulator). Fall back to hourly buckets so a forecast is
        # still possible from genuinely-recorded data, rather than refusing outright.
        hourly = {}
        for r in rows:
            try:
                bucket = datetime.fromisoformat(r["timestamp"]).replace(minute=0, second=0, microsecond=0)
            except ValueError:
                continue
            hourly.setdefault(bucket, []).append(r["value"])

        if len(hourly) < 3:
            raise ValueError("Need at least 3 distinct days (or 3 distinct hours) of data to forecast.")

        hours_sorted = sorted(hourly.keys())
        daily_means = [sum(hourly[h]) / len(hourly[h]) for h in hours_sorted]
        step = timedelta(hours=1)
        last_point = hours_sorted[-1]

    n = len(daily_means)

    X = np.arange(n).reshape(-1, 1)
    y = np.array(daily_means)

    metrics = None
    if n >= 5:
        split = max(int(n * 0.8), n - 3)
        X_train, X_test = X[:split], X[split:]
        y_train, y_test = y[:split], y[split:]
        if len(X_test) > 0:
            eval_model = LinearRegression()
            eval_model.fit(X_train, y_train)
            y_pred = eval_model.predict(X_test)
            metrics = {
                "mae": round(float(mean_absolute_error(y_test, y_pred)), 3),
                "rmse": round(float(mean_squared_error(y_test, y_pred) ** 0.5), 3),
                "r2": round(float(r2_score(y_test, y_pred)), 3) if len(y_test) > 1 else None,
                "test_samples": len(y_test),
            }

    model = LinearRegression()
    model.fit(X, y)

    future_X = np.arange(n, n + 7).reshape(-1, 1)
    future_y = model.predict(future_X)

    forecast_days = []
    for i, value in enumerate(future_y, start=1):
        forecast_point = last_point + step * i
        label = forecast_point.date().isoformat() if step == timedelta(days=1) else forecast_point.strftime("%Y-%m-%d %H:00")
        forecast_days.append({
            "date": label,
            "predicted_value": round(float(value), 2),
        })

    result = {
        "source_type": source_type,
        "metric": METRIC_BY_SOURCE[source_type],
        "group_key": group_key or "all",
        "generated_at": datetime.utcnow().isoformat(),
        "history_days": n,
        "last_observed_value": round(daily_means[-1], 2),
        "forecast": forecast_days,
        "metrics": metrics,
    }
    return result


def detect_ml_anomalies(source_type: str, contamination: float = 0.05) -> dict:
    """Run IsolationForest over all metric values to flag model-based anomalies."""
    rows = _load_clean_rows(source_type)

    if len(rows) < 10:
        raise ValueError("Need at least 10 records for anomaly detection.")

    X = np.array([[r["value"]] for r in rows])
    model = IsolationForest(contamination=contamination, random_state=42)
    labels = model.fit_predict(X)  # -1 = anomaly, 1 = normal

    anomalies = [
        {"group_key": rows[i]["group_key"], "timestamp": rows[i]["timestamp"], "value": rows[i]["value"]}
        for i, label in enumerate(labels)
        if label == -1
    ]

    result = {
        "source_type": source_type,
        "metric": METRIC_BY_SOURCE[source_type],
        "generated_at": datetime.utcnow().isoformat(),
        "total_records": len(rows),
        "anomaly_count": len(anomalies),
        "anomalies": anomalies,
    }
    _write_ml_result(source_type, "anomaly", result)
    return result


def _write_ml_result(source_type: str, kind: str, result: dict) -> str:
    out_dir = os.path.join(ML_OUT_DIR, source_type)
    os.makedirs(out_dir, exist_ok=True)
    filename = f"{kind}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
    filepath = os.path.join(out_dir, filename)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)
    return filepath


def latest_ml_result(source_type: str, kind: str) -> dict | None:
    out_dir = os.path.join(ML_OUT_DIR, source_type)
    if not os.path.isdir(out_dir):
        return None
    files = sorted(f for f in os.listdir(out_dir) if f.startswith(kind))
    if not files:
        return None
    with open(os.path.join(out_dir, files[-1]), encoding="utf-8") as f:
        return json.load(f)
