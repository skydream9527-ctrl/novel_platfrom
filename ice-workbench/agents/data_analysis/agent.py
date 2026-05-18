"""Data Analysis Agent — declarative registration for shared Runtime."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from shared.runtime import AgentDefinition
from shared.tool_registry import ToolDef

from tools.nlsql import handle_generate_sql, handle_save_sql
from tools.kyuubi import handle_execute_query
from tools.csv_export import handle_save_csv
from tools.chart import handle_generate_chart
from tools.feishu import handle_publish_to_feishu
from tools.anomaly_detect import handle_anomaly_detect
from tools.event_correlate import handle_event_correlate
from tools.trend_forecast import handle_trend_forecast
from tools.period_compare import handle_period_compare
from tools.auto_drilldown import handle_auto_drilldown

AGENT_DIR = Path(__file__).resolve().parent

# Tool definitions
TOOLS = [
    ToolDef(
        name="generate_sql_via_nlsql",
        description="通过 NL-SQL 获取指定业务线的参考文件，用于生成 SQL",
        parameters={
            "type": "object",
            "properties": {
                "business_line": {"type": "string", "description": "业务线标识"},
                "data_type": {"type": "string", "description": "数据类型: core_metrics 或 events"},
            },
            "required": ["business_line", "data_type"],
        },
        handler=lambda args: handle_generate_sql(
            business_line=args["business_line"], data_type=args["data_type"]
        ),
    ),
    ToolDef(
        name="save_sql_file",
        description="保存生成的 SQL 文件",
        parameters={
            "type": "object",
            "properties": {
                "metric_name": {"type": "string"},
                "sql": {"type": "string"},
            },
            "required": ["metric_name", "sql"],
        },
        handler=lambda args: handle_save_sql(
            metric_name=args["metric_name"], sql=args["sql"]
        ),
    ),
    ToolDef(
        name="execute_query",
        description="通过 Kyuubi 执行 SQL 查询",
        parameters={
            "type": "object",
            "properties": {
                "sql": {"type": "string", "description": "要执行的 SQL"},
            },
            "required": ["sql"],
        },
        handler=lambda args: handle_execute_query(sql=args["sql"]),
    ),
    ToolDef(
        name="save_csv",
        description="保存查询结果为 CSV 文件",
        parameters={
            "type": "object",
            "properties": {
                "csv_content": {"type": "string"},
                "topic": {"type": "string"},
            },
            "required": ["csv_content", "topic"],
        },
        handler=lambda args: handle_save_csv(
            csv_content=args["csv_content"], topic=args["topic"]
        ),
    ),
    ToolDef(
        name="generate_chart",
        description="根据 CSV 数据生成可视化图表",
        parameters={
            "type": "object",
            "properties": {
                "csv_content": {"type": "string"},
                "chart_type": {"type": "string"},
                "title": {"type": "string"},
                "x_column": {"type": "string"},
                "y_column": {"type": "string"},
                "topic": {"type": "string"},
            },
            "required": ["csv_content", "chart_type", "title", "x_column", "y_column", "topic"],
        },
        handler=lambda args: handle_generate_chart(
            csv_content=args["csv_content"],
            chart_type=args["chart_type"],
            title=args["title"],
            x_column=args["x_column"],
            y_column=args["y_column"],
            topic=args["topic"],
        ),
    ),
    ToolDef(
        name="publish_to_feishu",
        description="将分析报告发布到飞书文档",
        parameters={
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "markdown_content": {"type": "string"},
            },
            "required": ["title", "markdown_content"],
        },
        handler=lambda args: handle_publish_to_feishu(
            title=args["title"], markdown_content=args["markdown_content"]
        ),
    ),
    ToolDef(
        name="anomaly_detect",
        description="对时序数据进行异常检测",
        parameters={
            "type": "object",
            "properties": {
                "csv_data": {"type": "string"},
                "metric_column": {"type": "string"},
                "date_column": {"type": "string"},
            },
            "required": ["csv_data", "metric_column", "date_column"],
        },
        handler=lambda args: handle_anomaly_detect(
            csv_data=args["csv_data"],
            metric_column=args["metric_column"],
            date_column=args["date_column"],
        ),
    ),
    ToolDef(
        name="event_correlate",
        description="将异常日期与已知事件进行关联分析",
        parameters={
            "type": "object",
            "properties": {
                "anomaly_dates": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["anomaly_dates"],
        },
        handler=lambda args: handle_event_correlate(anomaly_dates=args["anomaly_dates"]),
    ),
    ToolDef(
        name="trend_forecast",
        description="对时序数据进行趋势预测",
        parameters={
            "type": "object",
            "properties": {
                "csv_data": {"type": "string"},
                "metric_column": {"type": "string"},
                "date_column": {"type": "string"},
                "forecast_days": {"type": "integer", "default": 7},
            },
            "required": ["csv_data", "metric_column", "date_column"],
        },
        handler=lambda args: handle_trend_forecast(
            csv_data=args["csv_data"],
            metric_column=args["metric_column"],
            date_column=args["date_column"],
            forecast_days=args.get("forecast_days", 7),
        ),
    ),
    ToolDef(
        name="period_compare",
        description="环比或同比对比分析",
        parameters={
            "type": "object",
            "properties": {
                "sql": {"type": "string"},
                "compare_type": {"type": "string", "enum": ["wow", "yoy"]},
                "metric_column": {"type": "string"},
            },
            "required": ["sql", "compare_type", "metric_column"],
        },
        handler=lambda args: handle_period_compare(
            sql=args["sql"],
            compare_type=args["compare_type"],
            metric_column=args["metric_column"],
        ),
    ),
    ToolDef(
        name="auto_drilldown",
        description="按维度自动下钻归因分析",
        parameters={
            "type": "object",
            "properties": {
                "sql": {"type": "string"},
                "dimensions": {"type": "array", "items": {"type": "string"}},
                "metric_column": {"type": "string"},
            },
            "required": ["sql", "dimensions", "metric_column"],
        },
        handler=lambda args: handle_auto_drilldown(
            sql=args["sql"],
            dimensions=args["dimensions"],
            metric_column=args["metric_column"],
        ),
    ),
]

agent_definition = AgentDefinition(
    name="data_analysis",
    prompt_dir=AGENT_DIR / "prompt",
    skills_dir=AGENT_DIR / "skills",
    tools=TOOLS,
    config={
        "display_name": "数据分析 Agent",
        "icon": "📊",
        "color": "green",
    },
)
