"""Scheduled tasks. Cron parsing + run history. Source of truth: tasks/{tid}/scheduled.json."""
from __future__ import annotations

import asyncio
import logging
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

from ..core.errors import APIError, ErrorCode
from ..core.storage import append_jsonl, get_paths, read_json, read_jsonl, write_json

log = logging.getLogger("scheduler")


def _now() -> datetime:
    return datetime.now(tz=timezone.utc)


def _now_iso() -> str:
    return _now().isoformat()


def _new_id() -> str:
    return uuid.uuid4().hex


# ---- cron parsing (minute hour dom month dow) ----

def _expand(field: str, lo: int, hi: int) -> set[int]:
    out: set[int] = set()
    for part in field.split(","):
        step = 1
        if "/" in part:
            base, s = part.split("/", 1)
            step = int(s)
            part = base
        if part == "*":
            rng = range(lo, hi + 1, step)
        elif "-" in part:
            a, b = part.split("-", 1)
            rng = range(int(a), int(b) + 1, step)
        else:
            rng = [int(part)]
        out.update(rng)
    return out


def _next_fire(expr: str, *, after: datetime) -> datetime | None:
    parts = expr.split()
    if len(parts) != 5:
        return None
    try:
        minutes = _expand(parts[0], 0, 59)
        hours = _expand(parts[1], 0, 23)
        doms = _expand(parts[2], 1, 31)
        months = _expand(parts[3], 1, 12)
        dows = _expand(parts[4], 0, 6)
    except ValueError:
        return None
    cur = after.replace(second=0, microsecond=0) + timedelta(minutes=1)
    for _ in range(60 * 24 * 366):
        if (
            cur.minute in minutes
            and cur.hour in hours
            and cur.day in doms
            and cur.month in months
            and (cur.weekday() + 1) % 7 in dows
        ):
            return cur
        cur += timedelta(minutes=1)
    return None


# ---- storage helpers ----


def _sched_path(tid: str) -> Path:
    return get_paths().task_dir(tid) / "scheduled.json"


def _runs_path(tid: str, sid: str) -> Path:
    return get_paths().task_dir(tid) / "scheduled_runs" / f"{sid}.jsonl"


def list_for_task(tid: str) -> list[dict]:
    return read_json(_sched_path(tid), default=[]) or []


def list_for_user(user_id: str) -> list[dict]:
    """Aggregate scheduled tasks across user's tasks."""
    paths = get_paths()
    out: list[dict] = []
    user_index = read_json(paths.user_tasks_index(user_id), default=[]) or []
    for entry in user_index:
        tid = entry.get("task_id")
        if not tid:
            continue
        for s in list_for_task(tid):
            out.append({**s, "task_id": tid, "task_name": entry.get("name")})
    if paths.tasks.exists():
        for d in paths.tasks.iterdir():
            if not d.is_dir():
                continue
            meta = read_json(d / "meta.json")
            if meta and meta.get("owner_id") == user_id:
                for s in list_for_task(meta["id"]):
                    if not any(o["id"] == s["id"] for o in out):
                        out.append({**s, "task_id": meta["id"], "task_name": meta.get("name")})
    return out


def get_one(tid: str, sid: str) -> dict | None:
    for s in list_for_task(tid):
        if s.get("id") == sid:
            return s
    return None


def create(*, task_id: str, owner_id: str, body: dict) -> dict:
    cron = (body.get("cron") or "").strip()
    if not cron or _next_fire(cron, after=_now()) is None:
        raise APIError(400, ErrorCode.VALIDATION_ERROR, "cron 表达式无效")
    sid = _new_id()
    record = {
        "id": sid,
        "task_id": task_id,
        "name": body.get("name") or f"Schedule {sid[:6]}",
        "owner_id": owner_id,
        "cron": cron,
        "prompt": body.get("prompt") or "",
        "channels": body.get("channels") or ["in_app"],
        "enabled": body.get("enabled", True),
        "created_at": _now_iso(),
        "updated_at": _now_iso(),
        "next_fire_at": _next_fire(cron, after=_now()).isoformat(),
        "last_fire_at": None,
    }
    items = list_for_task(task_id)
    items.append(record)
    write_json(_sched_path(task_id), items)
    return record


def update(task_id: str, sid: str, owner_id: str, patch: dict) -> dict:
    items = list_for_task(task_id)
    found = None
    for i, s in enumerate(items):
        if s["id"] == sid:
            found = i
            break
    if found is None:
        raise APIError(404, ErrorCode.RESOURCE_NOT_FOUND, "定时任务不存在")
    rec = items[found]
    if rec.get("owner_id") not in (owner_id, None):
        raise APIError(403, ErrorCode.PERMISSION_DENIED, "无权修改")
    if "cron" in patch:
        if _next_fire(patch["cron"], after=_now()) is None:
            raise APIError(400, ErrorCode.VALIDATION_ERROR, "cron 表达式无效")
        rec["cron"] = patch["cron"]
        rec["next_fire_at"] = _next_fire(patch["cron"], after=_now()).isoformat()
    for k in ("name", "prompt", "channels", "enabled"):
        if k in patch:
            rec[k] = patch[k]
    rec["updated_at"] = _now_iso()
    items[found] = rec
    write_json(_sched_path(task_id), items)
    return rec


