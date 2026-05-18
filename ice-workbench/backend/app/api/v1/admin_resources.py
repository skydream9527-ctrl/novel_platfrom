"""/admin/{files,skills,knowledge-bases,templates} resource management."""
from __future__ import annotations

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile

from ...core.deps import require_admin
from ...core.errors import APIError, ErrorCode, ok
from ...services import admin_svc, file_svc, kb_svc, skill_svc, template_svc

router = APIRouter()


# ---------- Files ----------


@router.get("/files")
async def admin_list_files(_: dict = Depends(require_admin)):
    items = await file_svc.list_public_files()
    return ok({"items": items, "total": len(items)})


@router.post("/files/upload")
async def admin_upload_file(
    is_pinned: bool = Form(False),
    file: UploadFile = File(...),
    op: dict = Depends(require_admin),
):
    data = await file.read()
    meta = await file_svc.upload_public_file(
        filename=file.filename or "untitled", data=data, is_pinned=is_pinned
    )
    await admin_svc.audit(
        admin_id=op["id"], action="upload_public_file", target_type="public_file", target_id=meta["id"],
        diff={"name": meta["name"], "size": meta["size_bytes"]},
    )
    return ok(meta)


@router.get("/files/{file_id}/content")
async def admin_read_file(file_id: str, _: dict = Depends(require_admin)):
    return ok(await file_svc.read_public_file(file_id))


@router.patch("/files/{file_id}")
async def admin_update_file(file_id: str, body: dict, op: dict = Depends(require_admin)):
    meta = await file_svc.update_public_file(
        file_id, content=body.get("content"), is_pinned=body.get("is_pinned")
    )
    await admin_svc.audit(
        admin_id=op["id"], action="update_public_file", target_type="public_file", target_id=file_id,
        diff={"is_pinned": meta.get("is_pinned"), "content_changed": "content" in body},
    )
    return ok(meta)


@router.delete("/files/{file_id}")
async def admin_delete_file(file_id: str, op: dict = Depends(require_admin)):
    await file_svc.delete_public_file(file_id)
    await admin_svc.audit(
        admin_id=op["id"], action="delete_public_file", target_type="public_file", target_id=file_id,
    )
    return ok({"deleted": True})


# ---------- Skills ----------


@router.get("/skills")
async def admin_list_skills(_: dict = Depends(require_admin)):
    items = skill_svc.list_all()
    return ok({"items": items, "total": len(items)})


@router.get("/skills/{skill_id}")
async def admin_get_skill(skill_id: str, _: dict = Depends(require_admin)):
    s = skill_svc.get_skill(skill_id)
    if not s:
        raise APIError(404, ErrorCode.RESOURCE_NOT_FOUND, "Skill 不存在")
    return ok(s)


@router.post("/skills")
async def admin_create_skill(body: dict, op: dict = Depends(require_admin)):
    rec = skill_svc.upsert_skill(skill_id=None, body=body)
    await admin_svc.audit(
        admin_id=op["id"], action="create_skill", target_type="skill", target_id=rec["id"],
    )
    return ok(rec)


@router.patch("/skills/{skill_id}")
async def admin_update_skill(skill_id: str, body: dict, op: dict = Depends(require_admin)):
    rec = skill_svc.upsert_skill(skill_id=skill_id, body=body)
    await admin_svc.audit(
        admin_id=op["id"], action="update_skill", target_type="skill", target_id=skill_id,
    )
    return ok(rec)


@router.delete("/skills/{skill_id}")
async def admin_delete_skill(skill_id: str, op: dict = Depends(require_admin)):
    skill_svc.delete_skill(skill_id)
    await admin_svc.audit(
        admin_id=op["id"], action="delete_skill", target_type="skill", target_id=skill_id,
    )
    return ok({"deleted": True})


@router.post("/skills/validate-schema")
async def admin_validate_schema(body: dict, _: dict = Depends(require_admin)):
    schema = body.get("tool_schema") or body
    ok_, reason = skill_svc.validate_tool_schema(schema)
    return ok({"valid": ok_, "reason": reason})


