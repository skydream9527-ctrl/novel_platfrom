"""User-side experience cards: create draft + list per task / per agent."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from ...core.deps import get_current_user
from ...core.errors import APIError, ErrorCode, ok
from ...services import experience_card_svc, task_svc

router = APIRouter()


@router.post("/tasks/{task_id}")
async def create_card(task_id: str, body: dict, user: dict = Depends(get_current_user)):
    task = await task_svc.get_task(task_id, user["id"])
    title = (body.get("title") or "").strip()
    rule = (body.get("rule") or "").strip()
    if not title or not rule:
        raise APIError(400, ErrorCode.VALIDATION_ERROR, "title 和 rule 必填")
    card = await experience_card_svc.create_draft(
        task_id=task_id,
        author_id=user["id"],
        agent_id=task.get("agent_id"),
        title=title,
        rule=rule,
        reason=body.get("reason"),
        source_message_id=body.get("source_message_id"),
    )
    return ok(card)


@router.get("/tasks/{task_id}")
async def list_task_cards(
    task_id: str, status: str | None = Query(None), user: dict = Depends(get_current_user)
):
    await task_svc.get_task(task_id, user["id"])
    return ok({"items": await experience_card_svc.list_for_task(task_id, status=status)})


@router.get("/agents/{agent_id}")
async def list_agent_cards(agent_id: str, user: dict = Depends(get_current_user)):
    return ok({"items": await experience_card_svc.list_public(agent_id=agent_id)})
