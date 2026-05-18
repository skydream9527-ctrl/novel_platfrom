"""Skill tool execution. Builtins are globally callable across Agents.

Tools available regardless of which Agent the conversation is bound to:
    - now / echo            : trivial demo
    - kyuubi_query          : SELECT via xiaomi-kyuubi-cli
    - feishu_publish        : create a Feishu doc via the bundled `feishu` CLI
    - write_file            : drop generated content into the task workspace
                              (tasks/{tid}/files/output/...) so it shows up in
                              the left-side file panel.
"""
from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Any

from ..core.config import get_settings
from ..core.errors import ErrorCode

# Built-in demo tools usable without external services.
BUILTIN_TOOL_SCHEMAS: list[dict] = [
    {
        "type": "function",
        "function": {
            "name": "now",
            "description": "Return the current UTC datetime in ISO 8601.",
            "parameters": {"type": "object", "properties": {}},
        },
        "_meta": {"display_name": "当前时间"},
    },
    {
        "type": "function",
        "function": {
            "name": "echo",
            "description": "Echo back the given text. Useful for testing tool calling.",
            "parameters": {
                "type": "object",
                "properties": {"text": {"type": "string"}},
                "required": ["text"],
            },
        },
        "_meta": {"display_name": "回声"},
    },
    {
        "type": "function",
        "function": {
            "name": "kyuubi_query",
            "description": (
                "Run a SELECT against Xiaomi Kyuubi SQL gateway. Read-only. "
                "The server already has the connection context configured "
                "(region=chnbj, workspace=11329, catalog=iceberg_zjyprc_hadoop, "
                "engine=presto, token=***). Do NOT ask the user for any of these — "
                "just call with the `sql` argument. Use fully-qualified table names "
                "like `iceberg_zjyprc_hadoop.<schema>.<table>`. Always include LIMIT."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "sql": {
                        "type": "string",
                        "description": "The SELECT statement to execute. Must include LIMIT.",
                    },
                    "limit": {
                        "type": "integer",
                        "default": 100,
                        "description": "Optional row cap, defaults to 100.",
                    },
                },
                "required": ["sql"],
            },
        },
        "_meta": {"display_name": "SQL 查询"},
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": (
                "Write text content to a file in the current task workspace. "
                "The file is registered under tasks/{task_id}/files/output/ and "
                "appears immediately in the user's left-side file panel. "
                "Use this whenever you produce a deliverable the user should be "
                "able to open / download / iterate on (markdown report, SQL "
                "script, CSV data, JSON, etc.). DO NOT use it for in-line answers."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Filename including extension, e.g. 'report.md', 'query.sql', 'data.csv'.",
                    },
                    "content": {
                        "type": "string",
                        "description": "Full file content as text (UTF-8).",
                    },
                },
                "required": ["name", "content"],
            },
        },
        "_meta": {"display_name": "保存文件到工作区"},
    },
    {
        "type": "function",
        "function": {
            "name": "list_files",
            "description": (
                "List every file currently in this task's workspace, including "
                "files the user uploaded (`uploaded`), inputs received from "
                "previous tool calls (`input`), and previous-turn deliverables "
                "you wrote with write_file (`output`). Call this at the start "
                "of a turn whenever the user references 'the file we made', "
                "'上一轮的产物', '刚才那份报告', or any prior artifact you "
                "may have lost from context. Returns id/name/scope/format/size."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "scope": {
                        "type": "string",
                        "enum": ["all", "uploaded", "input", "output"],
                        "description": "Filter by scope. Default 'all'.",
                    },
                },
            },
        },
        "_meta": {"display_name": "列出工作区文件"},
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": (
                "Read the contents of a file in this task's workspace. Accepts "
                "either the file's `id` (preferred — get from list_files) or "
                "its `name`. Text formats (.md/.txt/.csv/.tsv/.sql/.py/.json/"
                ".log/.yml/.yaml) return UTF-8 content; binary files return "
                "{is_binary: true} so you can advise the user to open it. Use "
                "this to pick up where a previous turn left off — e.g. read "
                "`query.sql` from last round before refining it."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "id": {"type": "string", "description": "File id from list_files."},
                    "name": {"type": "string", "description": "Filename, e.g. 'query.sql'."},
                },
            },
        },
        "_meta": {"display_name": "读取工作区文件"},
    },
    {
        "type": "function",
        "function": {
            "name": "feishu_publish",
            "description": (
                "Publish a markdown document to Feishu (lark) via the bundled "
                "`feishu` CLI. Uses the host's logged-in feishu account; if the "
                "user has not authenticated the CLI, returns FEISHU_CLI_ERROR "
                "with stderr. Returns the doc URL on success — INCLUDE the URL "
                "in your reply so the user can open it."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "Document title."},
                    "markdown": {
                        "type": "string",
                        "description": "Document body in Feishu-flavored markdown.",
                    },
                },
                "required": ["title", "markdown"],
            },
        },
        "_meta": {"display_name": "发布到飞书文档"},
    },
    {
        "type": "function",
        "function": {
            "name": "read_agent_knowledge",
            "description": (
                "Read a file from the current Agent's knowledge base "
                "(agents/<agent_id>/knowledge/<path>). Use this to fetch SQL "
                "templates, event-tracking indexes, page-structure specs, "
                "historical cases, and other reference data that is NOT part "
                "of the always-on system prompt. Start by reading "
                "`index.yaml` to see what's available, then drill in. "
                "Supports text formats (.yaml/.yml/.md/.json/.txt/.sql). "
                "Binary files (.db, images) are rejected — ask the user or "
                "use a different tool. Path must be relative within the "
                "agent's knowledge directory; '..' and absolute paths are "
                "rejected."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": (
                            "Relative path inside knowledge/, e.g. "
                            "'index.yaml', 'metrics/sql_templates/browser_feed.yaml', "
                            "'analysis/cases_and_lessons.yaml'."
                        ),
                    },
                },
                "required": ["path"],
            },
        },
        "_meta": {"display_name": "读取 Agent 知识库"},
    },
    {
        "type": "function",
        "function": {
            "name": "read_skill",
            "description": (
                "Fetch the full SKILL.md instructions for an agentic skill. "
                "Call this BEFORE attempting to execute an agentic skill (e.g. "
                "`nl-sql`, `feishu`, `pptx`, `xlsx`, `pdf`, `docx`, `notebooklm`, "
                "`planning-with-files`, `manimgl-best-practices`, etc.) when the "
                "user's request matches the skill's trigger conditions. The "
                "returned content is the canonical instruction set — follow it "
                "step by step. Do NOT call read_skill for function-callable "
                "tools (now / echo / kyuubi_query / write_file / feishu_publish)."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "skill_id": {
                        "type": "string",
                        "description": "ID from the skill catalog, e.g. 'nl-sql', 'feishu', 'pptx'.",
                    },
                },
                "required": ["skill_id"],
            },
        },
        "_meta": {"display_name": "读取 Skill 说明"},
    },
]


