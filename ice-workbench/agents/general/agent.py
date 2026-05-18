"""General Agent (全能助手) — integrates all agent capabilities."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from shared.runtime import AgentDefinition
from shared.tool_registry import ToolDef

from tools import (
    handle_query_data,
    handle_generate_chart,
    handle_search_knowledge,
    handle_web_search,
    handle_web_fetch,
    handle_create_document,
    handle_feishu_read,
    handle_feishu_publish,
    handle_anomaly_detect,
    handle_trend_forecast,
    handle_period_compare,
)

AGENT_DIR = Path(__file__).resolve().parent

TOOLS = [
    ToolDef(
        name="query_data",
        description="通过 SQL 查询业务数据（浏览器/信息流/搜索等）",
        parameters={
            "type": "object",
            "properties": {
                "sql": {"type": "string", "description": "要执行的 SQL 查询"},
                "database": {"type": "string", "description": "数据库标识", "default": "default"},
            },
            "required": ["sql"],
        },
        handler=lambda args: handle_query_data(
            sql=args["sql"], database=args.get("database", "default")
        ),
    ),
    ToolDef(
        name="generate_chart",
        description="根据数据生成可视化图表",
        parameters={
            "type": "object",
            "properties": {
                "data": {"type": "string", "description": "CSV 格式的数据"},
                "chart_type": {"type": "string", "enum": ["line", "bar", "pie", "scatter"]},
                "title": {"type": "string", "description": "图表标题"},
            },
            "required": ["data", "chart_type", "title"],
        },
        handler=lambda args: handle_generate_chart(
            data=args["data"], chart_type=args["chart_type"], title=args["title"]
        ),
    ),
    ToolDef(
        name="search_knowledge",
        description="搜索知识库（飞书 + Mify RAG）",
        parameters={
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "搜索问题"},
                "source": {"type": "string", "enum": ["all", "feishu", "mify"], "default": "all"},
            },
            "required": ["query"],
        },
        handler=lambda args: handle_search_knowledge(
            query=args["query"], source=args.get("source", "all")
        ),
    ),
    ToolDef(
        name="web_search",
        description="搜索互联网获取最新信息",
        parameters={
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "搜索关键词"},
            },
            "required": ["query"],
        },
        handler=lambda args: handle_web_search(query=args["query"]),
    ),
    ToolDef(
        name="web_fetch",
        description="抓取指定网页的内容",
        parameters={
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "网页 URL"},
            },
            "required": ["url"],
        },
        handler=lambda args: handle_web_fetch(url=args["url"]),
    ),
    ToolDef(
        name="create_document",
        description="生成结构化文档（PRD、方案、报告等）",
        parameters={
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "文档标题"},
                "content": {"type": "string", "description": "Markdown 内容"},
                "format": {"type": "string", "enum": ["md", "html"], "default": "md"},
            },
            "required": ["title", "content"],
        },
        handler=lambda args: handle_create_document(
            title=args["title"], content=args["content"], format=args.get("format", "md")
        ),
    ),
    ToolDef(
        name="feishu_read",
        description="读取飞书文档内容",
        parameters={
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "飞书文档 URL"},
            },
            "required": ["url"],
        },
        handler=lambda args: handle_feishu_read(url=args["url"]),
    ),
    ToolDef(
        name="feishu_publish",
        description="将内容发布到飞书知识库",
        parameters={
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "文档标题"},
                "content": {"type": "string", "description": "Markdown 内容"},
            },
            "required": ["title", "content"],
        },
        handler=lambda args: handle_feishu_publish(
            title=args["title"], content=args["content"]
        ),
    ),
    ToolDef(
        name="anomaly_detect",
        description="对时序数据进行异常检测",
        parameters={
            "type": "object",
            "properties": {
                "data": {"type": "string", "description": "CSV 格式数据"},
                "metric": {"type": "string", "description": "指标列名"},
                "date_col": {"type": "string", "description": "日期列名", "default": "date"},
            },
            "required": ["data", "metric"],
        },
        handler=lambda args: handle_anomaly_detect(
            data=args["data"], metric=args["metric"], date_col=args.get("date_col", "date")
        ),
    ),
    ToolDef(
        name="trend_forecast",
        description="对时序数据进行趋势预测",
        parameters={
            "type": "object",
            "properties": {
                "data": {"type": "string", "description": "CSV 格式数据"},
                "metric": {"type": "string", "description": "指标列名"},
                "days": {"type": "integer", "description": "预测天数", "default": 7},
            },
            "required": ["data", "metric"],
        },
        handler=lambda args: handle_trend_forecast(
            data=args["data"], metric=args["metric"], days=args.get("days", 7)
        ),
    ),
    ToolDef(
        name="period_compare",
        description="环比或同比对比分析",
        parameters={
            "type": "object",
            "properties": {
                "sql": {"type": "string", "description": "基础查询 SQL"},
                "compare_type": {"type": "string", "enum": ["wow", "yoy"]},
                "metric": {"type": "string", "description": "对比指标"},
            },
            "required": ["sql", "compare_type", "metric"],
        },
        handler=lambda args: handle_period_compare(
            sql=args["sql"], compare_type=args["compare_type"], metric=args["metric"]
        ),
    ),
]

agent_definition = AgentDefinition(
    name="general_agent",
    prompt_dir=AGENT_DIR / "prompt",
    skills_dir=AGENT_DIR / "skills",
    tools=TOOLS,
    config={
        "display_name": "全能助手",
        "icon": "🤖",
        "color": "blue",
    },
)
