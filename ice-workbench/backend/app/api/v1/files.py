from __future__ import annotations

import json

from fastapi import APIRouter, Depends, File, Form, UploadFile

from ...core.deps import TaskRole, derive_task_role, get_current_user
from ...core.errors import APIError, ErrorCode, ok
from ...core.storage import get_paths, read_json
from ...services import file_svc, task_svc

router = APIRouter()


async def _task_role_from_form(
    task_id: str = Form(...),
    user: dict = Depends(get_current_user),
) -> TaskRole:
    """Task-role gate for endpoints where task_id arrives as a form field
    (not a path param), so `require_task_role` cannot be used directly."""
    paths = get_paths()
    meta = read_json(paths.task_meta(task_id))
    if not meta:
        raise APIError(404, ErrorCode.RESOURCE_NOT_FOUND, "任务不存在")
    collabs = read_json(paths.task_collaborators(task_id), default=[]) or []
    role = derive_task_role(
        meta, collabs, user_id=user["id"], is_admin=bool(user.get("is_admin"))
    )
    if role is None or role not in (TaskRole.EDITOR, TaskRole.OWNER, TaskRole.ADMIN):
        raise APIError(403, ErrorCode.PERMISSION_DENIED, "无权执行")
    return role


@router.post("/upload")
async def upload(
    task_id: str = Form(...),
    scope: str = Form("uploaded"),
    file: UploadFile = File(...),
    user: dict = Depends(get_current_user),
):
    await task_svc.get_task(task_id, user["id"])
    data = await file.read()
    meta = await file_svc.upload_task_file(
        task_id=task_id, owner_id=user["id"], filename=file.filename or "untitled", data=data, scope=scope
    )
    return ok(meta)


@router.get("/task/{task_id}")
async def list_task_files(task_id: str, user: dict = Depends(get_current_user)):
    await task_svc.get_task(task_id, user["id"])
    items = await file_svc.list_task_files(task_id)
    return ok({"items": items, "total": len(items)})


@router.get("/public")
async def list_public_files(user: dict = Depends(get_current_user)):
    items = await file_svc.list_public_files()
    return ok({"items": items, "total": len(items)})


@router.get("/public/{file_id}/content")
async def read_public_file(file_id: str, user: dict = Depends(get_current_user)):
    return ok(await file_svc.read_public_file(file_id))


@router.get("/task/{task_id}/{file_id}/content")
async def read_file_content(task_id: str, file_id: str, user: dict = Depends(get_current_user)):
    await task_svc.get_task(task_id, user["id"])
    return ok(await file_svc.read_file_text(task_id, file_id))


@router.delete("/task/{task_id}/{file_id}")
async def delete_file(task_id: str, file_id: str, user: dict = Depends(get_current_user)):
    await task_svc.get_task(task_id, user["id"])
    await file_svc.delete_task_file(task_id, file_id)
    return ok({"deleted": True})


@router.post("/import")
async def import_external(
    task_id: str = Form(...),
    source_type: str = Form(...),
    source_url: str = Form(...),
    source_ref: str | None = Form(None),  # JSON-encoded dict
    user: dict = Depends(get_current_user),
    role: TaskRole = Depends(_task_role_from_form),
):
    ref = json.loads(source_ref) if source_ref else None
    meta = await file_svc.import_external(
        task_id=task_id,
        user_id=user["id"],
        source_type=source_type,
        source_url=source_url,
        source_ref=ref,
    )
    return ok(meta)


@router.post("/{file_id}/refresh")
async def refresh_imported(
    file_id: str,
    task_id: str = Form(...),
    user: dict = Depends(get_current_user),
    role: TaskRole = Depends(_task_role_from_form),
):
    is_owner = role == TaskRole.OWNER
    is_admin = role == TaskRole.ADMIN
    result = await file_svc.refresh_imported(
        task_id=task_id,
        file_id=file_id,
        user_id=user["id"],
        is_owner=is_owner,
        is_admin=is_admin,
    )
    return ok(result)
