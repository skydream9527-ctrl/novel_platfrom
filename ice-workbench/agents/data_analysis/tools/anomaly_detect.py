import io
import json

import pandas as pd

from config import ANOMALY_THRESHOLD_SIGMA

TOOL_DEFINITION = {
    "name": "anomaly_detect",
    "description": "Detect statistical anomalies in time series data using rolling Z-score",
    "input_schema": {
        "type": "object",
        "properties": {
            "csv_data": {"type": "string", "description": "CSV with date and metric columns"},
            "metric_column": {"type": "string"},
            "date_column": {"type": "string"},
        },
        "required": ["csv_data", "metric_column", "date_column"],
    },
}


def detect_anomalies(
    csv_data: str,
    metric_column: str,
    date_column: str,
    sigma: float = ANOMALY_THRESHOLD_SIGMA,
    min_points: int = 5,
) -> dict:
    df = pd.read_csv(io.StringIO(csv_data))
    if metric_column not in df.columns or date_column not in df.columns:
        return {"anomalies": [], "error": f"Column not found"}
    if len(df) < min_points:
        return {"anomalies": []}

    df = df.sort_values(date_column).reset_index(drop=True)
    series = df[metric_column].astype(float)

    window = min(7, len(df) - 1)
    rolling_mean = series.rolling(window=window, min_periods=3).mean()
    rolling_std = series.rolling(window=window, min_periods=3).std()

    anomalies = []
    for i, (val, mean, std) in enumerate(zip(series, rolling_mean, rolling_std)):
        if pd.isna(mean) or pd.isna(std) or std == 0:
            continue
        zscore = (val - mean) / std
        if abs(zscore) > sigma:
            if abs(zscore) > 4:
                severity = "severe"
            elif abs(zscore) > 3:
                severity = "moderate"
            else:
                severity = "mild"
            anomalies.append({
                "date": str(df[date_column].iloc[i]),
                "value": float(val),
                "zscore": round(float(zscore), 2),
                "severity": severity,
                "direction": "up" if zscore > 0 else "down",
            })

    return {"anomalies": anomalies}


def handle_anomaly_detect(csv_data: str, metric_column: str, date_column: str) -> str:
    result = detect_anomalies(csv_data, metric_column, date_column)
    return json.dumps(result, ensure_ascii=False)
