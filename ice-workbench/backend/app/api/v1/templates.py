from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from ...core.deps import get_current_user, require_admin
from ...core.errors import ok
from ...services import template_svc

router = APIRouter()


@router.get("")
async def list_templates(
    visibility: str | None = Query(None),
    user: dict = Depends(get_current_user),
):
    items = template_svc.list_templates(owner_id=user["id"], visibility=visibility)
    return ok({"items": items, "total": len(items)})


@router.post("")
async def create_template(body: dict, user: dict = Depends(get_current_user)):
    return ok(template_svc.create_template(owner_id=user["id"], body=body))


@router.get("/{tid}")
async def get_template(tid: str, user: dict = Depends(get_current_user)):
    t = template_svc.get_template(tid)
    if not t:
        from ...core.errors import APIError, ErrorCode

        raise APIError(404, ErrorCode.RESOURCE_NOT_FOUND, "模板不存在")
    return ok(t)


@router.patch("/{tid}")
async def update_template(tid: str, body: dict, user: dict = Depends(get_current_user)):
    return ok(template_svc.update_template(tid, user["id"], body))


@router.delete("/{tid}")
async def delete_template(tid: str, user: dict = Depends(get_current_user)):
    template_svc.delete_template(
        tid, user["id"], is_admin=user["auth_role"] in ("admin", "super_admin")
    )
    return ok({"deleted": True})


@router.post("/{tid}/review")
async def review_template(tid: str, body: dict, _: dict = Depends(require_admin)):
    return ok(
        template_svc.review_template(
            tid, status=body.get("status", "approved"), reject_reason=body.get("reject_reason")
        )
    )
