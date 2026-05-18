"""read_agent_knowledge 工具契约测试。

用户预期：
- 能按相对路径读取 agents/<agent_id>/knowledge/ 下的文本资源
- 拒绝绝对路径、'..' 穿越、越界、二进制扩展、过大文件
- 缺少 agent_id 上下文时失败
- 缺失知识目录或文件时返回明确错误码
"""
from __future__ import annotations

from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
AB_KB = REPO_ROOT / "agents" / "ab-experiment" / "knowledge"


def _reset_caches(monkeypatch):
    monkeypatch.setenv("DATA_ROOT", str(REPO_ROOT))
    from app.core import config as cfg
    from app.core.storage import index_db
    from app.core.storage import paths as p

    cfg.get_settings.cache_clear()
    p.get_paths.cache_clear()
    index_db.get_index_db.cache_clear()


@pytest.mark.asyncio
async def test_read_agent_knowledge_happy_path(monkeypatch):
    _reset_caches(monkeypatch)
    assert (AB_KB / "index.yaml").exists(), "前置：ab-experiment/knowledge/index.yaml 必须存在"

    from app.services import tool_runner

    result = await tool_runner.execute_tool(
        "read_agent_knowledge",
        {"path": "index.yaml"},
        ctx={"agent_id": "ab-experiment"},
    )
    assert result.get("agent_id") == "ab-experiment"
    assert result.get("path") == "index.yaml"
    assert result.get("content"), "index.yaml 应当有内容"
    assert result.get("size_bytes", 0) > 0


@pytest.mark.asyncio
async def test_read_agent_knowledge_nested_file(monkeypatch):
    _reset_caches(monkeypatch)
    target = "rules/decision_matrix.yaml"
    assert (AB_KB / target).exists(), "前置：决策矩阵文件必须存在"

    from app.services import tool_runner

    result = await tool_runner.execute_tool(
        "read_agent_knowledge",
        {"path": target},
        ctx={"agent_id": "ab-experiment"},
    )
    assert result.get("path") == target
    assert "matrix" in (result.get("content") or "")


@pytest.mark.asyncio
async def test_read_agent_knowledge_requires_agent_context(monkeypatch):
    _reset_caches(monkeypatch)
    from app.services import tool_runner

    result = await tool_runner.execute_tool(
        "read_agent_knowledge",
        {"path": "index.yaml"},
        ctx={},
    )
    assert result.get("error_code") == "VALIDATION_ERROR"


@pytest.mark.asyncio
async def test_read_agent_knowledge_rejects_absolute(monkeypatch):
    _reset_caches(monkeypatch)
    from app.services import tool_runner

    result = await tool_runner.execute_tool(
        "read_agent_knowledge",
        {"path": "/etc/passwd"},
        ctx={"agent_id": "ab-experiment"},
    )
    assert result.get("error_code") == "VALIDATION_ERROR"


@pytest.mark.asyncio
async def test_read_agent_knowledge_rejects_traversal(monkeypatch):
    _reset_caches(monkeypatch)
    from app.services import tool_runner

    result = await tool_runner.execute_tool(
        "read_agent_knowledge",
        {"path": "../../backend/app/core/config.py"},
        ctx={"agent_id": "ab-experiment"},
    )
    assert result.get("error_code") == "VALIDATION_ERROR"


@pytest.mark.asyncio
async def test_read_agent_knowledge_rejects_binary(monkeypatch):
    _reset_caches(monkeypatch)
    assert (AB_KB / "event_tracking" / "event_tracking.db").exists(), (
        "前置：.db 文件必须存在以验证二进制拒绝"
    )

    from app.services import tool_runner

    result = await tool_runner.execute_tool(
        "read_agent_knowledge",
        {"path": "event_tracking/event_tracking.db"},
        ctx={"agent_id": "ab-experiment"},
    )
    assert result.get("error_code") == "UNSUPPORTED_FORMAT"


@pytest.mark.asyncio
async def test_read_agent_knowledge_missing_file(monkeypatch):
    _reset_caches(monkeypatch)
    from app.services import tool_runner

    result = await tool_runner.execute_tool(
        "read_agent_knowledge",
        {"path": "does/not/exist.yaml"},
        ctx={"agent_id": "ab-experiment"},
    )
    assert result.get("error_code") == "FILE_NOT_FOUND"


@pytest.mark.asyncio
async def test_read_agent_knowledge_missing_kb_dir(monkeypatch):
    _reset_caches(monkeypatch)
    from app.services import tool_runner

    # biz-insight 没有 knowledge/ 目录
    result = await tool_runner.execute_tool(
        "read_agent_knowledge",
        {"path": "anything.yaml"},
        ctx={"agent_id": "biz-insight"},
    )
    assert result.get("error_code") == "KNOWLEDGE_NOT_FOUND"


@pytest.mark.asyncio
async def test_read_agent_knowledge_empty_path(monkeypatch):
    _reset_caches(monkeypatch)
    from app.services import tool_runner

    result = await tool_runner.execute_tool(
        "read_agent_knowledge",
        {"path": ""},
        ctx={"agent_id": "ab-experiment"},
    )
    assert result.get("error_code") == "VALIDATION_ERROR"


def test_read_agent_knowledge_in_schema():
    """确保新工具被暴露在 BUILTIN_TOOL_SCHEMAS 中。"""
    from app.services import tool_runner

    names = [t["function"]["name"] for t in tool_runner.BUILTIN_TOOL_SCHEMAS]
    assert "read_agent_knowledge" in names


def test_read_agent_knowledge_in_callable_catalog():
    """确保新工具被加入全局可调用工具白名单。"""
    import inspect

    from app.services import experience_card_svc

    src = inspect.getsource(experience_card_svc._build_skill_catalog_section)
    assert "read_agent_knowledge" in src, (
        "read_agent_knowledge 必须出现在 _build_skill_catalog_section 的 callable_names 中"
    )