def get_anthropic_tools() -> list[dict]:
    """Convert BUILTIN_TOOL_SCHEMAS to Anthropic native tool schema."""
    out = []
    for t in BUILTIN_TOOL_SCHEMAS:
        fn = t["function"]
        out.append(
            {
                "name": fn["name"],
                "description": fn["description"],
                "input_schema": fn["parameters"],
            }
        )
    return out


def get_display_name(tool_name: str) -> str:
    for t in BUILTIN_TOOL_SCHEMAS:
        if t["function"]["name"] == tool_name:
            return t["_meta"]["display_name"]
    return tool_name


async def _tool_now(_: dict, ctx: dict | None = None) -> Any:
    return {"now": datetime.now(tz=timezone.utc).isoformat()}


async def _tool_echo(args: dict, ctx: dict | None = None) -> Any:
    await asyncio.sleep(0.1)
    return {"echo": args.get("text", "")}


async def _tool_kyuubi(args: dict, ctx: dict | None = None) -> Any:
    """Run a SQL query through the bundled `kyuubi` CLI.

    The connection context (region / workspace / catalog / engine / token) is
    pinned in server settings so the LLM never has to ask the user about it.
    Caller passes only `sql` (and optional `limit`).

    Records every attempt to sql_audit regardless of outcome.
    """
    import json as _json
    import os
    import shutil
    import time

    from . import sql_audit_svc

    sql = (args.get("sql") or "").strip()
    limit = int(args.get("limit") or 100)
    decision, reason = sql_audit_svc.classify(sql)
    started = time.monotonic()
    s = get_settings()

    conn_ctx = {
        "region": s.KYUUBI_REGION,
        "workspace": s.KYUUBI_WORKSPACE,
        "catalog": s.KYUUBI_CATALOG,
        "engine": s.KYUUBI_ENGINE,
    }

    out: Any
    error_message: str | None = None
    rows_returned: int | None = None

    cli_path = shutil.which("kyuubi")

    if decision == "block":
        out = {"error_code": "SQL_BLOCKED", "message": reason, "context": conn_ctx}
    elif not s.KYUUBI_TOKEN:
        out = {
            "error_code": ErrorCode.KYUUBI_NOT_CONFIGURED,
            "message": "Kyuubi 未配置：请管理员在 .env 设置 KYUUBI_TOKEN",
            "context": conn_ctx,
        }
    elif not cli_path:
        out = {
            "error_code": ErrorCode.KYUUBI_NOT_CONFIGURED,
            "message": (
                "Kyuubi CLI 未安装：请管理员在后端环境安装 `kyuubi` 命令行（pipx install xiaomi-kyuubi-cli）"
            ),
            "context": conn_ctx,
        }
    else:
        try:
            env = {**os.environ, "KYUUBI_APIKEY": s.KYUUBI_TOKEN}
            cmd = [
                cli_path, "sql", "query", sql,
                "--region", conn_ctx["region"],
                "--workspace", conn_ctx["workspace"],
                "--catalog", conn_ctx["catalog"],
                "--engine", conn_ctx["engine"],
                "--format", "json",
                "--limit", str(limit),
            ]
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env,
            )
            try:
                stdout_b, stderr_b = await asyncio.wait_for(proc.communicate(), timeout=120.0)
            except asyncio.TimeoutError:
                proc.kill()
                await proc.wait()
                error_message = "kyuubi CLI timeout (120s)"
                out = {"error_code": "KYUUBI_TIMEOUT", "message": error_message, "context": conn_ctx}
            else:
                stdout_s = stdout_b.decode(errors="replace")
                stderr_s = stderr_b.decode(errors="replace")
                if proc.returncode != 0:
                    error_message = (stderr_s.strip() or f"kyuubi exit {proc.returncode}")[:600]
                    out = {
                        "error_code": "KYUUBI_CLI_ERROR",
                        "message": error_message,
                        "context": conn_ctx,
                    }
                else:
                    try:
                        data = _json.loads(stdout_s)
                    except _json.JSONDecodeError:
                        out = {
                            "columns": [],
                            "rows": [],
                            "row_count": 0,
                            "raw_output": stdout_s.strip()[:4000],
                            "context": conn_ctx,
                            "warning": reason if decision == "warn" else None,
                        }
                    else:
                        cols = data.get("columns") or []
                        col_names = [c.get("name") if isinstance(c, dict) else c for c in cols]
                        rows = data.get("rows") or []
                        rows_returned = len(rows)
                        out = {
                            "columns": col_names,
                            "rows": rows[:limit],
                            "row_count": rows_returned,
                            "context": conn_ctx,
                            "warning": reason if decision == "warn" else None,
                        }
        except Exception as e:
            error_message = str(e)[:300]
            out = {"error_code": "KYUUBI_CLI_ERROR", "message": error_message, "context": conn_ctx}

    try:
        await sql_audit_svc.record(
            user_id=(ctx or {}).get("user_id"),
            agent_id=(ctx or {}).get("agent_id"),
            task_id=(ctx or {}).get("task_id"),
            conversation_id=(ctx or {}).get("conversation_id"),
            sql=sql,
            decision=decision,
            block_reason=reason if decision != "allow" else None,
            error_message=error_message,
            rows_returned=rows_returned,
            duration_ms=int((time.monotonic() - started) * 1000),
        )
    except Exception:
        pass
    return out


