from __future__ import annotations

from fastapi import APIRouter, Depends

from ...core.deps import get_current_user
from ...core.errors import ok
from ...services import notification_svc

router = APIRouter()


@router.get("")
async def list_my_notifications(user: dict = Depends(get_current_user)):
    items = await notification_svc.list_notifications(user["id"])
    unread = await notification_svc.unread_count(user["id"])
    return ok({"items": items, "total": len(items), "unread": unread})


@router.post("/read-all")
async def mark_all_read(user: dict = Depends(get_current_user)):
    await notification_svc.mark_all_read(user["id"])
    return ok({"unread": 0})


@router.post("/{nid}/read")
async def mark_read(nid: str, user: dict = Depends(get_current_user)):
    await notification_svc.mark_read(user["id"], nid)
    return ok({"id": nid, "is_read": True})
