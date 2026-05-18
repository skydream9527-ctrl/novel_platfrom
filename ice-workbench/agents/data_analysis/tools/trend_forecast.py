import io
import json
from datetime import datetime, timedelta

import numpy as np
import pandas as pd
from scipy import stats

TOOL_DEFINITION = {
    "name": "trend_forecast",
    "description": "Forecast future metric values using linear regression on recent data",
    "input_schema": {
        "type": "object",
        "properties": {
            "csv_data": {"type": "string"},
            "metric_column": {"type": "string"},
            "date_column": {"type": "string"},
            "forecast_days": {"type": "integer", "default": 7},
        },
        "required": ["csv_data", "metric_column", "date_column"],
    },
}

_TREND_SLOPE_THRESHOLD = 0.005


def forecast_trend(
    csv_data: str,
    metric_column: str,
    date_column: str,
    forecast_days: int = 7,
    fit_window: int = 14,
) -> dict:
    df = pd.read_csv(io.StringIO(csv_data))
    df = df.sort_values(date_column).tail(fit_window).reset_index(drop=True)

    x = np.arange(len(df))
    y = df[metric_column].astype(float).values

    slope, intercept, r_value, _, _ = stats.linregress(x, y)
    predicted_in_sample = slope * x + intercept
    residuals = y - predicted_in_sample
    std_residual = np.std(residuals)
    ci_multiplier = 1.645  # 90% confidence

    last_date_str = str(df[date_column].iloc[-1])
    try:
        last_date = datetime.strptime(last_date_str, "%Y%m%d")
        date_fmt = "%Y%m%d"
    except ValueError:
        last_date = datetime.strptime(last_date_str, "%Y-%m-%d")
        date_fmt = "%Y-%m-%d"

    forecast = []
    for i in range(1, forecast_days + 1):
        x_future = len(df) - 1 + i
        pred = slope * x_future + intercept
        margin = ci_multiplier * std_residual
        future_date = last_date + timedelta(days=i)
        forecast.append({
            "date": future_date.strftime(date_fmt),
            "predicted": round(float(pred)),
            "lower": round(float(pred - margin)),
            "upper": round(float(pred + margin)),
        })

    normalized_slope = slope / (np.mean(y) if np.mean(y) != 0 else 1)
    if normalized_slope > _TREND_SLOPE_THRESHOLD:
        trend_direction = "up"
    elif normalized_slope < -_TREND_SLOPE_THRESHOLD:
        trend_direction = "down"
    else:
        trend_direction = "flat"

    return {
        "forecast": forecast,
        "trend_direction": trend_direction,
        "r_squared": round(float(r_value ** 2), 3),
    }


def handle_trend_forecast(
    csv_data: str,
    metric_column: str,
    date_column: str,
    forecast_days: int = 7,
) -> str:
    result = forecast_trend(csv_data, metric_column, date_column, forecast_days)
    return json.dumps(result, ensure_ascii=False)
