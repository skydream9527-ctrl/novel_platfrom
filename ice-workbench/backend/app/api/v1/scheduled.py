from __future__ import annotations

from fastapi import APIRouter, Depends

from ...core.deps import get_current_user
from ...core.errors import ok
from ...services import scheduler_svc, task_svc

router = APIRouter()


@router.get("")
async def list_my(user: dict = Depends(get_current_user)):
    items = scheduler_svc.list_for_user(user["id"])
    return ok({"items": items, "total": len(items)})


@router.get("/by-task/{task_id}")
async def list_by_task(task_id: str, user: dict = Depends(get_current_user)):
    await task_svc.get_task(task_id, user["id"])
    items = scheduler_svc.list_for_task(task_id)
    return ok({"items": items, "total": len(items)})


@router.post("/by-task/{task_id}")
async def create(task_id: str, body: dict, user: dict = Depends(get_current_user)):
    await task_svc.get_task(task_id, user["id"])
    return ok(scheduler_svc.create(task_id=task_id, owner_id=user["id"], body=body))


@router.patch("/by-task/{task_id}/{sid}")
async def update(task_id: str, sid: str, body: dict, user: dict = Depends(get_current_user)):
    await task_svc.get_task(task_id, user["id"])
    return ok(scheduler_svc.update(task_id, sid, user["id"], body))


@router.delete("/by-task/{task_id}/{sid}")
async def remove(task_id: str, sid: str, user: dict = Depends(get_current_user)):
    await task_svc.get_task(task_id, user["id"])
    scheduler_svc.remove(task_id, sid, user["id"])
    return ok({"deleted": True})


@router.post("/by-task/{task_id}/{sid}/run-now")
async def run_now(task_id: str, sid: str, user: dict = Depends(get_current_user)):
    await task_svc.get_task(task_id, user["id"])
    return ok(await scheduler_svc.run_now(task_id, sid, user["id"]))


@router.get("/by-task/{task_id}/{sid}/runs")
async def list_runs(task_id: str, sid: str, user: dict = Depends(get_current_user)):
    await task_svc.get_task(task_id, user["id"])
    return ok({"items": scheduler_svc.list_runs(task_id, sid)})
