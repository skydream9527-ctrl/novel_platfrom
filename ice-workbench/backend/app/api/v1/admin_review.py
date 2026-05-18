"""/admin/experience-cards + /admin/public-tasks + /admin/review-center."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from ...core.deps import get_current_user, require_admin
from ...core.errors import ok
from ...services import (
    admin_svc,
    experience_card_svc,
    public_task_svc,
    template_svc,
)

router = APIRouter()


# ---- experience cards ----


@router.get("/experience-cards")
async def admin_list_cards(
    status: str | None = Query(None),
    agent_id: str | None = Query(None),
    _: dict = Depends(require_admin),
):
    items = await experience_card_svc.list_admin(status=status, agent_id=agent_id)
    return ok({"items": items, "total": len(items)})


@router.post("/experience-cards/{card_id}/review")
async def review_card(card_id: str, body: dict, op: dict = Depends(require_admin)):
    new_status = body.get("status", "approved")
    reason = body.get("reject_reason")
    card = await experience_card_svc.update_status(
        card_id=card_id, new_status=new_status, operator_id=op["id"], reject_reason=reason
    )
    await admin_svc.audit(
        admin_id=op["id"],
        action="review_experience_card",
        target_type="experience_card",
        target_id=card_id,
        diff={"after": {"status": new_status, "reject_reason": reason}},
    )
    return ok(card)


@router.post("/experience-cards/batch-review")
async def batch_review_cards(body: dict, op: dict = Depends(require_admin)):
    ids = body.get("card_ids") or []
    new_status = body.get("status", "approved")
    reason = body.get("reject_reason")
    items = await experience_card_svc.batch_review(
        card_ids=ids, new_status=new_status, operator_id=op["id"], reject_reason=reason
    )
    await admin_svc.audit(
        admin_id=op["id"],
        action="batch_review_experience_cards",
        target_type="experience_card",
        target_id="batch",
        diff={"count": len(items), "status": new_status},
    )
    return ok({"items": items, "total": len(items)})


# ---- public tasks ----


@router.get("/public-tasks")
async def admin_list_public(
    status: str | None = Query(None),
    _: dict = Depends(require_admin),
):
    items = await public_task_svc.list_public(status=status)
    return ok({"items": items, "total": len(items)})


@router.post("/public-tasks/{task_id}/review")
async def review_public_task(task_id: str, body: dict, op: dict = Depends(require_admin)):
    decision = body.get("decision", "approve")
    reason = body.get("reason")
    meta = await public_task_svc.admin_review(
        task_id=task_id, decision=decision, reason=reason, operator_id=op["id"]
    )
    await admin_svc.audit(
        admin_id=op["id"],
        action=f"public_task_{decision}",
        target_type="task",
        target_id=task_id,
        diff={"reason": reason} if reason else {},
    )
    return ok(meta)


# ---- review center summary ----


@router.get("/review-center/summary")
async def review_center_summary(_: dict = Depends(require_admin)):
    drafts = await experience_card_svc.list_admin(status="draft", limit=500)
    pending_tasks = await public_task_svc.list_public(status="pending")
    pending_templates = template_svc.list_templates(visibility="public")
    pending_templates = [t for t in pending_templates if t.get("status") == "draft"]
    return ok(
        {
            "experience_cards_pending": len(drafts),
            "public_tasks_pending": len(pending_tasks),
            "templates_pending": len(pending_templates),
        }
    )


# ---- user-side share/unshare (authenticated, not admin) ----

share_router = APIRouter()


@share_router.post("/{task_id}/share")
async def share_task(task_id: str, user: dict = Depends(get_current_user)):
    meta = await public_task_svc.share_task(task_id=task_id, owner_id=user["id"])
    return ok(meta)


@share_router.post("/{task_id}/unshare")
async def unshare_task(task_id: str, user: dict = Depends(get_current_user)):
    meta = await public_task_svc.unshare_task(task_id=task_id, owner_id=user["id"])
    return ok(meta)
