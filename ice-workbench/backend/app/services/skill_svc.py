"""Custom skills (admin-managed). Source of truth: skills/{id}/skill.json.

Built-in skills (now / echo / kyuubi_query) are exposed via tool_runner; they're
read-only from admin. Custom skills are user-defined wrappers (calling external
HTTP endpoints) and live alongside built-ins.

For MVP we only support metadata + tool_schema editing + a test-run sandbox that
either matches a built-in (now/echo/kyuubi_query) or returns SKILL_NOT_RUNNABLE.
"""
from __future__ import annotations

import asyncio
import json
from pathlib import Path

from ..core.errors import APIError, ErrorCode
from ..core.storage import get_paths, read_json, write_json
from .tool_runner import BUILTIN_TOOL_SCHEMAS


def _skills_root() -> Path:
    p = get_paths().skills
    p.mkdir(parents=True, exist_ok=True)
    return p


def _skill_path(skill_id: str) -> Path:
    return _skills_root() / skill_id / "skill.json"


def list_all() -> list[dict]:
    """Return built-ins + custom skills + agentic SKILL.md descriptors.

    Three sources:
    1. BUILTIN_TOOL_SCHEMAS — function tools the LLM can call directly.
    2. skills/<id>/skill.json — admin-created custom skills (OpenAI tool_schema).
    3. skills/<id>/SKILL.md — agentic skills (Claude Skills format) where the
       agent reads the markdown for instructions; we surface them so users can
       tick-bind them in CreateTask Step 3 and the agent gets that context.
    """
    out: list[dict] = []
    for t in BUILTIN_TOOL_SCHEMAS:
        out.append(
            {
                "id": t["function"]["name"],
                "name": t["_meta"]["display_name"],
                "description": t["function"]["description"],
                "category": "builtin",
                "tool_entry": "app.services.tool_runner:" + t["function"]["name"],
                "tool_schema": t["function"],
                "builtin": True,
                "enabled": True,
            }
        )
    for d in sorted(_skills_root().iterdir()):
        if not d.is_dir() or d.name.startswith("."):
            continue
        cfg = read_json(d / "skill.json")
        if cfg:
            out.append({**cfg, "builtin": False})
            continue
        skill_md = d / "SKILL.md"
        if skill_md.exists():
            meta = _parse_skill_md_frontmatter(skill_md)
            if meta:
                # 优先读 INTRO.zh.md（中文展示文案），否则回落到 frontmatter description。
                zh_intro = _read_zh_intro(d)
                description = zh_intro or (meta.get("description") or "").strip()
                out.append(
                    {
                        "id": meta.get("name") or d.name,
                        "name": meta.get("name") or d.name,
                        "description": description,
                        "description_zh": zh_intro,  # 给前端做"是否已本地化"的判断
                        "category": "agentic",
                        "tool_entry": f"agentic:{d.name}",
                        "tool_schema": None,
                        "builtin": False,
                        "enabled": True,
                    }
                )
    return out


def _read_zh_intro(skill_dir: Path) -> str | None:
    """读 skills/{id}/INTRO.zh.md 作为中文展示文案。"""
    p = skill_dir / "INTRO.zh.md"
    if not p.exists():
        return None
    try:
        text = p.read_text(encoding="utf-8").strip()
    except OSError:
        return None
    return text or None


def _parse_skill_md_frontmatter(md_path: Path) -> dict | None:
    """Tiny YAML-ish parser for the `--- name: ... description: |- ... ---` header
    Claude-Skills uses. Only supports `name` (string) and `description` (multi-line
    `|`/`|-` block or single line); enough for surfacing in the picker."""
    try:
        text = md_path.read_text(encoding="utf-8")
    except OSError:
        return None
    if not text.startswith("---"):
        return None
    parts = text.split("---", 2)
    if len(parts) < 3:
        return None
    body = parts[1]
    out: dict = {}
    cur_key: str | None = None
    block_lines: list[str] = []
    for raw in body.splitlines():
        line = raw.rstrip("\n")
        if cur_key is None:
            if not line.strip() or line.lstrip().startswith("#"):
                continue
            if ":" in line:
                k, _, v = line.partition(":")
                k = k.strip()
                v = v.strip()
                if v in ("|", "|-"):
                    cur_key = k
                    block_lines = []
                else:
                    out[k] = v.strip('"').strip("'") if v else ""
        else:
            # within block
            if line.startswith(("  ", "\t")):
                block_lines.append(line.lstrip())
            elif line.strip() == "":
                block_lines.append("")
            else:
                out[cur_key] = "\n".join(block_lines).strip()
                cur_key = None
                block_lines = []
                if ":" in line:
                    k, _, v = line.partition(":")
                    out[k.strip()] = v.strip().strip('"').strip("'")
    if cur_key:
        out[cur_key] = "\n".join(block_lines).strip()
    return out if (out.get("name") or out.get("description")) else None


