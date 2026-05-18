"""Skill 目录契约测试。

用户预期：
- 仓库根目录的 skills/ 下每个真实 skill 都有 SKILL.md 与中文 INTRO.zh.md
- skill_svc.list_all 能把它们识别为 agentic 类型
- read_skill 工具对每个 agentic skill 都能成功返回内容
"""
from __future__ import annotations

from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SKILLS_DIR = REPO_ROOT / "skills"


def _real_skill_ids() -> list[str]:
    out: list[str] = []
    for d in sorted(SKILLS_DIR.iterdir()):
        if not d.is_dir() or d.name.startswith("."):
            continue
        if (d / "SKILL.md").exists():
            out.append(d.name)
    return out


REAL_SKILL_IDS = _real_skill_ids()


def test_skills_directory_not_empty():
    assert REAL_SKILL_IDS, f"skills/ 下没有任何 SKILL.md，实际目录: {SKILLS_DIR}"


@pytest.mark.parametrize("skill_id", REAL_SKILL_IDS)
def test_each_skill_has_zh_intro(skill_id: str):
    intro = SKILLS_DIR / skill_id / "INTRO.zh.md"
    assert intro.exists(), f"skill `{skill_id}` 缺中文介绍 INTRO.zh.md"
    text = intro.read_text(encoding="utf-8").strip()
    assert text, f"skill `{skill_id}` 的 INTRO.zh.md 是空文件"
    # 至少要包含触发场景或主要功能这类中文字段
    assert any(c >= "一" for c in text), f"skill `{skill_id}` INTRO.zh.md 不含中文"


@pytest.mark.parametrize("skill_id", REAL_SKILL_IDS)
def test_skill_md_has_frontmatter(skill_id: str):
    md = (SKILLS_DIR / skill_id / "SKILL.md").read_text(encoding="utf-8")
    assert md.lstrip().startswith("---"), f"skill `{skill_id}` SKILL.md 缺 frontmatter"


@pytest.mark.asyncio
async def test_skill_svc_lists_all_real_skills(monkeypatch):
    """skill_svc.list_all 在指向真实仓库时，应该能识别全部 14 个 agentic skill。"""
    monkeypatch.setenv("DATA_ROOT", str(REPO_ROOT))
    from app.core import config as cfg
    from app.core.storage import index_db
    from app.core.storage import paths as p

    cfg.get_settings.cache_clear()
    p.get_paths.cache_clear()
    index_db.get_index_db.cache_clear()

    from app.services import skill_svc

    items = skill_svc.list_all()
    agentic = {s["id"] for s in items if s.get("category") == "agentic"}
    assert agentic >= set(REAL_SKILL_IDS), (
        f"skill_svc.list_all 缺失 skill：{set(REAL_SKILL_IDS) - agentic}"
    )

    # 中文 description 已注入
    by_id = {s["id"]: s for s in items if s.get("category") == "agentic"}
    for sid in REAL_SKILL_IDS:
        s = by_id[sid]
        assert s.get("description_zh"), f"skill `{sid}` 没有 description_zh（INTRO.zh.md 没读出）"
        assert any(c >= "一" for c in s["description"]), (
            f"skill `{sid}` 的 description 不是中文"
        )


@pytest.mark.asyncio
@pytest.mark.parametrize("skill_id", REAL_SKILL_IDS)
async def test_read_skill_tool_returns_content(monkeypatch, skill_id: str):
    """read_skill 工具能把每个真实 skill 的 SKILL.md 完整返回。"""
    monkeypatch.setenv("DATA_ROOT", str(REPO_ROOT))
    from app.core import config as cfg
    from app.core.storage import index_db
    from app.core.storage import paths as p

    cfg.get_settings.cache_clear()
    p.get_paths.cache_clear()
    index_db.get_index_db.cache_clear()

    from app.services import tool_runner

    result = await tool_runner.execute_tool("read_skill", {"skill_id": skill_id})
    assert isinstance(result, dict)
    assert result.get("skill_id") == skill_id, f"read_skill 返回错误 skill_id：{result}"
    assert result.get("content"), f"read_skill 返回空内容：{result}"
    assert result["size_bytes"] > 100, f"skill `{skill_id}` 内容过短：{result['size_bytes']} bytes"


@pytest.mark.asyncio
async def test_read_skill_unknown_returns_error(monkeypatch):
    monkeypatch.setenv("DATA_ROOT", str(REPO_ROOT))
    from app.core import config as cfg
    from app.core.storage import index_db
    from app.core.storage import paths as p

    cfg.get_settings.cache_clear()
    p.get_paths.cache_clear()
    index_db.get_index_db.cache_clear()

    from app.services import tool_runner

    result = await tool_runner.execute_tool("read_skill", {"skill_id": "no-such-skill-xyz"})
    assert result.get("error_code") == "SKILL_NOT_FOUND"


@pytest.mark.asyncio
async def test_builtin_tools_runnable():
    """now / echo / read_skill 这三个无副作用的内置工具能直接调用。"""
    from app.services import tool_runner

    r = await tool_runner.execute_tool("now", {})
    assert r.get("now"), f"now 工具失败：{r}"

    r = await tool_runner.execute_tool("echo", {"text": "hi"})
    assert r.get("echo") == "hi", f"echo 工具失败：{r}"
