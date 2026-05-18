import asyncio
import json
from dataclasses import dataclass, field

from openai import AsyncOpenAI

from config import (
    MODEL_MAIN, API_BASE_URL, API_KEY,
    MAX_ANALYSIS_ROUNDS, FORECAST_DAYS_DEFAULT,
)
from tools.anomaly_detect import handle_anomaly_detect
from tools.event_correlate import handle_event_correlate
from tools.trend_forecast import handle_trend_forecast
from tools.period_compare import handle_period_compare
from tools.auto_drilldown import handle_auto_drilldown

client = AsyncOpenAI(base_url=API_BASE_URL, api_key=API_KEY)

PLAN_PROMPT = """\
You have the following initial query result:
{data_summary}

The user's analysis goal is: {analysis_brief}

Select which analysis actions are needed from the list below.
Only include actions that would materially improve the analysis.
Output a JSON array of steps to execute. Output ONLY the JSON array, no other text.

Available actions:
1. period_compare — if YoY/WoW comparison would be meaningful
2. auto_drilldown — if there is notable variation that needs dimension attribution
3. anomaly_detect — if the data is a time series with ≥3 data points
4. trend_forecast — if the user cares about future trajectory
5. event_correlate — if anomalies are found that could be linked to events

Output format example:
[
  {{"action": "period_compare", "params": {{"compare_type": "wow"}}}},
  {{"action": "anomaly_detect", "params": {{"metric_column": "dau", "date_column": "date"}}}},
  {{"action": "trend_forecast", "params": {{"metric_column": "dau", "date_column": "date", "forecast_days": 7}}}},
  {{"action": "auto_drilldown", "params": {{"dimensions": ["is_new_2024", "app_launch_way"], "metric_column": "dau"}}}},
  {{"action": "event_correlate", "params": {{"anomaly_dates": ["20260418"]}}}}
]

If no supplementary analysis is needed, output an empty array: []
"""


@dataclass
class AnalysisPackage:
    initial_data: str = ""
    sql_used: str = ""
    period_comparisons: list[dict] = field(default_factory=list)
    drilldowns: list[dict] = field(default_factory=list)
    anomalies: list[dict] = field(default_factory=list)
    forecasts: list[dict] = field(default_factory=list)
    event_correlations: list[dict] = field(default_factory=list)

    def merge(self, action: str, result: dict):
        if action == "period_compare":
            self.period_comparisons.append(result)
        elif action == "auto_drilldown":
            self.drilldowns.append(result)
        elif action == "anomaly_detect":
            self.anomalies.append(result)
        elif action == "trend_forecast":
            self.forecasts.append(result)
        elif action == "event_correlate":
            self.event_correlations.append(result)

    def summary(self) -> str:
        parts = [f"## Initial Data\n\n```csv\n{self.initial_data[:2000]}\n```"]
        if self.period_comparisons:
            parts.append(f"## Period Comparisons\n\n{json.dumps(self.period_comparisons, ensure_ascii=False, default=str)}")
        if self.anomalies:
            parts.append(f"## Anomalies Detected\n\n{json.dumps(self.anomalies, ensure_ascii=False)}")
        if self.drilldowns:
            parts.append(f"## Dimension Drilldowns\n\n{json.dumps(self.drilldowns, ensure_ascii=False, default=str)}")
        if self.forecasts:
            parts.append(f"## Trend Forecasts\n\n{json.dumps(self.forecasts, ensure_ascii=False)}")
        if self.event_correlations:
            parts.append(f"## Event Correlations\n\n{json.dumps(self.event_correlations, ensure_ascii=False)}")
        return "\n\n".join(parts)


async def generate_analysis_plan(data_summary: str, analysis_brief: str) -> list[dict]:
    prompt = PLAN_PROMPT.format(data_summary=data_summary, analysis_brief=analysis_brief)
    response = await client.chat.completions.create(
        model=MODEL_MAIN,
        max_tokens=2048,
        messages=[{"role": "user", "content": prompt}],
    )
    text = (response.choices[0].message.content or "").strip()
    start = text.find("[")
    end = text.rfind("]")
    if start == -1 or end == -1:
        return []
    try:
        return json.loads(text[start:end + 1])
    except json.JSONDecodeError:
        return []


def execute_analysis_step(step: dict, sql_used: str, csv_data: str) -> tuple[str, dict]:
    action = step.get("action", "")
    params = step.get("params", {})

    if action == "period_compare":
        result_str = handle_period_compare(
            sql=sql_used,
            compare_type=params.get("compare_type", "wow"),
            metric_column=params.get("metric_column", ""),
        )
    elif action == "auto_drilldown":
        result_str = handle_auto_drilldown(
            sql=sql_used,
            dimensions=params.get("dimensions", []),
            metric_column=params.get("metric_column", ""),
        )
    elif action == "anomaly_detect":
        result_str = handle_anomaly_detect(
            csv_data=csv_data,
            metric_column=params.get("metric_column", ""),
            date_column=params.get("date_column", "date"),
        )
    elif action == "trend_forecast":
        result_str = handle_trend_forecast(
            csv_data=csv_data,
            metric_column=params.get("metric_column", ""),
            date_column=params.get("date_column", "date"),
            forecast_days=params.get("forecast_days", FORECAST_DAYS_DEFAULT),
        )
    elif action == "event_correlate":
        result_str = handle_event_correlate(
            anomaly_dates=params.get("anomaly_dates", []),
        )
    else:
        return action, {"error": f"Unknown action: {action}"}

    try:
        return action, json.loads(result_str)
    except json.JSONDecodeError:
        return action, {"raw": result_str}


async def run_analysis_engine(
    initial_data: str,
    sql_used: str,
    analysis_brief: str,
) -> AnalysisPackage:
    package = AnalysisPackage(initial_data=initial_data, sql_used=sql_used)

    for round_num in range(MAX_ANALYSIS_ROUNDS):
        plan = await generate_analysis_plan(package.summary(), analysis_brief)
        if not plan:
            break

        for step in plan:
            action, result = execute_analysis_step(step, sql_used, initial_data)
            package.merge(action, result)

            if action == "anomaly_detect":
                anomaly_dates = [a["date"] for a in result.get("anomalies", [])]
                if anomaly_dates and not package.event_correlations:
                    _, corr_result = execute_analysis_step(
                        {"action": "event_correlate", "params": {"anomaly_dates": anomaly_dates}},
                        sql_used, initial_data,
                    )
                    package.merge("event_correlate", corr_result)

    return package
