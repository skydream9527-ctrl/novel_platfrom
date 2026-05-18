"""Seed runner. Idempotent — safe to call on every startup."""
from __future__ import annotations

import asyncio
import uuid
from datetime import datetime, timezone

from ..core.config import get_settings
from ..core.security import hash_password
from ..core.storage import file_transaction, get_index_db, get_paths, read_json
from ..core.storage.paths import ensure_layout
from ..services import agents_svc


def _now() -> str:
    return datetime.now(tz=timezone.utc).isoformat()


def _new_id() -> str:
    return uuid.uuid4().hex


async def bootstrap() -> None:
    ensure_layout()
    db = get_index_db()
    await db.init()
    agents_svc._ensure_seed_agents()
    await _ensure_admin()
    await _ensure_test_users()
    await _reindex_users_and_agents()


async def _ensure_admin() -> None:
    s = get_settings()
    paths = get_paths()
    db = get_index_db()
    row = await db.fetchone(
        "SELECT id FROM users_index WHERE auth_role = 'super_admin' LIMIT 1"
    )
    if row:
        return
    uid = _new_id()
    profile = {
        "id": uid,
        "email": s.ICE_BOOTSTRAP_ADMIN_EMAIL,
        "name": s.ICE_BOOTSTRAP_ADMIN_NAME,
        "auth_role": "super_admin",
        "status": "active",
        "password_hash": hash_password(s.ICE_BOOTSTRAP_ADMIN_PASSWORD),
        "feishu_user_id": None,
        "feishu_bound_at": None,
        "team": "platform",
        "title": "管理员",
        "avatar_url": None,
        "created_at": _now(),
        "last_login_at": None,
    }
    p = paths.user_profile(uid)
    with file_transaction([p, paths.user_tasks_index(uid)]) as tx:
        tx.makedirs(
            [
                paths.user_dir(uid) / "tasks",
                paths.user_dir(uid) / "notifications",
                paths.user_dir(uid) / "audit",
            ]
        )
        tx.write_json(p, profile)
        tx.write_json(paths.user_tasks_index(uid), [])
        tx.write_json(paths.user_settings(uid), {"theme": "dark"})
    await db.upsert(
        "users_index",
        {
            "id": uid,
            "email": profile["email"],
            "name": profile["name"],
            "auth_role": "super_admin",
            "status": "active",
            "feishu_user_id": None,
            "last_login_at": None,
            "password_hash": profile["password_hash"],
            "created_at": profile["created_at"],
        },
    )


async def _ensure_test_users() -> None:
    paths = get_paths()
    db = get_index_db()
    test_users = [
        {"email": "zhangmingyuan", "name": "张明远", "team": "growth", "title": "产品经理"},
        {"email": "lisihan", "name": "李思涵", "team": "biz", "title": "数据分析师"},
    ]
    for u in test_users:
        row = await db.fetchone("SELECT id FROM users_index WHERE email = ?", [u["email"]])
        if row:
            continue
        uid = _new_id()
        profile = {
            "id": uid,
            "email": u["email"],
            "name": u["name"],
            "auth_role": "user",
            "status": "active",
            "password_hash": hash_password("test123"),
            "feishu_user_id": None,
            "team": u["team"],
            "title": u["title"],
            "created_at": _now(),
            "last_login_at": None,
        }
        with file_transaction([paths.user_profile(uid), paths.user_tasks_index(uid)]) as tx:
            tx.makedirs(
                [
                    paths.user_dir(uid) / "tasks",
                    paths.user_dir(uid) / "notifications",
                    paths.user_dir(uid) / "audit",
                ]
            )
            tx.write_json(paths.user_profile(uid), profile)
            tx.write_json(paths.user_tasks_index(uid), [])
            tx.write_json(paths.user_settings(uid), {"theme": "dark"})
        await db.upsert(
            "users_index",
            {
                "id": uid,
                "email": profile["email"],
                "name": profile["name"],
                "auth_role": "user",
                "status": "active",
                "feishu_user_id": None,
                "last_login_at": None,
                "password_hash": profile["password_hash"],
                "created_at": profile["created_at"],
            },
        )


async def _reindex_users_and_agents() -> None:
    """Sweep users/ and agents/ trees back into cache index (idempotent)."""
    paths = get_paths()
    db = get_index_db()
    if paths.users.exists():
        for d in paths.users.iterdir():
            if not d.is_dir():
                continue
            profile = read_json(d / "profile.json")
            if not profile:
                continue
            await db.upsert(
                "users_index",
                {
                    "id": profile["id"],
                    "email": profile.get("email", ""),
                    "name": profile.get("name", ""),
                    "auth_role": profile.get("auth_role", "user"),
                    "status": profile.get("status", "active"),
                    "feishu_user_id": profile.get("feishu_user_id"),
                    "last_login_at": profile.get("last_login_at"),
                    "password_hash": profile.get("password_hash"),
                    "created_at": profile.get("created_at"),
                },
            )
            tasks_idx = d / "tasks" / "index.json"
            for entry in read_json(tasks_idx, default=[]) or []:
                tid = entry.get("task_id")
                if not tid:
                    continue
                meta = read_json(paths.task_meta(tid))
                if not meta:
                    continue
                await db.upsert(
                    "tasks_index",
                    {
                        "id": meta["id"],
                        "owner_id": meta["owner_id"],
                        "name": meta.get("name", ""),
                        "paradigm": meta.get("paradigm", ""),
                        "agent_id": meta.get("agent_id"),
                        "status": meta.get("status", "active"),
                        "visibility": meta.get("visibility", "private"),
                        "publish_status": meta.get("publish_status", "draft"),
                        "file_count": int(meta.get("file_count", 0)),
                        "last_message_preview": meta.get("last_message_preview"),
                        "updated_at": meta.get("updated_at"),
                        "created_at": meta.get("created_at"),
                    },
                )
    for a in agents_svc.list_agents():
        await db.upsert(
            "agents_index",
            {
                "id": a["id"],
                "name": a.get("name"),
                "paradigm": a.get("paradigm"),
                "icon": a.get("icon"),
                "color": a.get("color"),
                "publish_status": a.get("publish_status", "published"),
                "description": a.get("description"),
                "updated_at": _now(),
            },
        )


def main() -> None:
    asyncio.run(bootstrap())
    print("seed: ok")


if __name__ == "__main__":
    main()
