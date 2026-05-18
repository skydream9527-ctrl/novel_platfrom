"""Agents and Skills exposed via filesystem under agents/ and skills/."""
from __future__ import annotations

from pathlib import Path

from ..core.storage import get_paths, read_json

_DEFAULT_AGENTS = [
    {
        "id": "biz-insight",
        "name": "经营洞察 Agent",
        "paradigm": "biz",
        "icon": "📈",
        "color": "#d4a34e",
        "description": "经营数据拆解归因与趋势洞察，帮助团队快速定位业务问题",
        "publish_status": "published",
        "system_prompt": (
            "你是一名专业的经营分析 Agent，帮助产品团队从经营数据中发现关键洞察。\n\n"
            "核心原则：\n"
            "1. 数据查询必须先确认指标口径\n"
            "2. 渠道归因优先检查自然流量与推荐渠道的版本影响\n"
            "3. 季度报告必须包含同比和环比"
        ),
    },
    {
        "id": "ab-experiment",
        "name": "实验分析 Agent",
        "paradigm": "ab",
        "icon": "⚖",
        "color": "#7bafd4",
        "description": "AB 实验显著性检验、样本均衡、效应量评估",
        "publish_status": "published",
        "system_prompt": "你是一名 AB 实验分析专家，遵循统计严谨的标准。",
    },
    {
        "id": "wave-attribution",
        "name": "波动归因 Agent",
        "paradigm": "wave",
        "icon": "🔥",
        "color": "#c97b7b",
        "description": "多维下钻指标异常根因定位",
        "publish_status": "published",
        "system_prompt": "你是一名指标异常归因专家，按渠道、版本、地域等维度逐层下钻。",
    },
    {
        "id": "data-analysis",
        "name": "数据分析 Agent",
        "paradigm": "data",
        "icon": "📊",
        "color": "#6baa8e",
        "description": "自然语言生成 SQL 查询，自动可视化",
        "publish_status": "published",
        "system_prompt": "你是一名 NL→SQL 助手，写完 SQL 后再做可视化建议。",
    },
    {
        "id": "gray-release",
        "name": "灰度版本 Agent",
        "paradigm": "gray",
        "icon": "🌐",
        "color": "#9b8ec4",
        "description": "灰度版本对比与放量决策建议",
        "publish_status": "published",
        "system_prompt": "你是一名灰度发布分析助手，关注版本间的关键指标差异。",
    },
]


def _ensure_seed_agents() -> None:
    paths = get_paths()
    paths.agents.mkdir(parents=True, exist_ok=True)
    for a in _DEFAULT_AGENTS:
        d = paths.agents / a["id"]
        d.mkdir(parents=True, exist_ok=True)
        cfg_path = d / "agent.json"
        if not cfg_path.exists():
            from ..core.storage import write_json

            write_json(cfg_path, a)
        prompt_dir = d / "prompt"
        prompt_dir.mkdir(parents=True, exist_ok=True)
        sp_path = prompt_dir / "system.md"
        if not sp_path.exists():
            sp_path.write_text(a.get("system_prompt", ""), encoding="utf-8")


def list_agents() -> list[dict]:
    _ensure_seed_agents()
    paths = get_paths()
    out: list[dict] = []
    if not paths.agents.exists():
        return out
    for d in sorted(paths.agents.iterdir()):
        if not d.is_dir():
            continue
        cfg = read_json(d / "agent.json")
        if cfg:
            out.append(cfg)
    return out


def get_agent(agent_id: str) -> dict | None:
    _ensure_seed_agents()
    cfg = read_json(get_paths().agents / agent_id / "agent.json")
    return cfg


def get_agent_system_prompt(agent_id: str) -> str:
    _ensure_seed_agents()
    md_path: Path = get_paths().agents / agent_id / "prompt" / "system.md"
    if md_path.exists():
        return md_path.read_text(encoding="utf-8")
    cfg = get_agent(agent_id) or {}
    return cfg.get("system_prompt", "你是一名通用 AI 助手。")


def list_skills() -> list[dict]:
    """Builtin tool descriptors are exposed as Skills for now."""
    from .tool_runner import BUILTIN_TOOL_SCHEMAS

    return [
        {
            "id": t["function"]["name"],
            "name": t["_meta"]["display_name"],
            "description": t["function"]["description"],
            "category": "builtin",
            "tool_entry": "app.services.tool_runner:" + t["function"]["name"],
            "tool_schema": t["function"],
        }
        for t in BUILTIN_TOOL_SCHEMAS
    ]