def get_skill(skill_id: str) -> dict | None:
    for s in list_all():
        if s["id"] == skill_id:
            return s
    return None


def validate_tool_schema(schema: dict) -> tuple[bool, str | None]:
    if not isinstance(schema, dict):
        return False, "tool_schema 必须为对象"
    if not schema.get("name"):
        return False, "缺少 name"
    if not schema.get("description"):
        return False, "缺少 description"
    params = schema.get("parameters") or {}
    if params and params.get("type") != "object":
        return False, "parameters.type 必须为 object"
    return True, None


def upsert_skill(*, skill_id: str | None, body: dict) -> dict:
    """Create or update a custom skill."""
    schema = body.get("tool_schema") or {}
    if isinstance(schema, str):
        try:
            schema = json.loads(schema)
        except json.JSONDecodeError as e:
            raise APIError(400, ErrorCode.VALIDATION_ERROR, f"tool_schema JSON 解析失败：{e}")
    ok, reason = validate_tool_schema(schema)
    if not ok:
        raise APIError(400, ErrorCode.VALIDATION_ERROR, f"tool_schema 无效：{reason}")
    sid = skill_id or schema["name"]
    if sid in {t["function"]["name"] for t in BUILTIN_TOOL_SCHEMAS}:
        raise APIError(400, ErrorCode.VALIDATION_ERROR, "不能与内置 Skill 同名")
    record = {
        "id": sid,
        "name": body.get("name") or schema.get("name"),
        "description": body.get("description") or schema.get("description"),
        "category": body.get("category", "custom"),
        "tool_entry": body.get("tool_entry") or f"custom:{sid}",
        "tool_schema": schema,
        "enabled": body.get("enabled", True),
    }
    d = _skills_root() / sid
    d.mkdir(parents=True, exist_ok=True)
    write_json(d / "skill.json", record)
    return record


def delete_skill(skill_id: str) -> None:
    if skill_id in {t["function"]["name"] for t in BUILTIN_TOOL_SCHEMAS}:
        raise APIError(400, ErrorCode.VALIDATION_ERROR, "不能删除内置 Skill")
    d = _skills_root() / skill_id
    if not d.exists():
        raise APIError(404, ErrorCode.RESOURCE_NOT_FOUND, "Skill 不存在")
    import shutil

    shutil.rmtree(d, ignore_errors=True)


async def test_run(skill_id: str, args: dict) -> dict:
    """Sandbox execution. Built-ins run via tool_runner; custom skills are
    placeholder for now (return TOOL_NOT_RUNNABLE)."""
    from . import tool_runner

    builtin_names = {t["function"]["name"] for t in BUILTIN_TOOL_SCHEMAS}
    if skill_id in builtin_names:
        try:
            result = await asyncio.wait_for(
                tool_runner.execute_tool(skill_id, args, ctx={"user_id": "admin-test"}),
                timeout=10,
            )
            return {"success": True, "result": result, "duration_ms": None}
        except asyncio.TimeoutError:
            return {"success": False, "error": "test-run 超时（10s）"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    skill = get_skill(skill_id)
    if not skill:
        raise APIError(404, ErrorCode.RESOURCE_NOT_FOUND, "Skill 不存在")
    return {
        "success": False,
        "error": "Custom skill 沙盒执行尚未实现（MVP 阶段，下轮交付）",
    }