async def _tool_write_file(args: dict, ctx: dict | None = None) -> Any:
    """Write content into the task's workspace files/output and register it."""
    from . import file_svc

    name = (args.get("name") or "").strip()
    content = args.get("content") or ""
    if not name:
        return {"error_code": "VALIDATION_ERROR", "message": "name is required"}
    if not isinstance(content, str):
        return {"error_code": "VALIDATION_ERROR", "message": "content must be a string"}
    task_id = (ctx or {}).get("task_id")
    user_id = (ctx or {}).get("user_id")
    if not task_id or not user_id:
        return {
            "error_code": "VALIDATION_ERROR",
            "message": "write_file is only available in a task context",
        }
    try:
        meta = await file_svc.upload_task_file(
            task_id=task_id,
            owner_id=user_id,
            filename=name,
            data=content.encode("utf-8"),
            scope="output",
        )
    except Exception as e:
        return {"error_code": "WRITE_FILE_FAILED", "message": str(e)[:300]}
    return {
        "saved": True,
        "file_id": meta["id"],
        "name": meta["name"],
        "size_bytes": meta["size_bytes"],
        "scope": "output",
        "path": meta["path"],
        "message": f"已保存到工作区：{meta['name']}（{meta['size_bytes']} bytes）",
    }


async def _tool_feishu_publish(args: dict, ctx: dict | None = None) -> Any:
    """Create a Feishu doc via the bundled `feishu` CLI."""
    import json as _json
    import shutil
    import tempfile
    from pathlib import Path

    title = (args.get("title") or "").strip()
    markdown = args.get("markdown") or ""
    if not title:
        return {"error_code": "VALIDATION_ERROR", "message": "title is required"}
    cli = shutil.which("feishu")
    if not cli:
        return {
            "error_code": "FEISHU_CLI_NOT_INSTALLED",
            "message": "feishu CLI 未安装；请管理员在后端环境安装 feishu 命令行",
        }

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".md", delete=False, encoding="utf-8"
    ) as f:
        f.write(markdown)
        tmp_path = f.name
    try:
        proc = await asyncio.create_subprocess_exec(
            cli, "docx", "create", title, "-f", tmp_path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        try:
            out_b, err_b = await asyncio.wait_for(proc.communicate(), timeout=90.0)
        except asyncio.TimeoutError:
            proc.kill()
            await proc.wait()
            return {"error_code": "FEISHU_CLI_TIMEOUT", "message": "feishu CLI timeout (90s)"}
    finally:
        Path(tmp_path).unlink(missing_ok=True)

    out_s = out_b.decode(errors="replace")
    err_s = err_b.decode(errors="replace")
    # Reference impl: rc 0/2/3 all carry a usable doc_token; 2/3 = warnings only.
    if proc.returncode not in (0, 2, 3):
        return {
            "error_code": "FEISHU_CLI_ERROR",
            "message": (err_s.strip() or f"feishu exit {proc.returncode}")[:600],
        }
    try:
        data = _json.loads(out_s)
    except _json.JSONDecodeError:
        return {"raw_output": out_s.strip()[:2000]}
    return {
        "url": data.get("url", ""),
        "doc_token": data.get("doc_token", ""),
        "title": title,
        "warning": err_s.strip() if proc.returncode in (2, 3) else None,
    }


async def _tool_list_files(args: dict, ctx: dict | None = None) -> Any:
    """List every file in the current task workspace."""
    from . import file_svc

    task_id = (ctx or {}).get("task_id")
    if not task_id:
        return {"error_code": "VALIDATION_ERROR", "message": "list_files needs a task context"}
    scope = (args.get("scope") or "all").lower()
    if scope not in ("all", "uploaded", "input", "output"):
        return {"error_code": "VALIDATION_ERROR", "message": f"invalid scope: {scope}"}
    items = await file_svc.list_task_files(task_id)
    if scope != "all":
        items = [m for m in items if m.get("scope") == scope]
    out = [
        {
            "id": m["id"],
            "name": m["name"],
            "scope": m.get("scope"),
            "format": m.get("format"),
            "size_bytes": m.get("size_bytes"),
            "created_at": m.get("created_at"),
        }
        for m in items
    ]
    return {"files": out, "total": len(out), "scope": scope}


async def _tool_read_file(args: dict, ctx: dict | None = None) -> Any:
    """Read a workspace file by id or name."""
    from . import file_svc
    from ..core.errors import APIError

    task_id = (ctx or {}).get("task_id")
    if not task_id:
        return {"error_code": "VALIDATION_ERROR", "message": "read_file needs a task context"}

    file_id = (args.get("id") or "").strip()
    name = (args.get("name") or "").strip()
    if not file_id and not name:
        return {"error_code": "VALIDATION_ERROR", "message": "id 或 name 至少给一个"}

    if not file_id:
        items = await file_svc.list_task_files(task_id)
        # 同名按时间倒序，取最新（list_task_files 已按 created_at desc）
        match = next((m for m in items if m.get("name") == name), None)
        if not match:
            return {
                "error_code": "FILE_NOT_FOUND",
                "message": f"工作区里没有名为 `{name}` 的文件，请先用 list_files 查看。",
            }
        file_id = match["id"]

    try:
        result = await file_svc.read_file_text(task_id, file_id)
    except APIError as e:
        return {"error_code": e.error_code, "message": e.message}

    meta = result.get("meta") or {}
    if result.get("binary"):
        return {
            "id": file_id,
            "name": meta.get("name"),
            "scope": meta.get("scope"),
            "format": meta.get("format"),
            "is_binary": True,
            "size_bytes": meta.get("size_bytes"),
            "message": "二进制文件，无法以文本形式返回。",
        }
    return {
        "id": file_id,
        "name": meta.get("name"),
        "scope": meta.get("scope"),
        "format": meta.get("format"),
        "size_bytes": meta.get("size_bytes"),
        "content": result.get("content") or "",
    }


_KNOWLEDGE_TEXT_EXTS = {".yaml", ".yml", ".md", ".json", ".txt", ".sql"}
_KNOWLEDGE_MAX_BYTES = 200 * 1024  # 200KB


async def _tool_read_agent_knowledge(args: dict, ctx: dict | None = None) -> Any:
    """Read a file from agents/<agent_id>/knowledge/<path>.

    Security: rejects absolute paths, traversal ('..'), and anything resolving
    outside the agent's knowledge directory. Rejects binary extensions; caps
    size at 200KB.
    """
    from ..core.storage import get_paths

    agent_id = (ctx or {}).get("agent_id")
    if not agent_id:
        return {
            "error_code": "VALIDATION_ERROR",
            "message": "read_agent_knowledge needs an agent context",
        }

    raw = (args.get("path") or "").strip()
    if not raw:
        return {"error_code": "VALIDATION_ERROR", "message": "path is required"}

    from pathlib import Path, PurePosixPath

    pp = PurePosixPath(raw)
    if pp.is_absolute() or any(part == ".." for part in pp.parts):
        return {
            "error_code": "VALIDATION_ERROR",
            "message": "path must be relative and must not contain '..'",
        }

    base = (get_paths().agents / agent_id / "knowledge").resolve()
    if not base.exists():
        return {
            "error_code": "KNOWLEDGE_NOT_FOUND",
            "message": f"agent '{agent_id}' has no knowledge/ directory",
        }

    target = (base / raw).resolve()
    try:
        target.relative_to(base)
    except ValueError:
        return {
            "error_code": "VALIDATION_ERROR",
            "message": "path escapes the knowledge directory",
        }

    if not target.exists() or not target.is_file():
        return {
            "error_code": "FILE_NOT_FOUND",
            "message": f"knowledge file not found: {raw}",
        }

    ext = target.suffix.lower()
    if ext not in _KNOWLEDGE_TEXT_EXTS:
        return {
            "error_code": "UNSUPPORTED_FORMAT",
            "message": (
                f"binary/unsupported extension: {ext}. "
                f"Supported: {sorted(_KNOWLEDGE_TEXT_EXTS)}"
            ),
        }

    size = target.stat().st_size
    if size > _KNOWLEDGE_MAX_BYTES:
        return {
            "error_code": "FILE_TOO_LARGE",
            "message": f"{raw} is {size} bytes (limit {_KNOWLEDGE_MAX_BYTES})",
        }

    try:
        content = target.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return {
            "error_code": "ENCODING_ERROR",
            "message": f"{raw} is not valid UTF-8",
        }
    except OSError as e:
        return {"error_code": "READ_FAILED", "message": str(e)[:300]}

    return {
        "agent_id": agent_id,
        "path": raw,
        "size_bytes": size,
        "content": content,
    }


async def _tool_read_skill(args: dict, ctx: dict | None = None) -> Any:
    """Return the full SKILL.md body for an agentic skill."""
    from ..core.storage import get_paths

    sid = (args.get("skill_id") or "").strip()
    if not sid:
        return {"error_code": "VALIDATION_ERROR", "message": "skill_id is required"}
    p = get_paths().skills / sid / "SKILL.md"
    if not p.exists():
        return {
            "error_code": "SKILL_NOT_FOUND",
            "message": f"skill '{sid}' has no SKILL.md (not an agentic skill, or wrong id)",
        }
    try:
        text = p.read_text(encoding="utf-8")
    except OSError as e:
        return {"error_code": "SKILL_READ_FAILED", "message": str(e)[:300]}
    return {
        "skill_id": sid,
        "size_bytes": len(text.encode("utf-8")),
        "content": text,
    }


_DISPATCH = {
    "now": _tool_now,
    "echo": _tool_echo,
    "kyuubi_query": _tool_kyuubi,
    "write_file": _tool_write_file,
    "list_files": _tool_list_files,
    "read_file": _tool_read_file,
    "feishu_publish": _tool_feishu_publish,
    "read_skill": _tool_read_skill,
    "read_agent_knowledge": _tool_read_agent_knowledge,
}


async def execute_tool(name: str, args: dict, ctx: dict | None = None) -> Any:
    fn = _DISPATCH.get(name)
    if not fn:
        return {"error_code": "TOOL_NOT_FOUND", "message": f"unknown tool: {name}"}
    return await fn(args, ctx)