def remove(task_id: str, sid: str, owner_id: str) -> None:
    items = list_for_task(task_id)
    items2 = [s for s in items if s["id"] != sid]
    if len(items2) == len(items):
        return
    write_json(_sched_path(task_id), items2)


def list_runs(task_id: str, sid: str, *, limit: int = 50) -> list[dict]:
    rows = read_jsonl(_runs_path(task_id, sid))
    return rows[-limit:][::-1]


async def run_now(task_id: str, sid: str, owner_id: str) -> dict:
    rec = get_one(task_id, sid)
    if not rec:
        raise APIError(404, ErrorCode.RESOURCE_NOT_FOUND, "定时任务不存在")
    return await _execute_run(task_id, rec, trigger="manual")


async def _execute_run(task_id: str, rec: dict, *, trigger: str) -> dict:
    from ..core.config import get_settings
    from . import llm_gateway, usage_svc
    from ..core.storage import read_json, get_paths

    sid = rec["id"]
    started = _now_iso()
    run = {
        "id": _new_id(),
        "scheduled_id": sid,
        "task_id": task_id,
        "trigger": trigger,
        "status": "running",
        "started_at": started,
        "ended_at": None,
        "prompt": rec.get("prompt"),
        "output": None,
        "error": None,
        "tokens": None,
    }
    try:
        if not get_settings().llm_enabled:
            run["status"] = "skipped"
            run["error"] = {
                "code": ErrorCode.LLM_KEY_MISSING,
                "message": "LLM 未配置，跳过执行",
            }
        else:
            meta = read_json(get_paths().task_meta(task_id), default={}) or {}
            ws_cfg = read_json(get_paths().task_workspace(task_id), default={}) or {}
            model_id = rec.get("model") or ws_cfg.get("model") or llm_gateway.resolve_model(None)
            result = await llm_gateway.complete_once(
                system_prompt="你是定时任务执行助手，按用户指令完成任务并简明输出结果。",
                messages=[{"role": "user", "content": rec.get("prompt") or ""}],
                model=model_id,
            )
            run["status"] = "success"
            run["output"] = (result.get("text") or "")[:4000]
            usage = result.get("usage") or {}
            run["tokens"] = {
                "input": int(usage.get("input_tokens") or 0),
                "output": int(usage.get("output_tokens") or 0),
            }
            run["model"] = result.get("model")
            try:
                await usage_svc.record_usage(
                    user_id=meta.get("owner_id"),
                    agent_id=meta.get("agent_id"),
                    task_id=task_id,
                    conversation_id=None,
                    model=result.get("model") or model_id,
                    input_tokens=int(usage.get("input_tokens") or 0),
                    output_tokens=int(usage.get("output_tokens") or 0),
                    success=True,
                )
            except Exception as exc:
                log.warning("scheduler record_usage failed: %s", exc)
    except Exception as e:
        run["status"] = "failed"
        run["error"] = {"code": "RUN_ERROR", "message": str(e)[:500]}
    finally:
        run["ended_at"] = _now_iso()
        append_jsonl(_runs_path(task_id, sid), run)
        # update last_fire_at + next_fire_at
        items = list_for_task(task_id)
        for i, s in enumerate(items):
            if s["id"] == sid:
                items[i]["last_fire_at"] = run["ended_at"]
                nf = _next_fire(s["cron"], after=_now())
                items[i]["next_fire_at"] = nf.isoformat() if nf else None
                break
        write_json(_sched_path(task_id), items)
    return run


# ---- background loop ----

_loop_task: asyncio.Task | None = None


async def scheduler_loop() -> None:
    log.info("scheduler loop started")
    while True:
        try:
            await asyncio.sleep(20)
            now = _now()
            paths = get_paths()
            if not paths.tasks.exists():
                continue
            for d in paths.tasks.iterdir():
                if not d.is_dir() or d.name.startswith("."):
                    continue
                items = read_json(d / "scheduled.json", default=[]) or []
                for s in items:
                    if not s.get("enabled"):
                        continue
                    nf_iso = s.get("next_fire_at")
                    if not nf_iso:
                        continue
                    try:
                        nf = datetime.fromisoformat(nf_iso)
                    except ValueError:
                        continue
                    if nf <= now:
                        try:
                            await _execute_run(d.name, s, trigger="cron")
                        except Exception as e:
                            log.warning("scheduler run failed task=%s sid=%s: %s", d.name, s["id"], e)
        except asyncio.CancelledError:
            break
        except Exception as e:
            log.exception("scheduler loop error: %s", e)


def start_loop() -> None:
    global _loop_task
    if _loop_task is None:
        _loop_task = asyncio.create_task(scheduler_loop(), name="scheduler-loop")


def stop_loop() -> None:
    global _loop_task
    if _loop_task:
        _loop_task.cancel()
        _loop_task = None
