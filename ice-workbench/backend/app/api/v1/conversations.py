from __future__ import annotations

from fastapi import APIRouter, Depends

from ...core.deps import TaskRole, get_current_user, require_task_role
from ...core.errors import APIError, ErrorCode, ok
from ...services import conversation_svc

router = APIRouter()


@router.get("/tasks/{task_id}/conversations")
async def list_convs(
    task_id: str,
    role: TaskRole = Depends(require_task_role(TaskRole.VIEWER, TaskRole.EDITOR, TaskRole.OWNER, TaskRole.ADMIN)),
):
    items = await conversation_svc.list_conversations(task_id=task_id)
    return ok({"items": items, "total": len(items)})


@router.post("/tasks/{task_id}/conversations")
async def create_conv(
    task_id: str,
    body: dict | None = None,
    role: TaskRole = Depends(require_task_role(TaskRole.EDITOR, TaskRole.OWNER, TaskRole.ADMIN)),
    user: dict = Depends(get_current_user),
):
    title = (body or {}).get("title")
    conv = await conversation_svc.create_conversation(
        task_id=task_id, created_by=user["id"], title=title,
    )
    return ok(conv)


@router.patch("/tasks/{task_id}/conversations/{conv_id}")
async def rename_conv(
    task_id: str,
    conv_id: str,
    body: dict,
    role: TaskRole = Depends(require_task_role(TaskRole.EDITOR, TaskRole.OWNER, TaskRole.ADMIN)),
    user: dict = Depends(get_current_user),
):
    # Creator or owner only
    items = await conversation_svc.list_conversations(task_id=task_id)
    target = next((c for c in items if c["id"] == conv_id), None)
    if not target:
        raise APIError(404, ErrorCode.RESOURCE_NOT_FOUND, "对话不存在")
    if target["created_by"] != user["id"] and role not in (TaskRole.OWNER, TaskRole.ADMIN):
        raise APIError(403, ErrorCode.PERMISSION_DENIED, "仅创建者或任务 owner 可改标题")
    title = body.get("title", "").strip()
    if not title:
        raise APIError(400, ErrorCode.VALIDATION_ERROR, "title 不能为空")
    return ok(await conversation_svc.rename_conversation(task_id=task_id, conv_id=conv_id, title=title))


@router.delete("/tasks/{task_id}/conversations/{conv_id}")
async def delete_conv(
    task_id: str,
    conv_id: str,
    role: TaskRole = Depends(require_task_role(TaskRole.EDITOR, TaskRole.OWNER, TaskRole.ADMIN)),
    user: dict = Depends(get_current_user),
):
    items = await conversation_svc.list_conversations(task_id=task_id)
    target = next((c for c in items if c["id"] == conv_id), None)
    if not target:
        raise APIError(404, ErrorCode.RESOURCE_NOT_FOUND, "对话不存在")
    if target["created_by"] != user["id"] and role not in (TaskRole.OWNER, TaskRole.ADMIN):
        raise APIError(403, ErrorCode.PERMISSION_DENIED, "仅创建者或任务 owner 可删除")
    await conversation_svc.delete_conversation(task_id=task_id, conv_id=conv_id)
    return ok({"deleted": True})


@router.get("/tasks/{task_id}/conversations/{conv_id}")
async def get_conv(
    task_id: str,
    conv_id: str,
    role: TaskRole = Depends(require_task_role(TaskRole.VIEWER, TaskRole.EDITOR, TaskRole.OWNER, TaskRole.ADMIN)),
):
    from ...services import task_svc
    # Verify the conv belongs to this task
    items = await conversation_svc.list_conversations(task_id=task_id)
    if not any(c["id"] == conv_id for c in items):
        raise APIError(404, ErrorCode.RESOURCE_NOT_FOUND, "对话不存在")
    messages = task_svc.load_conversation_messages(task_id, conv_id)
    return ok({"conversation_id": conv_id, "messages": messages})
