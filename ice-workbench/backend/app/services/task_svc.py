"""Task service. Implements G3 file-first dual-write."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from ..core.errors import APIError, ErrorCode
from ..core.storage import file_transaction, get_index_db, get_paths, read_json, write_json
from . import agent_snapshot_svc


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _new_id() -> str:
    return uuid.uuid4().hex


async def create_task(
    *,
    name: str,
    paradigm: str,
    owner_id: str,
    agent_id: str | None = None,
    description: str | None = None,
    initial_prompt: str | None = None,
    skill_ids: list[str] | None = None,
    visibility: str = "private",
) -> dict:
    paths = get_paths()
    db = get_index_db()
    tid = _new_id()
    cid = _new_id()
    meta = {
        "id": tid,
        "name": name,
        "paradigm": paradigm,
        "agent_id": agent_id,
        "owner_id": owner_id,
        "description": description,
        "initial_prompt": initial_prompt,
        "skill_ids": skill_ids or [],
        "visibility": visibility,
        "publish_status": "draft",
        "status": "active",
        "file_count": 0,
        "created_at": _now(),
        "updated_at": _now(),
    }
    from . import llm_gateway

    workspace = {
        "current_conversation_id": cid,
        "model": llm_gateway.resolve_model(None),
        "context_size": 20,
    }
    paths_to_lock = [paths.task_meta(tid), paths.user_tasks_index(owner_id)]
    with file_transaction(paths_to_lock) as tx:
        tx.makedirs(
            [
                paths.task_dir(tid) / "conversations",
                paths.task_dir(tid) / "tool_calls",
                paths.task_files_input(tid),
                paths.task_files_output(tid),
                paths.task_files_uploaded(tid),
                paths.task_files_meta(tid),
            ]
        )
        tx.write_json(paths.task_meta(tid), meta)
        tx.write_json(paths.task_workspace(tid), workspace)
        tx.write_json(
            paths.task_collaborators(tid),
            [{"user_id": owner_id, "role": "owner", "joined_at": _now(), "status": "active"}],
        )
        tx.write_json(paths.task_experience_cards(tid), [])

        # C3 snapshot (Task 5): agent + skills + snapshot.json
        tx.makedirs([
            paths.task_agent_prompt_dir(tid),
            paths.task_skills_dir(tid),
            paths.task_files_imported(tid),
            paths.task_files_imported(tid) / ".meta",
        ])
        # Agent files are plain shutil copies (not transactional) because they
        # live outside the tx's managed paths; the tx still holds the meta lock.
        agent_snapshot_svc.snapshot_agent_into_task(task_id=tid, agent_id=agent_id)
        agent_snapshot_svc.snapshot_skills_into_task(task_id=tid, skill_ids=skill_ids or [])
        snap = {
            "mode": "live",
            "agent_source_version": agent_snapshot_svc.compute_agent_version(agent_id) if agent_id else None,
            "frozen_at": None,
            "frozen_by": None,
            "last_manual_update_at": None,
            "last_manual_update_by": None,
        }
        tx.write_json(paths.task_snapshot(tid), snap)

        user_index = tx.read_json(paths.user_tasks_index(owner_id), default=[])
        user_index.append(
            {"task_id": tid, "name": name, "paradigm": paradigm, "role": "owner", "added_at": _now()}
        )
        tx.write_json(paths.user_tasks_index(owner_id), user_index)

    # cache index update happens after fs commit
    await db.upsert(
        "tasks_index",
        {
            "id": tid,
            "owner_id": owner_id,
            "name": name,
            "paradigm": paradigm,
            "agent_id": agent_id,
            "status": "active",
            "visibility": visibility,
            "publish_status": "draft",
            "file_count": 0,
            "last_message_preview": None,
            "updated_at": meta["updated_at"],
            "created_at": meta["created_at"],
        },
    )
    await db.upsert(
        "conversations_index",
        {
            "id": cid,
            "task_id": tid,
            "title": "default",
            "created_at": meta["created_at"],
            "updated_at": meta["updated_at"],
        },
    )
    return meta


async def list_user_tasks(user_id: str, *, limit: int = 30) -> list[dict]:
    db = get_index_db()
    rows = await db.fetchall(
        "SELECT * FROM tasks_index WHERE owner_id = ? ORDER BY updated_at DESC LIMIT ?",
        [user_id, limit],
    )
    seen = {r["id"] for r in rows}
    out: list[dict] = []
    for r in rows:
        meta = read_json(get_paths().task_meta(r["id"]))
        if meta:
            meta["role"] = "owner"
            out.append(meta)

    paths = get_paths()
    user_index = read_json(paths.user_tasks_index(user_id), default=[]) or []
    for entry in user_index:
        tid = entry.get("task_id")
        if not tid or tid in seen:
            continue
        meta = read_json(paths.task_meta(tid))
        if meta and meta.get("owner_id") != user_id:
            meta["role"] = "collaborator"
            out.append(meta)
            seen.add(tid)
    out.sort(key=lambda m: m.get("updated_at") or "", reverse=True)
    return out[:limit]


async def list_public_tasks(limit: int = 50) -> list[dict]:
    db = get_index_db()
    rows = await db.fetchall(
        "SELECT * FROM tasks_index WHERE visibility = 'public' AND publish_status = 'published' ORDER BY updated_at DESC LIMIT ?",
        [limit],
    )
    out = []
    for r in rows:
        meta = read_json(get_paths().task_meta(r["id"]))
        if meta:
            out.append(meta)
    return out


async def get_task(task_id: str, user_id: str) -> dict:
    paths = get_paths()
    meta = read_json(paths.task_meta(task_id))
    if not meta:
        raise APIError(404, ErrorCode.RESOURCE_NOT_FOUND, "任务不存在")
    collaborators = read_json(paths.task_collaborators(task_id), default=[])
    if meta.get("owner_id") != user_id and meta.get("visibility") != "public":
        if not any(c["user_id"] == user_id and c.get("status") == "active" for c in collaborators):
            raise APIError(403, ErrorCode.PERMISSION_DENIED, "无权访问此任务")
    workspace = read_json(paths.task_workspace(task_id), default={})
    from . import agent_snapshot_svc
    snap = read_json(paths.task_snapshot(task_id)) or {
        "mode": "live",
        "agent_source_version": None,
        "frozen_at": None,
        "frozen_by": None,
        "last_manual_update_at": None,
        "last_manual_update_by": None,
    }
    agent_update_available = False
    if meta.get("visibility") == "public":
        aid = meta.get("agent_id")
        if aid:
            current_version = agent_snapshot_svc.compute_agent_version(aid)
            if current_version and current_version != snap.get("agent_source_version"):
                agent_update_available = True

    return {
        **meta,
        "workspace": workspace,
        "collaborators": collaborators,
        "snapshot": snap,
        "agent_update_available": agent_update_available,
    }


async def delete_task(task_id: str, user_id: str) -> None:
    """Hard-delete a task: filesystem dir + index rows + user index entry.

    Only the owner can delete. Files / conversations / tool_calls / experience
    cards under the task are wiped from disk; index tables are scrubbed.
    """
    import shutil

    paths = get_paths()
    meta = read_json(paths.task_meta(task_id))
    if not meta:
        raise APIError(404, ErrorCode.RESOURCE_NOT_FOUND, "任务不存在")
    if meta.get("owner_id") != user_id:
        raise APIError(403, ErrorCode.PERMISSION_DENIED, "仅创建者可删除任务")

    owner_id = meta["owner_id"]
    user_index_path = paths.user_tasks_index(owner_id)
    paths_to_lock = [paths.task_meta(task_id), user_index_path]
    with file_transaction(paths_to_lock) as tx:
        items = tx.read_json(user_index_path, default=[]) or []
        items = [it for it in items if it.get("task_id") != task_id]
        tx.write_json(user_index_path, items)

    task_dir = paths.task_dir(task_id)
    if task_dir.exists():
        shutil.rmtree(task_dir, ignore_errors=True)

    db = get_index_db()
    for table, col in (
        ("tasks_index", "id"),
        ("files_index", "task_id"),
        ("messages_index", "task_id"),
        ("conversations_index", "task_id"),
        ("sql_audit", "task_id"),
        ("llm_usage", "task_id"),
    ):
        try:
            await db.execute(f"DELETE FROM {table} WHERE {col} = ?", [task_id])
        except Exception:
            pass


async def touch_task(task_id: str, *, last_message_preview: str | None = None) -> None:
    paths = get_paths()
    meta = read_json(paths.task_meta(task_id))
    if not meta:
        return
    meta["updated_at"] = _now()
    if last_message_preview is not None:
        meta["last_message_preview"] = last_message_preview[:120]
    write_json(paths.task_meta(task_id), meta)
    db = get_index_db()
    await db.execute(
        "UPDATE tasks_index SET updated_at = ?, last_message_preview = COALESCE(?, last_message_preview) WHERE id = ?",
        [meta["updated_at"], meta.get("last_message_preview"), task_id],
    )


async def get_or_create_default_conversation(task_id: str) -> str:
    paths = get_paths()
    workspace = read_json(paths.task_workspace(task_id), default={})
    cid = workspace.get("current_conversation_id")
    if cid:
        return cid
    cid = _new_id()
    workspace["current_conversation_id"] = cid
    write_json(paths.task_workspace(task_id), workspace)
    db = get_index_db()
    await db.upsert(
        "conversations_index",
        {"id": cid, "task_id": task_id, "title": "default", "created_at": _now(), "updated_at": _now()},
    )
    return cid


def load_conversation_messages(task_id: str, conv_id: str) -> list[dict]:
    from ..core.storage import read_jsonl

    return read_jsonl(get_paths().task_conversation(task_id, conv_id))
