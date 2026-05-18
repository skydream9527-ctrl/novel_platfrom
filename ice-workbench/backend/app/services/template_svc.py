"""Task templates. Source of truth: tasks/.templates/{tid}/template.json."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from pathlib import Path

from ..core.errors import APIError, ErrorCode
from ..core.storage import get_paths, read_json, write_json


def _now() -> str:
    return datetime.now(tz=timezone.utc).isoformat()


def _new_id() -> str:
    return uuid.uuid4().hex


def _root() -> Path:
    p = get_paths().tasks / ".templates"
    p.mkdir(parents=True, exist_ok=True)
    return p


def list_templates(*, owner_id: str | None = None, visibility: str | None = None) -> list[dict]:
    out: list[dict] = []
    for d in sorted(_root().iterdir()):
        if not d.is_dir():
            continue
        meta = read_json(d / "template.json")
        if not meta:
            continue
        if owner_id and meta.get("owner_id") != owner_id and meta.get("visibility") != "public":
            continue
        if visibility and meta.get("visibility") != visibility:
            continue
        out.append(meta)
    out.sort(key=lambda m: m.get("created_at") or "", reverse=True)
    return out


def get_template(tid: str) -> dict | None:
    return read_json(_root() / tid / "template.json")


def create_template(*, owner_id: str, body: dict) -> dict:
    tid = _new_id()
    record = {
        "id": tid,
        "owner_id": owner_id,
        "name": body.get("name", "未命名模板"),
        "description": body.get("description"),
        "paradigm": body.get("paradigm", "biz"),
        "agent_id": body.get("agent_id"),
        "skill_ids": body.get("skill_ids") or [],
        "file_seeds": body.get("file_seeds") or [],
        "initial_prompt": body.get("initial_prompt"),
        "has_schedule": bool(body.get("has_schedule")),
        "schedule_config": body.get("schedule_config"),
        "visibility": body.get("visibility", "private"),
        "status": "draft",
        "reject_reason": None,
        "created_at": _now(),
        "updated_at": _now(),
    }
    d = _root() / tid
    d.mkdir(parents=True, exist_ok=True)
    write_json(d / "template.json", record)
    return record


def update_template(tid: str, owner_id: str, patch: dict) -> dict:
    rec = get_template(tid)
    if not rec:
        raise APIError(404, ErrorCode.RESOURCE_NOT_FOUND, "模板不存在")
    if rec["owner_id"] != owner_id:
        raise APIError(403, ErrorCode.PERMISSION_DENIED, "无权修改此模板")
    for k in (
        "name",
        "description",
        "paradigm",
        "agent_id",
        "skill_ids",
        "file_seeds",
        "initial_prompt",
        "has_schedule",
        "schedule_config",
        "visibility",
    ):
        if k in patch:
            rec[k] = patch[k]
    rec["updated_at"] = _now()
    write_json(_root() / tid / "template.json", rec)
    return rec


def delete_template(tid: str, owner_id: str, *, is_admin: bool = False) -> None:
    rec = get_template(tid)
    if not rec:
        return
    if not is_admin and rec["owner_id"] != owner_id:
        raise APIError(403, ErrorCode.PERMISSION_DENIED, "无权删除此模板")
    import shutil

    shutil.rmtree(_root() / tid, ignore_errors=True)


def review_template(tid: str, *, status: str, reject_reason: str | None = None) -> dict:
    rec = get_template(tid)
    if not rec:
        raise APIError(404, ErrorCode.RESOURCE_NOT_FOUND, "模板不存在")
    if status not in {"approved", "rejected", "draft"}:
        raise APIError(400, ErrorCode.VALIDATION_ERROR, "status 非法")
    rec["status"] = status
    rec["reject_reason"] = reject_reason if status == "rejected" else None
    rec["updated_at"] = _now()
    write_json(_root() / tid / "template.json", rec)
    return rec