@router.post("/skills/{skill_id}/test-run")
async def admin_test_run_skill(skill_id: str, body: dict, _: dict = Depends(require_admin)):
    res = await skill_svc.test_run(skill_id, body.get("arguments") or {})
    return ok(res)


# ---------- Knowledge Bases ----------


@router.get("/knowledge-bases")
async def admin_list_kbs(_: dict = Depends(require_admin)):
    items = kb_svc.list_kbs()
    return ok({"items": items, "total": len(items)})


@router.get("/knowledge-bases/{kb_id}")
async def admin_get_kb(kb_id: str, _: dict = Depends(require_admin)):
    kb = kb_svc.get_kb(kb_id)
    if not kb:
        raise APIError(404, ErrorCode.RESOURCE_NOT_FOUND, "知识库不存在")
    return ok(kb)


@router.post("/knowledge-bases")
async def admin_create_kb(body: dict, op: dict = Depends(require_admin)):
    rec = kb_svc.create_kb(body)
    await admin_svc.audit(
        admin_id=op["id"], action="create_kb", target_type="kb", target_id=rec["id"],
    )
    return ok(rec)


@router.patch("/knowledge-bases/{kb_id}")
async def admin_update_kb(kb_id: str, body: dict, op: dict = Depends(require_admin)):
    rec = kb_svc.update_kb(kb_id, body)
    await admin_svc.audit(
        admin_id=op["id"], action="update_kb", target_type="kb", target_id=kb_id,
    )
    return ok(rec)


@router.delete("/knowledge-bases/{kb_id}")
async def admin_delete_kb(kb_id: str, op: dict = Depends(require_admin)):
    kb_svc.delete_kb(kb_id)
    await admin_svc.audit(
        admin_id=op["id"], action="delete_kb", target_type="kb", target_id=kb_id,
    )
    return ok({"deleted": True})


@router.post("/knowledge-bases/{kb_id}/sync")
async def admin_sync_kb(kb_id: str, op: dict = Depends(require_admin)):
    log = await kb_svc.sync_kb(kb_id, trigger="manual")
    await admin_svc.audit(
        admin_id=op["id"], action="sync_kb", target_type="kb", target_id=kb_id,
        diff={"status": log["status"]},
    )
    return ok(log)


@router.get("/knowledge-bases/{kb_id}/sync-logs")
async def admin_kb_sync_logs(kb_id: str, _: dict = Depends(require_admin)):
    return ok({"items": kb_svc.list_sync_logs(kb_id)})


@router.post("/knowledge-bases/{kb_id}/test-connection")
async def admin_kb_test(kb_id: str, _: dict = Depends(require_admin)):
    return ok(await kb_svc.test_connection(kb_id))


# ---------- Templates (admin extensions) ----------


@router.get("/templates")
async def admin_list_templates(
    status: str | None = Query(None),
    visibility: str | None = Query(None),
    _: dict = Depends(require_admin),
):
    items = template_svc.list_templates()
    if status:
        items = [t for t in items if t.get("status") == status]
    if visibility:
        items = [t for t in items if t.get("visibility") == visibility]
    return ok({"items": items, "total": len(items)})


@router.post("/templates/{tid}/review")
async def admin_review_template(tid: str, body: dict, op: dict = Depends(require_admin)):
    rec = template_svc.review_template(
        tid, status=body.get("status", "approved"), reject_reason=body.get("reject_reason")
    )
    await admin_svc.audit(
        admin_id=op["id"], action="review_template", target_type="template", target_id=tid,
        diff={"status": rec["status"]},
    )
    return ok(rec)


@router.delete("/templates/{tid}")
async def admin_delete_template(tid: str, op: dict = Depends(require_admin)):
    template_svc.delete_template(tid, owner_id=op["id"], is_admin=True)
    await admin_svc.audit(
        admin_id=op["id"], action="delete_template", target_type="template", target_id=tid,
    )
    return ok({"deleted": True})
