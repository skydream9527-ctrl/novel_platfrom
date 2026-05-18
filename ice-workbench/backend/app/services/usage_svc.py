"""LLM usage tracking. Append-only JSONL + cache index for aggregations."""
from __future__ import annotations

import csv
import io
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

from ..core.storage import append_jsonl, get_index_db, get_paths, read_jsonl
from . import sysconfig_svc

USAGE_TABLE_DDL = """
CREATE TABLE IF NOT EXISTS llm_usage (
    id              TEXT PRIMARY KEY,
    user_id         TEXT,
    agent_id        TEXT,
    task_id         TEXT,
    conversation_id TEXT,
    model           TEXT,
    input_tokens    INTEGER NOT NULL DEFAULT 0,
    output_tokens   INTEGER NOT NULL DEFAULT 0,
    cost_usd        REAL    NOT NULL DEFAULT 0,
    success         INTEGER NOT NULL DEFAULT 1,
    created_at      TEXT NOT NULL,
    day             TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_usage_day ON llm_usage(day);
CREATE INDEX IF NOT EXISTS ix_usage_user ON llm_usage(user_id);
CREATE INDEX IF NOT EXISTS ix_usage_agent ON llm_usage(agent_id);
CREATE INDEX IF NOT EXISTS ix_usage_task ON llm_usage(task_id);
"""


async def _ensure_table() -> None:
    db = get_index_db()
    await db.executescript(USAGE_TABLE_DDL)


def _now() -> datetime:
    return datetime.now(tz=timezone.utc)


def _iso(d: datetime) -> str:
    return d.isoformat()


def _day(d: datetime) -> str:
    return d.strftime("%Y-%m-%d")


def _month(d: datetime) -> str:
    return d.strftime("%Y-%m")


def _usage_log_path(month: str) -> Path:
    return get_paths().cache / "usage" / f"{month}.jsonl"


def calc_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    in_per_m, out_per_m = sysconfig_svc.get_model_pricing(model)
    return (input_tokens * in_per_m + output_tokens * out_per_m) / 1_000_000.0


