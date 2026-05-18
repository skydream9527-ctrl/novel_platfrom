"""SQLite cache index. Filesystem is source of truth — this is rebuildable."""
from __future__ import annotations

import asyncio
from functools import lru_cache
from pathlib import Path
from typing import Any, Iterable

import aiosqlite

from ..config import get_settings

SCHEMA = """
CREATE TABLE IF NOT EXISTS users_index (
    id            TEXT PRIMARY KEY,
    email         TEXT UNIQUE,
    name          TEXT,
    auth_role     TEXT NOT NULL DEFAULT 'user',
    status        TEXT NOT NULL DEFAULT 'active',
    feishu_user_id TEXT,
    last_login_at TEXT,
    password_hash TEXT,
    created_at    TEXT
);

CREATE TABLE IF NOT EXISTS tasks_index (
    id            TEXT PRIMARY KEY,
    owner_id      TEXT NOT NULL,
    name          TEXT,
    paradigm      TEXT,
    agent_id      TEXT,
    status        TEXT,
    visibility    TEXT DEFAULT 'private',
    publish_status TEXT DEFAULT 'draft',
    file_count    INTEGER DEFAULT 0,
    last_message_preview TEXT,
    updated_at    TEXT,
    created_at    TEXT
);
CREATE INDEX IF NOT EXISTS ix_tasks_owner ON tasks_index(owner_id);
CREATE INDEX IF NOT EXISTS ix_tasks_paradigm ON tasks_index(paradigm);

CREATE TABLE IF NOT EXISTS messages_index (
    id              TEXT PRIMARY KEY,
    conversation_id TEXT NOT NULL,
    task_id         TEXT NOT NULL,
    role            TEXT NOT NULL,
    created_at      TEXT
);
CREATE INDEX IF NOT EXISTS ix_msgs_conv ON messages_index(conversation_id);
CREATE INDEX IF NOT EXISTS ix_msgs_task ON messages_index(task_id);

CREATE TABLE IF NOT EXISTS files_index (
    id           TEXT PRIMARY KEY,
    task_id      TEXT,
    owner_id     TEXT,
    scope        TEXT NOT NULL,
    name         TEXT,
    path         TEXT,
    file_type    TEXT,
    format       TEXT,
    size_bytes   INTEGER,
    is_pinned    INTEGER DEFAULT 0,
    created_at   TEXT
);
CREATE INDEX IF NOT EXISTS ix_files_task ON files_index(task_id);
CREATE INDEX IF NOT EXISTS ix_files_scope ON files_index(scope);

CREATE TABLE IF NOT EXISTS notifications_index (
    id          TEXT PRIMARY KEY,
    user_id     TEXT NOT NULL,
    kind        TEXT NOT NULL,
    title       TEXT,
    body        TEXT,
    action_url  TEXT,
    is_read     INTEGER DEFAULT 0,
    created_at  TEXT
);
CREATE INDEX IF NOT EXISTS ix_notify_user ON notifications_index(user_id);

CREATE TABLE IF NOT EXISTS agents_index (
    id            TEXT PRIMARY KEY,
    name          TEXT,
    paradigm      TEXT,
    icon          TEXT,
    color         TEXT,
    publish_status TEXT DEFAULT 'published',
    description   TEXT,
    updated_at    TEXT
);

CREATE TABLE IF NOT EXISTS skills_index (
    id            TEXT PRIMARY KEY,
    name          TEXT,
    category      TEXT,
    description   TEXT,
    tool_entry    TEXT,
    tool_schema   TEXT,
    updated_at    TEXT
);

CREATE TABLE IF NOT EXISTS conversations_index (
    id          TEXT PRIMARY KEY,
    task_id     TEXT NOT NULL,
    title       TEXT,
    created_at  TEXT,
    updated_at  TEXT
);
CREATE INDEX IF NOT EXISTS ix_conv_task ON conversations_index(task_id);
"""


class IndexDB:
    def __init__(self, path: Path):
        self.path = path
        self._lock = asyncio.Lock()

    async def init(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        async with aiosqlite.connect(self.path) as db:
            await db.executescript(SCHEMA)
            await db.commit()

    async def execute(self, sql: str, params: Iterable[Any] | None = None) -> None:
        async with self._lock, aiosqlite.connect(self.path) as db:
            await db.execute(sql, tuple(params or ()))
            await db.commit()

    async def executescript(self, script: str) -> None:
        async with self._lock, aiosqlite.connect(self.path) as db:
            await db.executescript(script)
            await db.commit()

    async def executemany(self, sql: str, rows: Iterable[Iterable[Any]]) -> None:
        async with self._lock, aiosqlite.connect(self.path) as db:
            await db.executemany(sql, [tuple(r) for r in rows])
            await db.commit()

    async def fetchone(self, sql: str, params: Iterable[Any] | None = None) -> dict | None:
        async with aiosqlite.connect(self.path) as db:
            db.row_factory = aiosqlite.Row
            cur = await db.execute(sql, tuple(params or ()))
            row = await cur.fetchone()
            return dict(row) if row else None

    async def fetchall(self, sql: str, params: Iterable[Any] | None = None) -> list[dict]:
        async with aiosqlite.connect(self.path) as db:
            db.row_factory = aiosqlite.Row
            cur = await db.execute(sql, tuple(params or ()))
            rows = await cur.fetchall()
            return [dict(r) for r in rows]

    async def upsert(self, table: str, row: dict, key: str = "id") -> None:
        cols = list(row.keys())
        placeholders = ",".join(["?"] * len(cols))
        col_list = ",".join(cols)
        update_set = ",".join(f"{c}=excluded.{c}" for c in cols if c != key)
        sql = f"INSERT INTO {table} ({col_list}) VALUES ({placeholders}) ON CONFLICT({key}) DO UPDATE SET {update_set}"
        await self.execute(sql, [row[c] for c in cols])


@lru_cache
def get_index_db() -> IndexDB:
    return IndexDB(get_settings().cache_db_path)
