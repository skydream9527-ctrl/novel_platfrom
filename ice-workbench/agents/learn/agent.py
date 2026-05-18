"""Learn Agent — declarative registration for shared Runtime."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from shared.runtime import AgentDefinition
from shared.tool_registry import ToolDef

from tools import handle_web_fetch, handle_check_sources, handle_generate_digest, handle_import_links

AGENT_DIR = Path(__file__).resolve().parent

TOOLS = [
    ToolDef(
        name="web_fetch",
        description="抓取指定 URL 的网页正文内容",
        parameters={
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "要抓取的网页 URL"},
            },
            "required": ["url"],
        },
        handler=lambda args: handle_web_fetch(url=args["url"]),
    ),
    ToolDef(
        name="check_sources",
        description="巡检预设信息源，获取最新变化",
        parameters={
            "type": "object",
            "properties": {},
        },
        handler=lambda args: handle_check_sources(),
    ),
    ToolDef(
        name="generate_digest",
        description="生成本周学习周报草稿",
        parameters={
            "type": "object",
            "properties": {},
        },
        handler=lambda args: handle_generate_digest(),
    ),
    ToolDef(
        name="import_links",
        description="导入收件箱中的链接并进行学习",
        parameters={
            "type": "object",
            "properties": {},
        },
        handler=lambda args: handle_import_links(),
    ),
]

agent_definition = AgentDefinition(
    name="learn_agent",
    prompt_dir=AGENT_DIR / "prompt",
    skills_dir=AGENT_DIR / "skills",
    tools=TOOLS,
    config={
        "display_name": "学习研究 Agent",
        "icon": "🎓",
        "color": "amber",
    },
)
