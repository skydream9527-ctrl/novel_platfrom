import json
import re
import subprocess

from tools.kyuubi import KYUUBI_REGION, KYUUBI_WORKSPACE

TOOL_DEFINITION = {
    "name": "auto_drilldown",
    "description": "Drill down into dimensions to find which dimension values contribute most to a metric change",
    "input_schema": {
        "type": "object",
        "properties": {
            "sql": {"type": "string", "description": "Original nl-sql-generated query"},
            "dimensions": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Dimension columns to drill down (e.g., ['is_new_2024', 'app_launch_way'])",
            },
            "metric_column": {"type": "string", "description": "Name of the metric/aggregation column"},
        },
        "required": ["sql", "dimensions", "metric_column"],
    },
}


def _inject_group_by(sql: str, dimension: str) -> str:
    sql_upper = sql.upper()

    if "GROUP BY" in sql_upper:
        group_idx = sql_upper.index("GROUP BY")
        group_end = group_idx + len("GROUP BY")
        return sql[:group_end] + f" {dimension}, " + sql[group_end:]

    select_pattern = re.compile(r"(SELECT\s)", re.IGNORECASE)
    sql = select_pattern.sub(f"SELECT {dimension}, ", sql, count=1)

    order_match = re.search(r"\bORDER\s+BY\b", sql, re.IGNORECASE)
    insert_pos = order_match.start() if order_match else len(sql)
    sql = sql[:insert_pos] + f" GROUP BY {dimension} " + sql[insert_pos:]
    return sql


def _run_query(sql: str) -> dict:
    result = subprocess.run(
        ["kyuubi", "sql", "query", sql,
         "--region", KYUUBI_REGION, "--workspace", KYUUBI_WORKSPACE],
        capture_output=True, text=True, timeout=300,
    )
    if result.returncode != 0:
        return {"error": result.stderr.strip() or f"exit code {result.returncode}"}
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        return {"raw_output": result.stdout.strip()}


def drilldown(sql: str, dimensions: list[str], metric_column: str) -> dict:
    results = []
    for dim in dimensions:
        dim_sql = _inject_group_by(sql, dim)
        query_result = _run_query(dim_sql)
        if "error" in query_result:
            results.append({"dimension": dim, "error": query_result["error"]})
            continue

        rows = query_result.get("rows", query_result.get("raw_output", []))
        results.append({"dimension": dim, "breakdown": rows})

    return {"drilldowns": results}


def handle_auto_drilldown(sql: str, dimensions: list[str], metric_column: str) -> str:
    result = drilldown(sql, dimensions, metric_column)
    return json.dumps(result, ensure_ascii=False, default=str)
