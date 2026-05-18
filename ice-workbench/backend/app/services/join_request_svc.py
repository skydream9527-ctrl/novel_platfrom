"""Join requests for public task collaboration (spec 3.4 / 4 / W3)."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from ..core.errors import APIError, ErrorCode
from ..core.storage import file_transaction, get_paths, read_json


def _now() -> str:
    return datetime.now(tz=timezone.utc).isoformat()


def _new_id() -> str:
    return "req_" + uuid.uuid4().hex


async def submit(*, task_id: str, user_id: str, message: str) -> dict:
    paths = get_paths()
    meta = read_json(paths.task_meta(task_id))
    if not meta:
        raise APIError(404, ErrorCode.RESOURCE_NOT_FOUND, "任务不存在")
    if meta.get("visibility") != "public" or meta.get("publish_status") != "published":
        raise APIError(400, ErrorCode.VALIDATION_ERROR, "仅对已公开的任务可申请加入")

    collabs = read_json(paths.task_collaborators(task_id), default=[]) or []
    if any(c.get("user_id") == user_id and c.get("status") == "active" for c in collabs):
        raise APIError(400, ErrorCode.JOIN_ALREADY_MEMBER, "已是任务成员")

    jr_path = paths.task_join_requests(task_id)
    with file_transaction([jr_path]) as tx:
        reqs = tx.read_json(jr_path, default=[])
        if any(r.get("user_id") == user_id and r.get("status") == "pending" for r in reqs):
            raise APIError(409, ErrorCode.JOIN_ALREADY_PENDING, "已有待处理申请")
        req = {
            "id": _new_id(),
            "user_id": user_id,
            "message": message,
            "status": "pending",
            "created_at": _now(),
            "reviewed_at": None,
            "reviewed_by": None,
        }
        reqs.append(req)
        tx.write_json(jr_path, reqs)
    return req


async def list_requests(*, task_id: str, status: str | None = None) -> list[dict]:
    paths = get_paths()
    reqs = read_json(paths.task_join_requests(task_id), default=[]) or []
    if status:
        reqs = [r for r in reqs if r.get("status") == status]
    return reqs


async def review(
    *, task_id: str, req_id: str, new_status: str, operator_id: str,
    reject_reason: str | None = None,
) -> dict:
    if new_status not in {"approved", "rejected"}:
        raise APIError(400, ErrorCode.VALIDATION_ERROR, "new_status must be approved|rejected")
    paths = get_paths()
    jr_path = paths.task_join_requests(task_id)
    collab_path = paths.task_collaborators(task_id)
    with file_transaction([jr_path, collab_path]) as tx:
        reqs = tx.read_json(jr_path, default=[])
        target = next((r for r in reqs if r["id"] == req_id), None)
        if not target:
            raise APIError(404, ErrorCode.RESOURCE_NOT_FOUND, "申请不存在")
        if target.get("status") != "pending":
            raise APIError(409, ErrorCode.VALIDATION_ERROR, "申请已处理")
        target["status"] = new_status
        target["reviewed_at"] = _now()
        target["reviewed_by"] = operator_id
        if reject_reason:
            target["reject_reason"] = reject_reason
        tx.write_json(jr_path, reqs)

        if new_status == "approved":
            collabs = tx.read_json(collab_path, default=[])
            collabs.append({
                "user_id": target["user_id"],
                "role": "editor",
                "joined_at": _now(),
                "status": "active",
            })
            tx.write_json(collab_path, collabs)

    try:
        from . import admin_svc
        await admin_svc.audit(
            admin_id=operator_id,
            action=f"{new_status}_join_request",
            target_type="task",
            target_id=task_id,
            diff={"request_id": req_id, "applicant": target["user_id"]},
        )
    except Exception:
        pass  # audit must never block business path
    return target
