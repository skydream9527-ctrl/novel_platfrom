import subprocess
import sys
from pathlib import Path

from config import NLSQL_REFERENCE_DIR, NLSQL_SCRIPT


def load_reference_file(business_line: str, filename: str) -> str:
    path = NLSQL_REFERENCE_DIR / business_line / filename
    if not path.exists():
        raise FileNotFoundError(f"Reference file not found: {path}")
    return path.read_text(encoding="utf-8")


def load_metric_index(business_line: str) -> str:
    return load_reference_file(business_line, "metric-name-index.md")


def load_dimension_index(business_line: str) -> str:
    return load_reference_file(business_line, "metric-dimension-index.md")


def load_table_schema(business_line: str) -> str:
    return load_reference_file(business_line, "core-metrics-tables.md")


def load_event_index(business_line: str) -> str:
    return load_reference_file(business_line, "event-name-index.md")


def load_event_reference(business_line: str) -> str:
    return load_reference_file(business_line, "event-metrics-reference.md")


def load_core_metrics_reference(business_line: str) -> str:
    return load_reference_file(business_line, "core-metrics-reference.md")


def save_sql_file(metric_name: str, sql: str, output_dir: str | None = None) -> str:
    cmd = [
        sys.executable, str(NLSQL_SCRIPT),
        "--metric", metric_name,
        "--sql", sql,
    ]
    if output_dir:
        cmd.extend(["--output-dir", output_dir])

    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return result.stdout.strip()


TOOL_DEFINITION = {
    "name": "generate_sql_via_nlsql",
    "description": (
        "Generate SQL using nl-sql skill reference files. "
        "Returns reference data (metric index, dimension index, table schema, "
        "event index) for the specified business line and data type. "
        "The agent MUST use this data to construct SQL following nl-sql's "
        "three-element model. This is the ONLY permitted way to produce SQL."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "business_line": {
                "type": "string",
                "enum": ["browser-main", "browser-feed", "content-center", "search", "novel"],
                "description": "Which business line to query",
            },
            "data_type": {
                "type": "string",
                "enum": ["core-metrics", "event-tracking"],
                "description": "Core metrics or event tracking",
            },
        },
        "required": ["business_line", "data_type"],
    },
}


def handle_generate_sql(business_line: str, data_type: str) -> str:
    parts = []

    if data_type == "core-metrics":
        parts.append("## Metric Name Index\n\n" + load_metric_index(business_line))
        parts.append("## Dimension Index\n\n" + load_dimension_index(business_line))
        parts.append("## Table Schema & SQL Templates\n\n" + load_table_schema(business_line))
        parts.append("## Core Metrics Reference\n\n" + load_core_metrics_reference(business_line))
    else:
        parts.append("## Event Name Index\n\n" + load_event_index(business_line))
        parts.append("## Event Metrics Reference\n\n" + load_event_reference(business_line))
        parts.append("## Table Schema\n\n" + load_table_schema(business_line))

    return "\n\n---\n\n".join(parts)


SAVE_SQL_TOOL = {
    "name": "save_sql_file",
    "description": "Save generated SQL to a file using nl-sql script",
    "input_schema": {
        "type": "object",
        "properties": {
            "metric_name": {
                "type": "string",
                "description": "Metric name for the filename",
            },
            "sql": {
                "type": "string",
                "description": "SQL content to save",
            },
        },
        "required": ["metric_name", "sql"],
    },
}


def handle_save_sql(metric_name: str, sql: str) -> str:
    try:
        output = save_sql_file(metric_name, sql)
        return output
    except subprocess.CalledProcessError as e:
        return f"Error saving SQL: {e.stderr}"
