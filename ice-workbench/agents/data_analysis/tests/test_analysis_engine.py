import json
import pytest
from unittest.mock import AsyncMock, patch

from experts.analysis_engine import (
    AnalysisPackage,
    execute_analysis_step,
    generate_analysis_plan,
)


def test_analysis_package_merge_anomalies():
    pkg = AnalysisPackage(initial_data="date,dau\n20260401,1000000")
    pkg.merge("anomaly_detect", {"anomalies": [{"date": "20260405", "severity": "mild"}]})
    assert len(pkg.anomalies) == 1
    assert pkg.anomalies[0]["anomalies"][0]["date"] == "20260405"


def test_analysis_package_merge_forecast():
    pkg = AnalysisPackage()
    pkg.merge("trend_forecast", {"forecast": [{"date": "20260422", "predicted": 100}]})
    assert len(pkg.forecasts) == 1


def test_analysis_package_merge_unknown_action():
    pkg = AnalysisPackage()
    pkg.merge("unknown_action", {"data": "test"})
    assert len(pkg.anomalies) == 0
    assert len(pkg.forecasts) == 0


def test_analysis_package_summary_includes_sections():
    pkg = AnalysisPackage(initial_data="date,dau\n20260401,100")
    pkg.merge("anomaly_detect", {"anomalies": [{"date": "20260405"}]})
    pkg.merge("trend_forecast", {"forecast": [{"date": "20260422"}]})
    summary = pkg.summary()
    assert "Initial Data" in summary
    assert "Anomalies Detected" in summary
    assert "Trend Forecasts" in summary


def test_analysis_package_summary_empty():
    pkg = AnalysisPackage(initial_data="date,dau\n20260401,100")
    summary = pkg.summary()
    assert "Initial Data" in summary
    assert "Anomalies" not in summary


def test_execute_analysis_step_anomaly_detect():
    csv = "date,dau\n" + "\n".join(f"{20260401 + i},{1000000}" for i in range(10))
    action, result = execute_analysis_step(
        {"action": "anomaly_detect", "params": {"metric_column": "dau", "date_column": "date"}},
        sql_used="SELECT ...",
        csv_data=csv,
    )
    assert action == "anomaly_detect"
    assert "anomalies" in result


def test_execute_analysis_step_trend_forecast():
    csv = "date,dau\n" + "\n".join(f"{20260401 + i},{1000000 + i * 1000}" for i in range(14))
    action, result = execute_analysis_step(
        {"action": "trend_forecast", "params": {"metric_column": "dau", "date_column": "date", "forecast_days": 3}},
        sql_used="SELECT ...",
        csv_data=csv,
    )
    assert action == "trend_forecast"
    assert "forecast" in result
    assert len(result["forecast"]) == 3


def test_execute_analysis_step_event_correlate():
    action, result = execute_analysis_step(
        {"action": "event_correlate", "params": {"anomaly_dates": ["20260418"]}},
        sql_used="SELECT ...",
        csv_data="",
    )
    assert action == "event_correlate"
    assert "correlations" in result


def test_execute_analysis_step_unknown_action():
    action, result = execute_analysis_step(
        {"action": "nonexistent", "params": {}},
        sql_used="", csv_data="",
    )
    assert "error" in result


@pytest.mark.asyncio
async def test_generate_analysis_plan_parses_json():
    mock_response = AsyncMock()
    mock_response.choices = [AsyncMock()]
    mock_response.choices[0].message.content = '[{"action": "anomaly_detect", "params": {"metric_column": "dau", "date_column": "date"}}]'

    with patch("experts.analysis_engine.client") as mock_client:
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
        plan = await generate_analysis_plan("data summary", "analysis brief")
        assert len(plan) == 1
        assert plan[0]["action"] == "anomaly_detect"


@pytest.mark.asyncio
async def test_generate_analysis_plan_handles_empty():
    mock_response = AsyncMock()
    mock_response.choices = [AsyncMock()]
    mock_response.choices[0].message.content = "[]"

    with patch("experts.analysis_engine.client") as mock_client:
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
        plan = await generate_analysis_plan("data summary", "brief")
        assert plan == []


@pytest.mark.asyncio
async def test_generate_analysis_plan_handles_malformed():
    mock_response = AsyncMock()
    mock_response.choices = [AsyncMock()]
    mock_response.choices[0].message.content = "not json at all"

    with patch("experts.analysis_engine.client") as mock_client:
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
        plan = await generate_analysis_plan("data", "brief")
        assert plan == []
