from __future__ import annotations

from fastapi import APIRouter, Depends

from ...core.deps import TaskRole, get_current_user, require_task_role
from ...core.errors import APIError, ErrorCode, ok
from ...core.storage import file_transaction, get_paths
from ...schemas.task import TaskCreate
from ...services import agent_snapshot_svc, join_request_svc, task_svc

router = APIRouter()


@router.get("")
async def list_tasks(user: dict = Depends(get_current_user)):
    items = await task_svc.list_user_tasks(user["id"])
    return ok({"items": items, "total": len(items)})


@router.get("/public")
async def list_public(user: dict = Depends(get_current_user)):
    items = await task_svc.list_public_tasks()
    return ok({"items": items, "total": len(items)})


@router.post("")
async def create_task(body: TaskCreate, user: dict = Depends(get_current_user)):
    task = await task_svc.create_task(
        name=body.name,
        paradigm=body.paradigm,
        owner_id=user["id"],
        agent_id=body.agent_id,
        description=body.description,
        initial_prompt=body.initial_prompt,
        skill_ids=body.skill_ids,
        visibility=body.visibility,
    )
    return ok(task)


@router.get("/{task_id}")
async def get_task(task_id: str, user: dict = Depends(get_current_user)):
    return ok(await task_svc.get_task(task_id, user["id"]))


@router.get("/{task_id}/conversation")
async def task_conversation(task_id: str, user: dict = Depends(get_current_user)):
    await task_svc.get_task(task_id, user["id"])
    cid = await task_svc.get_or_create_default_conversation(task_id)
    messages = task_svc.load_conversation_messages(task_id, cid)
    return ok({"conversation_id": cid, "messages": messages})


@router.delete("/{task_id}")
async def delete_task(task_id: str, user: dict = Depends(get_current_user)):
    await task_svc.delete_task(task_id, user["id"])
    return ok({"deleted": True, "task_id": task_id})


@router.post("/{task_id}/agent/refresh")
async def refresh_agent_snapshot(
    task_id: str,
    body: dict | None = None,
    role: TaskRole = Depends(require_task_role(TaskRole.OWNER, TaskRole.ADMIN)),
    user: dict = Depends(get_current_user),
):
    expected = (body or {}).get("expected_agent_source_version")
    result = await agent_snapshot_svc.refresh_task_snapshot(
        task_id=task_id, user_id=user["id"], expected_version=expected,
    )
    return ok(result)


@router.post("/{task_id}/join-request")
async def submit_join(
    task_id: str,
    body: dict,
    role: TaskRole = Depends(require_task_role(TaskRole.VIEWER)),
    user: dict = Depends(get_current_user),
):
    req = await join_request_svc.submit(
        task_id=task_id, user_id=user["id"], message=body.get("message", ""),
    )
    return ok(req)


@router.get("/{task_id}/join-requests")
async def list_joins(
    task_id: str,
    status: str | None = None,
    role: TaskRole = Depends(require_task_role(TaskRole.OWNER, TaskRole.ADMIN)),
):
    items = await join_request_svc.list_requests(task_id=task_id, status=status)
    return ok({"items": items, "total": len(items)})


@router.post("/{task_id}/join-requests/{req_id}/review")
async def review_join(
    task_id: str,
    req_id: str,
    body: dict,
    role: TaskRole = Depends(require_task_role(TaskRole.OWNER, TaskRole.ADMIN)),
    user: dict = Depends(get_current_user),
):
    new_status = body.get("status", "approved")
    reason = body.get("reject_reason")
    req = await join_request_svc.review(
        task_id=task_id, req_id=req_id, new_status=new_status,
        operator_id=user["id"], reject_reason=reason,
    )
    return ok(req)


@router.delete("/{task_id}/collaborators/{user_id}")
async def remove_collaborator(
    task_id: str,
    user_id: str,
    role: TaskRole = Depends(require_task_role(TaskRole.OWNER, TaskRole.ADMIN)),
):
    paths = get_paths()
    cpath = paths.task_collaborators(task_id)
    with file_transaction([cpath]) as tx:
        collabs = tx.read_json(cpath, default=[])
        target = next((c for c in collabs if c["user_id"] == user_id), None)
        if not target:
            raise APIError(404, ErrorCode.RESOURCE_NOT_FOUND, "协作者不存在")
        if target.get("role") == "owner":
            raise APIError(400, ErrorCode.VALIDATION_ERROR, "不能移除 owner")
        target["status"] = "removed"
        tx.write_json(cpath, collabs)
    return ok({"removed": True})
