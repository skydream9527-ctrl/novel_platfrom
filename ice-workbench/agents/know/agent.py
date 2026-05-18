"""Knowledge Agent — declarative registration for shared Runtime."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from shared.runtime import AgentDefinition
from shared.tool_registry import ToolDef

from tools import (
    handle_feishu_read,
    handle_feishu_write,
    handle_feishu_search,
    handle_mify_search,
    handle_mify_upload,
)

AGENT_DIR = Path(__file__).resolve().parent

TOOLS = [
    ToolDef(
        name="feishu_read",
        description="读取飞书文档内容（wiki/docx/sheet）",
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
        name="feishu_write",
        description="在飞书知识库中创建新文档",
        parameters={
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "文档标题"},
                "content": {"type": "string", "description": "Markdown 内容"},
                "parent_node": {"type": "string", "description": "父节点 token（可选）"},
            },
            "required": ["title", "content"],
        },
        handler=lambda args: handle_feishu_write(
            title=args["title"],
            content=args["content"],
            parent_node=args.get("parent_node", ""),
        ),
    ),
    ToolDef(
        name="feishu_search",
        description="搜索飞书知识库文档",
        parameters={
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "搜索关键词"},
            },
            "required": ["query"],
        },
        handler=lambda args: handle_feishu_search(query=args["query"]),
    ),
    ToolDef(
        name="mify_search",
        description="通过 Mify RAG 进行语义知识检索",
        parameters={
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "搜索问题"},
                "kb_name": {"type": "string", "description": "知识库名称"},
                "top_k": {"type": "integer", "description": "返回结果数量", "default": 5},
            },
            "required": ["query"],
        },
        handler=lambda args: handle_mify_search(
            query=args["query"],
            kb_name=args.get("kb_name", "数据产品知识库beta"),
            top_k=args.get("top_k", 5),
        ),
    ),
    ToolDef(
        name="mify_upload",
        description="上传本地文件到 Mify RAG 知识库",
        parameters={
            "type": "object",
            "properties": {
                "kb_name": {"type": "string", "description": "知识库名称"},
                "file_path": {"type": "string", "description": "本地文件/目录路径"},
            },
            "required": ["kb_name", "file_path"],
        },
        handler=lambda args: handle_mify_upload(
            kb_name=args["kb_name"], file_path=args["file_path"]
        ),
    ),
]

agent_definition = AgentDefinition(
    name="know_agent",
    prompt_dir=AGENT_DIR / "prompt",
    skills_dir=AGENT_DIR / "skills",
    tools=TOOLS,
    config={
        "display_name": "知识库 Agent",
        "icon": "📚",
        "color": "purple",
    },
)
