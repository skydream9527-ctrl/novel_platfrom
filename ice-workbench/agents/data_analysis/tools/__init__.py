from tools.nlsql import (
    TOOL_DEFINITION as NLSQL_TOOL,
    SAVE_SQL_TOOL,
    handle_generate_sql,
    handle_save_sql,
)
from tools.kyuubi import TOOL_DEFINITION as KYUUBI_TOOL, handle_execute_query
from tools.csv_export import TOOL_DEFINITION as CSV_TOOL, handle_save_csv
from tools.chart import TOOL_DEFINITION as CHART_TOOL, handle_generate_chart
from tools.feishu import TOOL_DEFINITION as FEISHU_TOOL, handle_publish_to_feishu
from tools.anomaly_detect import TOOL_DEFINITION as ANOMALY_TOOL, handle_anomaly_detect
from tools.event_correlate import TOOL_DEFINITION as EVENT_TOOL, handle_event_correlate
from tools.trend_forecast import TOOL_DEFINITION as FORECAST_TOOL, handle_trend_forecast
from tools.period_compare import TOOL_DEFINITION as PERIOD_TOOL, handle_period_compare
from tools.auto_drilldown import TOOL_DEFINITION as DRILLDOWN_TOOL, handle_auto_drilldown

ALL_TOOLS = [
    NLSQL_TOOL, SAVE_SQL_TOOL, KYUUBI_TOOL, CSV_TOOL, CHART_TOOL, FEISHU_TOOL,
    ANOMALY_TOOL, EVENT_TOOL, FORECAST_TOOL, PERIOD_TOOL, DRILLDOWN_TOOL,
]

TOOL_HANDLERS = {
    "generate_sql_via_nlsql": lambda args: handle_generate_sql(
        business_line=args["business_line"],
        data_type=args["data_type"],
    ),
    "save_sql_file": lambda args: handle_save_sql(
        metric_name=args["metric_name"],
        sql=args["sql"],
    ),
    "execute_query": lambda args: handle_execute_query(sql=args["sql"]),
    "save_csv": lambda args: handle_save_csv(
        csv_content=args["csv_content"],
        topic=args["topic"],
    ),
    "generate_chart": lambda args: handle_generate_chart(
        csv_content=args["csv_content"],
        chart_type=args["chart_type"],
        title=args["title"],
        x_column=args["x_column"],
        y_column=args["y_column"],
        topic=args["topic"],
    ),
    "publish_to_feishu": lambda args: handle_publish_to_feishu(
        title=args["title"],
        markdown_content=args["markdown_content"],
    ),
    "anomaly_detect": lambda args: handle_anomaly_detect(
        csv_data=args["csv_data"],
        metric_column=args["metric_column"],
        date_column=args["date_column"],
    ),
    "event_correlate": lambda args: handle_event_correlate(
        anomaly_dates=args["anomaly_dates"],
    ),
    "trend_forecast": lambda args: handle_trend_forecast(
        csv_data=args["csv_data"],
        metric_column=args["metric_column"],
        date_column=args["date_column"],
        forecast_days=args.get("forecast_days", 7),
    ),
    "period_compare": lambda args: handle_period_compare(
        sql=args["sql"],
        compare_type=args["compare_type"],
        metric_column=args["metric_column"],
    ),
    "auto_drilldown": lambda args: handle_auto_drilldown(
        sql=args["sql"],
        dimensions=args["dimensions"],
        metric_column=args["metric_column"],
    ),
}
