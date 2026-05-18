"""Multi-conversation per task (spec 3.5, 4.6)."""
from __future__ import annotations

import fcntl
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

from ..core.errors import APIError, ErrorCode
from ..core.storage import file_transaction, get_paths, read_json, write_json


def _now() -> str:
    return datetime.now(tz=timezone.utc).isoformat()


def _new_id() -> str:
    return uuid.uuid4().hex


async def list_conversations(*, task_id: str) -> list[dict]:
    paths = get_paths()
    return read_json(paths.task_conversations_index(task_id), default=[]) or []


async def create_conversation(*, task_id: str, created_by: str, title: str | None = None) -> dict:
    paths = get_paths()
    cid = _new_id()
    now = _now()
    entry = {
        "id": cid,
        "title": title or "新对话",
        "created_by": created_by,
        "created_at": now,
        "last_message_at": now,
        "message_count": 0,
    }
    idx_path = paths.task_conversations_index(task_id)
    with file_transaction([idx_path]) as tx:
        idx = tx.read_json(idx_path, default=[])
        idx.append(entry)
        tx.write_json(idx_path, idx)
    # Ensure conversation jsonl parent exists
    paths.task_conversation(task_id, cid).parent.mkdir(parents=True, exist_ok=True)
    return entry


async def rename_conversation(*, task_id: str, conv_id: str, title: str) -> dict:
    paths = get_paths()
    idx_path = paths.task_conversations_index(task_id)
    with file_transaction([idx_path]) as tx:
        idx = tx.read_json(idx_path, default=[])
        for item in idx:
            if item["id"] == conv_id:
                item["title"] = title
                tx.write_json(idx_path, idx)
                return item
    raise APIError(404, ErrorCode.RESOURCE_NOT_FOUND, "对话不存在")


async def delete_conversation(*, task_id: str, conv_id: str) -> None:
    paths = get_paths()
    idx_path = paths.task_conversations_index(task_id)
    with file_transaction([idx_path]) as tx:
        idx = tx.read_json(idx_path, default=[])
        idx = [c for c in idx if c["id"] != conv_id]
        tx.write_json(idx_path, idx)
    jsonl = paths.task_conversation(task_id, conv_id)
    if jsonl.exists():
        jsonl.unlink()
    lock = paths.task_conversation_lock(task_id, conv_id)
    if lock.exists():
        lock.unlink()


async def get_or_create_default(*, task_id: str, created_by: str) -> dict:
    items = await list_conversations(task_id=task_id)
    if items:
        items.sort(key=lambda c: c.get("last_message_at") or "", reverse=True)
        return items[0]
    return await create_conversation(task_id=task_id, created_by=created_by, title="默认对话")


async def touch_last_message(*, task_id: str, conv_id: str) -> None:
    """Bump last_message_at + message_count. Call after each successful message write."""
    paths = get_paths()
    idx_path = paths.task_conversations_index(task_id)
    with file_transaction([idx_path]) as tx:
        idx = tx.read_json(idx_path, default=[])
        for item in idx:
            if item["id"] == conv_id:
                item["last_message_at"] = _now()
                item["message_count"] = int(item.get("message_count", 0)) + 1
                tx.write_json(idx_path, idx)
                return


@contextmanager
def acquire_inflight_lock(*, task_id: str, conv_id: str):
    """Per-cid fcntl lock, non-blocking. Raises CONVERSATION_INFLIGHT on conflict.

    Usage:
        with acquire_inflight_lock(task_id=tid, conv_id=cid):
            # call LLM, append message to jsonl
            ...
    """
    paths = get_paths()
    lock_path = paths.task_conversation_lock(task_id, conv_id)
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    f = open(lock_path, "w")
    try:
        try:
            fcntl.flock(f.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            f.close()
            raise APIError(
                409,
                ErrorCode.CONVERSATION_INFLIGHT,
                "该对话正在处理中，请稍候",
            )
        try:
            yield
        finally:
            fcntl.flock(f.fileno(), fcntl.LOCK_UN)
    finally:
        f.close()