async def record_usage(
    *,
    user_id: str | None,
    agent_id: str | None,
    task_id: str | None,
    conversation_id: str | None,
    model: str,
    input_tokens: int,
    output_tokens: int,
    success: bool = True,
) -> dict:
    await _ensure_table()
    now = _now()
    cost = calc_cost(model, input_tokens, output_tokens)
    rec = {
        "id": uuid.uuid4().hex,
        "user_id": user_id,
        "agent_id": agent_id,
        "task_id": task_id,
        "conversation_id": conversation_id,
        "model": model,
        "input_tokens": int(input_tokens or 0),
        "output_tokens": int(output_tokens or 0),
        "cost_usd": round(cost, 6),
        "success": 1 if success else 0,
        "created_at": _iso(now),
        "day": _day(now),
    }
    db = get_index_db()
    await db.execute(
        """INSERT INTO llm_usage
        (id,user_id,agent_id,task_id,conversation_id,model,input_tokens,output_tokens,cost_usd,success,created_at,day)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
        [
            rec["id"],
            rec["user_id"],
            rec["agent_id"],
            rec["task_id"],
            rec["conversation_id"],
            rec["model"],
            rec["input_tokens"],
            rec["output_tokens"],
            rec["cost_usd"],
            rec["success"],
            rec["created_at"],
            rec["day"],
        ],
    )
    append_jsonl(_usage_log_path(_month(now)), rec)
    return rec


async def daily_trend(*, days: int = 30) -> list[dict]:
    await _ensure_table()
    db = get_index_db()
    cutoff = _day(_now() - timedelta(days=days - 1))
    rows = await db.fetchall(
        """SELECT day,
                  SUM(input_tokens) AS input_tokens,
                  SUM(output_tokens) AS output_tokens,
                  SUM(cost_usd) AS cost_usd,
                  COUNT(*) AS calls
           FROM llm_usage
           WHERE day >= ?
           GROUP BY day
           ORDER BY day ASC""",
        [cutoff],
    )
    # densify missing days
    by_day = {r["day"]: r for r in rows}
    out: list[dict] = []
    base = _now() - timedelta(days=days - 1)
    for i in range(days):
        d = _day(base + timedelta(days=i))
        r = by_day.get(d) or {}
        out.append(
            {
                "day": d,
                "input_tokens": int(r.get("input_tokens") or 0),
                "output_tokens": int(r.get("output_tokens") or 0),
                "cost_usd": float(r.get("cost_usd") or 0.0),
                "calls": int(r.get("calls") or 0),
            }
        )
    return out


async def by_dimension(*, dimension: str, days: int = 30, limit: int = 20) -> list[dict]:
    """dimension in {model, user_id, agent_id, task_id}."""
    await _ensure_table()
    if dimension not in {"model", "user_id", "agent_id", "task_id"}:
        return []
    db = get_index_db()
    cutoff = _day(_now() - timedelta(days=days - 1))
    rows = await db.fetchall(
        f"""SELECT {dimension} AS key,
               SUM(input_tokens) AS input_tokens,
               SUM(output_tokens) AS output_tokens,
               SUM(cost_usd) AS cost_usd,
               COUNT(*) AS calls
        FROM llm_usage
        WHERE day >= ? AND {dimension} IS NOT NULL
        GROUP BY {dimension}
        ORDER BY cost_usd DESC
        LIMIT ?""",
        [cutoff, limit],
    )
    return [
        {
            "key": r["key"],
            "input_tokens": int(r["input_tokens"] or 0),
            "output_tokens": int(r["output_tokens"] or 0),
            "cost_usd": float(r["cost_usd"] or 0.0),
            "calls": int(r["calls"] or 0),
        }
        for r in rows
    ]


async def month_summary() -> dict:
    await _ensure_table()
    db = get_index_db()
    month = _month(_now())
    row = await db.fetchone(
        """SELECT SUM(input_tokens) AS input_tokens,
                  SUM(output_tokens) AS output_tokens,
                  SUM(cost_usd) AS cost_usd,
                  COUNT(*) AS calls
           FROM llm_usage
           WHERE day LIKE ?""",
        [f"{month}-%"],
    )
    cost = float((row or {}).get("cost_usd") or 0.0)
    cfg = sysconfig_svc.get_llm_config()
    budget = float(cfg["budget_monthly_usd"] or 0.0)
    threshold = float(cfg["budget_alert_threshold"])
    ratio = (cost / budget) if budget > 0 else 0.0
    state = "ok"
    if budget > 0:
        if ratio >= 1.0:
            state = "exceeded"
        elif ratio >= threshold:
            state = "warning"
    return {
        "month": month,
        "input_tokens": int((row or {}).get("input_tokens") or 0),
        "output_tokens": int((row or {}).get("output_tokens") or 0),
        "cost_usd": round(cost, 4),
        "calls": int((row or {}).get("calls") or 0),
        "budget_usd": budget,
        "budget_threshold": threshold,
        "budget_used_ratio": round(ratio, 4),
        "budget_state": state,
    }


async def export_csv(*, days: int = 30) -> str:
    await _ensure_table()
    db = get_index_db()
    cutoff = _day(_now() - timedelta(days=days - 1))
    rows = await db.fetchall(
        """SELECT created_at, user_id, agent_id, task_id, model,
                  input_tokens, output_tokens, cost_usd, success
           FROM llm_usage WHERE day >= ? ORDER BY created_at DESC""",
        [cutoff],
    )
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(
        ["created_at", "user_id", "agent_id", "task_id", "model", "input_tokens", "output_tokens", "cost_usd", "success"]
    )
    for r in rows:
        w.writerow(
            [
                r["created_at"],
                r["user_id"] or "",
                r["agent_id"] or "",
                r["task_id"] or "",
                r["model"] or "",
                r["input_tokens"],
                r["output_tokens"],
                f"{r['cost_usd']:.6f}",
                r["success"],
            ]
        )
    return buf.getvalue()


def reload_from_files() -> int:
    """Rebuild the cache table from monthly JSONL files. Returns row count."""
    from ..core.storage import get_index_db as _db

    paths = get_paths()
    base = paths.cache / "usage"
    if not base.exists():
        return 0
    rows: list[dict] = []
    for f in sorted(base.glob("*.jsonl")):
        rows.extend(read_jsonl(f))
    return len(rows)
