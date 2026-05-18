"""Admin endpoints — overview/users/agents/audit. Require admin role."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from ...core.deps import get_current_user, require_admin, require_super_admin
from ...core.errors import APIError, ErrorCode, ok
from ...core.storage import get_index_db, get_paths, read_json
from ...services import admin_svc, agents_svc

router = APIRouter()


# ---- overview ----


@router.get("/overview/stats")
async def overview_stats(
    days: int = Query(30, ge=1, le=365),
    _: dict = Depends(require_admin),
):
    db = get_index_db()
    user_row = await db.fetchone("SELECT COUNT(*) AS c FROM users_index")
    task_row = await db.fetchone("SELECT COUNT(*) AS c FROM tasks_index")
    msg_row = await db.fetchone("SELECT COUNT(*) AS c FROM messages_index")
    return ok(
        {
            "users": int((user_row or {}).get("c") or 0),
            "tasks": int((task_row or {}).get("c") or 0),
            "messages": int((msg_row or {}).get("c") or 0),
            "days": days,
        }
    )


@router.get("/overview/alerts")
async def overview_alerts(_: dict = Depends(require_admin)):
    """Pending review counters (D104)."""
    from ...services import experience_card_svc

    paths = get_paths()
    counts = {"experience_cards": 0, "public_tasks": 0, "templates": 0, "scheduled_failed": 0}
    db = get_index_db()
    await experience_card_svc.ensure_index()
    row = await db.fetchone(
        "SELECT COUNT(*) AS c FROM experience_cards_index WHERE status = 'draft'"
    )
    counts["experience_cards"] = int((row or {}).get("c") or 0)
    tdir = paths.tasks / ".templates"
    if tdir.exists():
        for d in tdir.iterdir():
            if not d.is_dir():
                continue
            t = read_json(d / "template.json")
            if t and t.get("visibility") == "public" and t.get("status") == "draft":
                counts["templates"] += 1
    row = await db.fetchone(
        "SELECT COUNT(*) AS c FROM tasks_index WHERE visibility = 'public' AND publish_status = 'pending'"
    )
    counts["public_tasks"] = int((row or {}).get("c") or 0)
    return ok(counts)


@router.get("/overview/recent-users")
async def recent_users(_: dict = Depends(require_admin), limit: int = 10):
    db = get_index_db()
    rows = await db.fetchall(
        "SELECT id, email, name, auth_role, created_at FROM users_index ORDER BY created_at DESC LIMIT ?",
        [limit],
    )
    return ok({"items": rows})


@router.get("/overview/agent-ranking")
async def agent_ranking(_: dict = Depends(require_admin), days: int = 30):
    return ok({"items": admin_svc.agent_ranking(days=days)})


# ---- users ----


@router.get("/users")
async def list_users(
    q: str | None = Query(None),
    role: str | None = Query(None),
    status: str | None = Query(None),
    _: dict = Depends(require_admin),
):
    items = await admin_svc.list_users(q=q, role=role, status=status)
    return ok({"items": items, "total": len(items)})


@router.post("/users")
async def create_user(body: dict, op: dict = Depends(require_admin)):
    user = await admin_svc.create_user(
        operator=op,
        email=body["email"],
        name=body.get("name", body["email"]),
        auth_role=body.get("auth_role", "user"),
        password=body.get("password"),
        team=body.get("team"),
        title=body.get("title"),
    )
    return ok(user)


@router.patch("/users/{uid}")
async def update_user(uid: str, body: dict, op: dict = Depends(require_admin)):
    return ok(await admin_svc.update_user(operator=op, uid=uid, patch=body))


@router.delete("/users/{uid}")
async def delete_user(uid: str, op: dict = Depends(require_super_admin)):
    await admin_svc.delete_user(operator=op, uid=uid)
    return ok({"deleted": True})


# ---- audit ----


@router.get("/audit-logs")
async def audit_logs(
    admin_id: str | None = Query(None),
    limit: int = Query(100, ge=1, le=500),
    _: dict = Depends(require_admin),
):
    items = await admin_svc.list_audit_logs(admin_id=admin_id, limit=limit)
    return ok({"items": items, "total": len(items)})


# ---- agents (admin) ----


@router.get("/agents")
async def admin_list_agents(_: dict = Depends(require_admin)):
    items = agents_svc.list_agents()
    return ok({"items": items, "total": len(items)})


@router.get("/agents/{aid}")
async def admin_agent_detail(aid: str, _: dict = Depends(require_admin)):
    a = agents_svc.get_agent(aid)
    if not a:
        raise APIError(404, ErrorCode.RESOURCE_NOT_FOUND, "Agent 不存在")
    a["system_prompt"] = agents_svc.get_agent_system_prompt(aid)
    return ok(a)


@router.patch("/agents/{aid}")
async def admin_agent_update(aid: str, body: dict, op: dict = Depends(require_admin)):
    cfg = agents_svc.get_agent(aid)
    if not cfg:
        raise APIError(404, ErrorCode.RESOURCE_NOT_FOUND, "Agent 不存在")
    diff = {"before": {}, "after": {}}
    for k in ("name", "description", "icon", "color", "publish_status", "paradigm"):
        if k in body and body[k] != cfg.get(k):
            diff["before"][k] = cfg.get(k)
            diff["after"][k] = body[k]
            cfg[k] = body[k]
    if "system_prompt" in body:
        admin_svc.update_agent_prompt(
            aid=aid,
            new_prompt=body["system_prompt"],
            operator=op,
            change_note=body.get("change_note"),
        )
    else:
        from ...core.storage import write_json

        write_json(get_paths().agents / aid / "agent.json", cfg)
    await admin_svc.audit(
        admin_id=op["id"], action="update_agent", target_type="agent", target_id=aid, diff=diff
    )
    return ok(cfg)


@router.get("/agents/{aid}/prompt-history")
async def prompt_history(aid: str, _: dict = Depends(require_admin)):
    return ok({"items": admin_svc.list_prompt_history(aid)})


@router.post("/agents/{aid}/prompt-rollback")
async def prompt_rollback(aid: str, body: dict, op: dict = Depends(require_admin)):
    cfg = admin_svc.rollback_agent_prompt(aid=aid, history_id=body["history_id"], operator=op)
    await admin_svc.audit(
        admin_id=op["id"],
        action="rollback_agent_prompt",
        target_type="agent",
        target_id=aid,
        diff={"history_id": body["history_id"]},
    )
    return ok(cfg)


@router.post("/agents/{aid}/test-chat")
async def test_chat(aid: str, body: dict, _: dict = Depends(require_admin)):
    """Sandbox: not persisted, not metered. Return synchronous text."""
    from ...core.config import get_settings
    from ...services import llm_gateway

    s = get_settings()
    if not s.llm_enabled:
        raise APIError(503, ErrorCode.LLM_KEY_MISSING, "LLM 未配置")
    sp = body.get("system_prompt") or agents_svc.get_agent_system_prompt(aid)
    msgs = body.get("messages") or [{"role": "user", "content": body.get("content", "你好")}]
    model_id = body.get("model") or llm_gateway.resolve_model(None)
    result = await llm_gateway.complete_once(
        system_prompt=sp, messages=msgs, model=model_id, max_tokens=2048
    )
    return ok({"response": result.get("text") or "", "model": result.get("model"), "usage": result.get("usage")})
