"""Admin services: users CRUD, agent prompt history, ranking, audit logs."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from pathlib import Path

from ..core.errors import APIError, ErrorCode
from ..core.security import hash_password
from ..core.storage import (
    append_jsonl,
    file_transaction,
    get_index_db,
    get_paths,
    read_json,
    read_jsonl,
    write_json,
)


def _now() -> str:
    return datetime.now(tz=timezone.utc).isoformat()


def _new_id() -> str:
    return uuid.uuid4().hex


# ---- audit log ----


def _audit_path(admin_id: str) -> Path:
    ym = datetime.now(tz=timezone.utc).strftime("%Y-%m")
    return get_paths().user_dir(admin_id) / "audit" / f"{ym}.jsonl"


async def audit(
    *,
    admin_id: str,
    action: str,
    target_type: str,
    target_id: str,
    diff: dict | None = None,
):
    rec = {
        "id": _new_id(),
        "admin_id": admin_id,
        "action": action,
        "target_type": target_type,
        "target_id": target_id,
        "diff": diff or {},
        "created_at": _now(),
    }
    p = _audit_path(admin_id)
    append_jsonl(p, rec)


async def list_audit_logs(*, admin_id: str | None = None, limit: int = 100) -> list[dict]:
    paths = get_paths()
    out: list[dict] = []
    if admin_id:
        users = [paths.user_dir(admin_id)]
    else:
        users = list(paths.users.iterdir()) if paths.users.exists() else []
    ym = datetime.now(tz=timezone.utc).strftime("%Y-%m")
    for u in users:
        if not u.is_dir():
            continue
        out.extend(read_jsonl(u / "audit" / f"{ym}.jsonl"))
    out.sort(key=lambda x: x.get("created_at") or "", reverse=True)
    return out[:limit]


# ---- users CRUD ----


async def list_users(*, q: str | None = None, role: str | None = None, status: str | None = None) -> list[dict]:
    db = get_index_db()
    where = []
    params: list = []
    if q:
        where.append("(name LIKE ? OR email LIKE ?)")
        params.extend([f"%{q}%", f"%{q}%"])
    if role:
        where.append("auth_role = ?")
        params.append(role)
    if status:
        where.append("status = ?")
        params.append(status)
    sql = "SELECT * FROM users_index"
    if where:
        sql += " WHERE " + " AND ".join(where)
    sql += " ORDER BY created_at DESC LIMIT 200"
    rows = await db.fetchall(sql, params)
    out: list[dict] = []
    paths = get_paths()
    for r in rows:
        prof = read_json(paths.user_profile(r["id"])) or {}
        out.append({
            "id": r["id"],
            "email": r["email"],
            "name": r["name"],
            "auth_role": r["auth_role"],
            "status": r["status"],
            "feishu_bound": bool(r["feishu_user_id"]),
            "team": prof.get("team"),
            "title": prof.get("title"),
            "last_login_at": r["last_login_at"],
            "created_at": r["created_at"],
        })
    return out


async def create_user(
    *,
    operator: dict,
    email: str,
    name: str,
    auth_role: str = "user",
    password: str | None = None,
    team: str | None = None,
    title: str | None = None,
) -> dict:
    if auth_role == "super_admin" and operator["auth_role"] != "super_admin":
        raise APIError(403, ErrorCode.PERMISSION_DENIED, "仅 super_admin 可创建 super_admin")
    db = get_index_db()
    row = await db.fetchone("SELECT id FROM users_index WHERE email = ?", [email])
    if row:
        raise APIError(409, "EMAIL_EXISTS", "邮箱已存在")
    uid = _new_id()
    paths = get_paths()
    profile = {
        "id": uid,
        "email": email,
        "name": name,
        "auth_role": auth_role,
        "status": "active",
        "password_hash": hash_password(password) if password else None,
        "feishu_user_id": None,
        "feishu_bound_at": None,
        "team": team,
        "title": title,
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
            "email": email,
            "name": name,
            "auth_role": auth_role,
            "status": "active",
            "feishu_user_id": None,
            "last_login_at": None,
            "password_hash": profile["password_hash"],
            "created_at": profile["created_at"],
        },
    )
    await audit(
        admin_id=operator["id"],
        action="create_user",
        target_type="user",
        target_id=uid,
        diff={"after": {"email": email, "name": name, "auth_role": auth_role}},
    )
    return profile


async def update_user(*, operator: dict, uid: str, patch: dict) -> dict:
    paths = get_paths()
    profile = read_json(paths.user_profile(uid))
    if not profile:
        raise APIError(404, ErrorCode.RESOURCE_NOT_FOUND, "用户不存在")
    db = get_index_db()
    if "auth_role" in patch:
        if operator["auth_role"] != "super_admin":
            raise APIError(403, ErrorCode.PERMISSION_DENIED, "仅 super_admin 可修改角色")
        if uid == operator["id"] and patch["auth_role"] != "super_admin":
            raise APIError(400, ErrorCode.CANNOT_DEMOTE_SELF, "不能降级自己")
        if profile["auth_role"] == "super_admin" and patch["auth_role"] != "super_admin":
            row = await db.fetchone(
                "SELECT COUNT(*) AS c FROM users_index WHERE auth_role = 'super_admin'"
            )
            if (row or {}).get("c", 0) <= 1:
                raise APIError(
                    400,
                    ErrorCode.LAST_SUPER_ADMIN_PROTECTED,
                    "至少保留一个 super_admin",
                )
    diff = {"before": {}, "after": {}}
    for k in ("name", "auth_role", "team", "title", "status"):
        if k in patch and patch[k] != profile.get(k):
            diff["before"][k] = profile.get(k)
            diff["after"][k] = patch[k]
            profile[k] = patch[k]
    if "password" in patch and patch["password"]:
        profile["password_hash"] = hash_password(patch["password"])
        diff["after"]["password_reset"] = True
    write_json(paths.user_profile(uid), profile)
    await db.upsert(
        "users_index",
        {
            "id": uid,
            "email": profile["email"],
            "name": profile["name"],
            "auth_role": profile["auth_role"],
            "status": profile["status"],
            "feishu_user_id": profile.get("feishu_user_id"),
            "last_login_at": profile.get("last_login_at"),
            "password_hash": profile.get("password_hash"),
            "created_at": profile["created_at"],
        },
    )
    await audit(
        admin_id=operator["id"], action="update_user", target_type="user", target_id=uid, diff=diff
    )
    return profile


async def delete_user(*, operator: dict, uid: str) -> None:
    if operator["auth_role"] != "super_admin":
        raise APIError(403, ErrorCode.PERMISSION_DENIED, "仅 super_admin 可删除用户")
    if uid == operator["id"]:
        raise APIError(400, "CANNOT_DELETE_SELF", "不能删除自己")
    paths = get_paths()
    target = paths.user_profile(uid)
    profile = read_json(target)
    if not profile:
        return
    if profile["auth_role"] == "super_admin":
        db = get_index_db()
        row = await db.fetchone(
            "SELECT COUNT(*) AS c FROM users_index WHERE auth_role = 'super_admin'"
        )
        if (row or {}).get("c", 0) <= 1:
            raise APIError(
                400,
                ErrorCode.LAST_SUPER_ADMIN_PROTECTED,
                "至少保留一个 super_admin",
            )
    import shutil

    shutil.rmtree(paths.user_dir(uid), ignore_errors=True)
    db = get_index_db()
    await db.execute("DELETE FROM users_index WHERE id = ?", [uid])
    await audit(
        admin_id=operator["id"],
        action="delete_user",
        target_type="user",
        target_id=uid,
        diff={"before": {"email": profile["email"]}},
    )


# ---- agent prompt history (D114) ----


def _agent_history_path(aid: str) -> Path:
    return get_paths().agents / aid / "prompt" / "history.jsonl"


def list_prompt_history(aid: str) -> list[dict]:
    rows = read_jsonl(_agent_history_path(aid))
    return rows[::-1]


def update_agent_prompt(*, aid: str, new_prompt: str, operator: dict, change_note: str | None = None) -> dict:
    paths = get_paths()
    cfg_path = paths.agents / aid / "agent.json"
    cfg = read_json(cfg_path)
    if not cfg:
        raise APIError(404, ErrorCode.RESOURCE_NOT_FOUND, "Agent 不存在")
    md_path = paths.agents / aid / "prompt" / "system.md"
    old_prompt = md_path.read_text(encoding="utf-8") if md_path.exists() else cfg.get("system_prompt", "")
    snapshot = {
        "id": _new_id(),
        "agent_id": aid,
        "system_prompt": old_prompt,
        "saved_by": operator["id"],
        "saved_by_name": operator.get("name"),
        "saved_at": _now(),
        "change_note": change_note,
    }
    append_jsonl(_agent_history_path(aid), snapshot)
    md_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.write_text(new_prompt, encoding="utf-8")
    cfg["system_prompt"] = new_prompt
    write_json(cfg_path, cfg)
    return cfg


def rollback_agent_prompt(*, aid: str, history_id: str, operator: dict) -> dict:
    snapshots = list_prompt_history(aid)
    target = next((s for s in snapshots if s["id"] == history_id), None)
    if not target:
        raise APIError(404, ErrorCode.RESOURCE_NOT_FOUND, "版本不存在")
    return update_agent_prompt(
        aid=aid,
        new_prompt=target["system_prompt"],
        operator=operator,
        change_note=f"rollback to {history_id[:8]}",
    )


# ---- agent ranking (D103) ----


def agent_ranking(*, days: int = 30, limit: int = 10) -> list[dict]:
    paths = get_paths()
    counts: dict[str, int] = {}
    if not paths.tasks.exists():
        return []
    cutoff = datetime.now(tz=timezone.utc) - timedelta_days(days)
    for d in paths.tasks.iterdir():
        if not d.is_dir() or d.name.startswith("."):
            continue
        meta = read_json(d / "meta.json")
        if not meta or not meta.get("agent_id"):
            continue
        ua = meta.get("updated_at") or ""
        try:
            ts = datetime.fromisoformat(ua)
            if ts < cutoff:
                continue
        except ValueError:
            pass
        # count messages as proxy for usage
        for jl in (d / "conversations").glob("*.jsonl") if (d / "conversations").exists() else []:
            counts[meta["agent_id"]] = counts.get(meta["agent_id"], 0)
            try:
                with jl.open("r", encoding="utf-8") as f:
                    for _ in f:
                        counts[meta["agent_id"]] += 1
            except OSError:
                pass
    from .agents_svc import list_agents

    agents = {a["id"]: a for a in list_agents()}
    ranked = sorted(counts.items(), key=lambda x: x[1], reverse=True)[:limit]
    return [
        {
            "agent_id": aid,
            "name": agents.get(aid, {}).get("name", aid),
            "icon": agents.get(aid, {}).get("icon", "🤖"),
            "paradigm": agents.get(aid, {}).get("paradigm"),
            "messages": cnt,
            "satisfaction": 0.95,  # placeholder until D47 feedback table is wired
        }
        for aid, cnt in ranked
    ]


def timedelta_days(d: int):
    from datetime import timedelta

    return timedelta(days=d)
