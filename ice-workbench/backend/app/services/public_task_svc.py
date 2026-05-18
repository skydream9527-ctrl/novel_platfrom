"""Public task share/review (D14 / D122)."""
from __future__ import annotations

from datetime import datetime, timezone

from ..core.errors import APIError, ErrorCode
from ..core.storage import get_index_db, get_paths, read_json, write_json
from . import sysconfig_svc


def _now() -> str:
    return datetime.now(tz=timezone.utc).isoformat()


async def share_task(*, task_id: str, owner_id: str) -> dict:
    """Mark a task as visibility=public.

    publish_status follows enable_public_task_review toggle:
    - true  → 'pending' (admin must approve)
    - false → 'published' (auto)
    """
    paths = get_paths()
    meta = read_json(paths.task_meta(task_id))
    if not meta:
        raise APIError(404, ErrorCode.RESOURCE_NOT_FOUND, "任务不存在")
    if meta["owner_id"] != owner_id:
        raise APIError(403, ErrorCode.PERMISSION_DENIED, "仅创建者可共享任务")
    review_required = sysconfig_svc.get_toggles().get("enable_public_task_review", False)
    meta["visibility"] = "public"
    meta["publish_status"] = "pending" if review_required else "published"
    meta["shared_at"] = _now()
    meta["updated_at"] = _now()
    # Freeze snapshot (spec 4.3)
    from . import agent_snapshot_svc
    agent_id = meta.get("agent_id")
    if agent_id:
        # Re-copy cards.md from source at freeze moment
        src_cards = paths.agent_prompt_cards_md(agent_id)
        if src_cards.exists():
            paths.task_agent_cards_md(task_id).write_text(src_cards.read_text())
        new_version = agent_snapshot_svc.compute_agent_version(agent_id)
    else:
        new_version = None
    snap = read_json(paths.task_snapshot(task_id)) or {}
    snap.update({
        "mode": "frozen",
        "agent_source_version": new_version,
        "frozen_at": _now(),
        "frozen_by": owner_id,
    })
    write_json(paths.task_snapshot(task_id), snap)
    write_json(paths.task_meta(task_id), meta)
    db = get_index_db()
    await db.upsert(
        "tasks_index",
        {
            "id": task_id,
            "owner_id": meta["owner_id"],
            "name": meta.get("name"),
            "paradigm": meta.get("paradigm"),
            "agent_id": meta.get("agent_id"),
            "status": meta.get("status", "active"),
            "visibility": "public",
            "publish_status": meta["publish_status"],
            "file_count": meta.get("file_count", 0),
            "last_message_preview": meta.get("last_message_preview"),
            "updated_at": meta["updated_at"],
            "created_at": meta.get("created_at"),
        },
    )
    return meta


async def unshare_task(*, task_id: str, owner_id: str) -> dict:
    paths = get_paths()
    meta = read_json(paths.task_meta(task_id))
    if not meta:
        raise APIError(404, ErrorCode.RESOURCE_NOT_FOUND, "任务不存在")
    if meta["owner_id"] != owner_id:
        raise APIError(403, ErrorCode.PERMISSION_DENIED, "仅创建者可撤回")
    meta["visibility"] = "private"
    meta["publish_status"] = "draft"
    meta["updated_at"] = _now()
    write_json(paths.task_meta(task_id), meta)
    # Thaw snapshot (spec 4.3)
    snap = read_json(paths.task_snapshot(task_id)) or {}
    if snap.get("mode") == "frozen":
        snap["mode"] = "live"
        snap["frozen_at"] = None
        snap["frozen_by"] = None
        write_json(paths.task_snapshot(task_id), snap)

    # Reject all pending join requests
    jr_path = paths.task_join_requests(task_id)
    requests = read_json(jr_path, default=[]) or []
    changed = False
    for r in requests:
        if r.get("status") == "pending":
            r["status"] = "rejected"
            r["reviewed_at"] = _now()
            r["reviewed_by"] = owner_id
            r["reject_reason"] = "task_unshared"
            changed = True
    if changed:
        write_json(jr_path, requests)
    db = get_index_db()
    await db.execute(
        "UPDATE tasks_index SET visibility = 'private', publish_status = 'draft', updated_at = ? WHERE id = ?",
        [meta["updated_at"], task_id],
    )
    return meta


async def list_public(
    *, status: str | None = None, limit: int = 100
) -> list[dict]:
    db = get_index_db()
    if status:
        rows = await db.fetchall(
            "SELECT * FROM tasks_index WHERE visibility = 'public' AND publish_status = ? ORDER BY updated_at DESC LIMIT ?",
            [status, limit],
        )
    else:
        rows = await db.fetchall(
            "SELECT * FROM tasks_index WHERE visibility = 'public' AND publish_status IN ('published','pending') ORDER BY updated_at DESC LIMIT ?",
            [limit],
        )
    paths = get_paths()
    out: list[dict] = []
    for r in rows:
        meta = read_json(paths.task_meta(r["id"]))
        if meta:
            out.append(meta)
    return out


async def admin_review(
    *, task_id: str, decision: str, reason: str | None, operator_id: str
) -> dict:
    if decision not in {"approve", "reject", "delist"}:
        raise APIError(400, ErrorCode.VALIDATION_ERROR, "decision 非法")
    paths = get_paths()
    meta = read_json(paths.task_meta(task_id))
    if not meta:
        raise APIError(404, ErrorCode.RESOURCE_NOT_FOUND, "任务不存在")
    if decision == "approve":
        meta["publish_status"] = "published"
        meta["review_reason"] = None
    elif decision == "reject":
        meta["publish_status"] = "rejected"
        meta["review_reason"] = reason
    elif decision == "delist":
        meta["publish_status"] = "draft"
        meta["visibility"] = "private"
        meta["review_reason"] = reason
    meta["reviewed_by"] = operator_id
    meta["reviewed_at"] = _now()
    meta["updated_at"] = _now()
    write_json(paths.task_meta(task_id), meta)
    db = get_index_db()
    await db.execute(
        "UPDATE tasks_index SET visibility = ?, publish_status = ?, updated_at = ? WHERE id = ?",
        [meta["visibility"], meta["publish_status"], meta["updated_at"], task_id],
    )
    return meta
