"""Notification service backed by users/{uid}/notifications/{YYYY-MM}.jsonl."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from ..core.storage import append_jsonl, get_index_db, get_paths, read_jsonl


def _now() -> datetime:
    return datetime.now(tz=timezone.utc)


async def add_notification(
    user_id: str, *, kind: str, title: str, body: str = "", action_url: str | None = None
) -> dict:
    nid = uuid.uuid4().hex
    record = {
        "id": nid,
        "user_id": user_id,
        "kind": kind,
        "title": title,
        "body": body,
        "action_url": action_url,
        "is_read": False,
        "created_at": _now().isoformat(),
    }
    paths = get_paths()
    ym = _now().strftime("%Y-%m")
    append_jsonl(paths.user_notifications(user_id, ym), record)
    db = get_index_db()
    await db.upsert("notifications_index", {**record, "is_read": 0})
    return record


async def list_notifications(user_id: str, *, limit: int = 50) -> list[dict]:
    db = get_index_db()
    rows = await db.fetchall(
        "SELECT * FROM notifications_index WHERE user_id = ? ORDER BY created_at DESC LIMIT ?",
        [user_id, limit],
    )
    return [{**r, "is_read": bool(r["is_read"])} for r in rows]


async def mark_read(user_id: str, nid: str) -> None:
    db = get_index_db()
    await db.execute(
        "UPDATE notifications_index SET is_read = 1 WHERE user_id = ? AND id = ?", [user_id, nid]
    )


async def mark_all_read(user_id: str) -> None:
    db = get_index_db()
    await db.execute("UPDATE notifications_index SET is_read = 1 WHERE user_id = ?", [user_id])


async def unread_count(user_id: str) -> int:
    db = get_index_db()
    row = await db.fetchone(
        "SELECT COUNT(*) AS c FROM notifications_index WHERE user_id = ? AND is_read = 0",
        [user_id],
    )
    return int(row["c"]) if row else 0


def reload_from_files(user_id: str) -> list[dict]:
    """Read recent month files and return records (for cache rebuild)."""
    paths = get_paths()
    out: list[dict] = []
    for ym in (_now().strftime("%Y-%m"),):
        out.extend(read_jsonl(paths.user_notifications(user_id, ym)))
    return out
