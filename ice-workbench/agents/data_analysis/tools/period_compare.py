import json
import re
import subprocess
from datetime import datetime, timedelta

KYUUBI_REGION = "chnbj"
KYUUBI_WORKSPACE = "11329"

COMPARE_DAYS = {"wow": 7, "mom": 28, "yoy": 365}

TOOL_DEFINITION = {
    "name": "period_compare",
    "description": "Compare current period with a previous period (wow/mom/yoy) by re-running the same SQL with shifted dates",
    "input_schema": {
        "type": "object",
        "properties": {
            "sql": {"type": "string", "description": "Original nl-sql-generated query"},
            "compare_type": {"type": "string", "enum": ["wow", "mom", "yoy"]},
            "metric_column": {"type": "string", "description": "Name of the metric column"},
        },
        "required": ["sql", "compare_type", "metric_column"],
    },
}


def shift_dates_in_sql(sql: str, days_back: int) -> str:
    def replace_date(m: re.Match) -> str:
        try:
            d = datetime.strptime(m.group(1), "%Y%m%d") - timedelta(days=days_back)
            return f"'{d.strftime('%Y%m%d')}'"
        except ValueError:
            return m.group(0)
    return re.sub(r"'(\d{8})'", replace_date, sql)


def run_kyuubi_query(sql: str) -> dict:
    result = subprocess.run(
        ["kyuubi", "sql", "query", sql, "--region", KYUUBI_REGION, "--workspace", KYUUBI_WORKSPACE],
        capture_output=True,
        text=True,
        timeout=300,
    )
    if result.returncode != 0:
        return {"error": result.stderr.strip() or f"kyuubi exit code {result.returncode}"}
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        return {"raw_output": result.stdout.strip()}


def handle_period_compare(sql: str, compare_type: str, metric_column: str) -> str:
    days = COMPARE_DAYS.get(compare_type, 7)
    comparison_sql = shift_dates_in_sql(sql, days)
    current_result = run_kyuubi_query(sql)
    previous_result = run_kyuubi_query(comparison_sql)
    return json.dumps({
        "compare_type": compare_type,
        "days_back": days,
        "metric_column": metric_column,
        "current_result": current_result,
        "previous_result": previous_result,
    }, ensure_ascii=False, default=str)
