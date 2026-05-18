"""SQL audit. 三级 classify (allow/warn/block) + 持久化 + CSV 导出 (D127)."""
from __future__ import annotations

import csv
import io
import uuid
from datetime import datetime, timedelta, timezone

from ..core.storage import append_jsonl, get_index_db, get_paths

SQL_AUDIT_DDL = """
CREATE TABLE IF NOT EXISTS sql_audit (
    id              TEXT PRIMARY KEY,
    user_id         TEXT,
    agent_id        TEXT,
    task_id         TEXT,
    conversation_id TEXT,
    sql             TEXT,
    decision        TEXT NOT NULL,
    block_reason    TEXT,
    error_message   TEXT,
    rows_returned   INTEGER,
    duration_ms     INTEGER,
    created_at      TEXT NOT NULL,
    day             TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_sqlaudit_day ON sql_audit(day);
CREATE INDEX IF NOT EXISTS ix_sqlaudit_user ON sql_audit(user_id);
CREATE INDEX IF NOT EXISTS ix_sqlaudit_decision ON sql_audit(decision);
"""


async def _ensure_table() -> None:
    await get_index_db().executescript(SQL_AUDIT_DDL)


def _now() -> datetime:
    return datetime.now(tz=timezone.utc)


def _iso(d: datetime) -> str:
    return d.isoformat()


def _day(d: datetime) -> str:
    return d.strftime("%Y-%m-%d")


def classify(sql: str) -> tuple[str, str | None]:
    """Return (decision, reason). decision in {allow, warn, block}."""
    s = (sql or "").strip().upper()
    if not s:
        return "block", "Empty SQL"
    first = s.split()[0] if s else ""
    if first in {"DROP", "TRUNCATE", "DELETE"}:
        if "WHERE" not in s:
            return "block", f"{first} without WHERE"
        return "warn", f"{first} statement"
    if first in {"INSERT", "UPDATE", "CREATE", "ALTER", "GRANT", "REVOKE"}:
        return "block", f"DML/DDL not allowed: {first}"
    if first == "SELECT":
        if "WHERE" not in s and "LIMIT" not in s:
            return "warn", "SELECT without WHERE/LIMIT"
        return "allow", None
    return "block", f"Unknown SQL type: {first[:32]}"


async def record(
    *,
    user_id: str | None,
    agent_id: str | None,
    task_id: str | None,
    conversation_id: str | None,
    sql: str,
    decision: str,
    block_reason: str | None = None,
    error_message: str | None = None,
    rows_returned: int | None = None,
    duration_ms: int | None = None,
) -> dict:
    await _ensure_table()
    rec = {
        "id": uuid.uuid4().hex,
        "user_id": user_id,
        "agent_id": agent_id,
        "task_id": task_id,
        "conversation_id": conversation_id,
        "sql": sql,
        "decision": decision,
        "block_reason": block_reason,
        "error_message": error_message,
        "rows_returned": rows_returned,
        "duration_ms": duration_ms,
        "created_at": _iso(_now()),
        "day": _day(_now()),
    }
    await get_index_db().execute(
        """INSERT INTO sql_audit
        (id,user_id,agent_id,task_id,conversation_id,sql,decision,block_reason,
         error_message,rows_returned,duration_ms,created_at,day)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        [
            rec["id"],
            rec["user_id"],
            rec["agent_id"],
            rec["task_id"],
            rec["conversation_id"],
            rec["sql"],
            rec["decision"],
            rec["block_reason"],
            rec["error_message"],
            rec["rows_returned"],
            rec["duration_ms"],
            rec["created_at"],
            rec["day"],
        ],
    )
    append_jsonl(get_paths().cache / "sql_audit" / f"{rec['day'][:7]}.jsonl", rec)
    return rec


async def list_logs(
    *,
    decision: str | None = None,
    user_id: str | None = None,
    agent_id: str | None = None,
    task_id: str | None = None,
    q: str | None = None,
    days: int = 30,
    limit: int = 200,
) -> list[dict]:
    await _ensure_table()
    cutoff = _day(_now() - timedelta(days=days - 1))
    where = ["day >= ?"]
    params: list = [cutoff]
    if decision:
        where.append("decision = ?")
        params.append(decision)
    if user_id:
        where.append("user_id = ?")
        params.append(user_id)
    if agent_id:
        where.append("agent_id = ?")
        params.append(agent_id)
    if task_id:
        where.append("task_id = ?")
        params.append(task_id)
    if q:
        where.append("sql LIKE ?")
        params.append(f"%{q}%")
    sql = "SELECT * FROM sql_audit WHERE " + " AND ".join(where) + " ORDER BY created_at DESC LIMIT ?"
    params.append(limit)
    return await get_index_db().fetchall(sql, params)


async def stats(*, days: int = 30) -> dict:
    await _ensure_table()
    cutoff = _day(_now() - timedelta(days=days - 1))
    db = get_index_db()
    by_decision = await db.fetchall(
        "SELECT decision, COUNT(*) AS c FROM sql_audit WHERE day >= ? GROUP BY decision",
        [cutoff],
    )
    daily = await db.fetchall(
        """SELECT day, decision, COUNT(*) AS c
           FROM sql_audit WHERE day >= ?
           GROUP BY day, decision
           ORDER BY day ASC""",
        [cutoff],
    )
    return {
        "by_decision": {r["decision"]: int(r["c"]) for r in by_decision},
        "daily": daily,
    }


async def export_csv(*, days: int = 30) -> str:
    rows = await list_logs(days=days, limit=10_000)
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(
        ["created_at", "user_id", "agent_id", "task_id", "decision", "block_reason", "duration_ms", "rows_returned", "sql"]
    )
    for r in rows:
        w.writerow(
            [
                r["created_at"],
                r["user_id"] or "",
                r["agent_id"] or "",
                r["task_id"] or "",
                r["decision"],
                r["block_reason"] or "",
                r["duration_ms"] or "",
                r["rows_returned"] or "",
                (r["sql"] or "").replace("\n", " ")[:1000],
            ]
        )
    return buf.getvalue()
