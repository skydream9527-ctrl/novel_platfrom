import json
import pytest
from tools.trend_forecast import handle_trend_forecast, forecast_trend


def make_csv(values: list[int], start_date: int = 20260401) -> str:
    rows = ["date,dau"]
    for i, v in enumerate(values):
        rows.append(f"{start_date + i},{v}")
    return "\n".join(rows)


def test_flat_trend_direction():
    csv = make_csv([1000000] * 14)
    result = forecast_trend(csv, "dau", "date", forecast_days=3)
    assert result["trend_direction"] == "flat"
    assert len(result["forecast"]) == 3


def test_upward_trend_direction():
    csv = make_csv([1000000 + i * 10000 for i in range(14)])
    result = forecast_trend(csv, "dau", "date", forecast_days=3)
    assert result["trend_direction"] == "up"


def test_forecast_has_confidence_interval():
    csv = make_csv([1000000 + i * 5000 for i in range(14)])
    result = forecast_trend(csv, "dau", "date", forecast_days=5)
    for point in result["forecast"]:
        assert "predicted" in point
        assert "lower" in point
        assert "upper" in point
        assert point["lower"] <= point["predicted"] <= point["upper"]


def test_forecast_dates_are_sequential():
    csv = make_csv([1000000] * 14, start_date=20260401)
    result = forecast_trend(csv, "dau", "date", forecast_days=3)
    dates = [p["date"] for p in result["forecast"]]
    assert dates == sorted(dates)


def test_handle_returns_json_string():
    csv = make_csv([1000000] * 14)
    result = handle_trend_forecast(csv, "dau", "date", 3)
    data = json.loads(result)
    assert "forecast" in data
    assert "r_squared" in data
