"""/admin/settings — global toggles, system params, LLM models, announcements."""
from __future__ import annotations

from fastapi import APIRouter, Depends

from ...core.deps import require_admin, require_super_admin
from ...core.errors import APIError, ErrorCode, ok
from ...services import admin_svc, sysconfig_svc

router = APIRouter()


# ---- aggregated read ----
@router.get("")
async def settings_read(_: dict = Depends(require_admin)):
    cfg = sysconfig_svc.get_full_config()
    return ok(cfg)


# ---- toggles (super_admin only) ----
@router.get("/toggles")
async def get_toggles(_: dict = Depends(require_admin)):
    return ok(sysconfig_svc.get_toggles())


@router.patch("/toggles")
async def update_toggles(body: dict, op: dict = Depends(require_super_admin)):
    new = sysconfig_svc.update_toggles(body or {})
    await admin_svc.audit(
        admin_id=op["id"], action="update_toggles", target_type="config", target_id="toggles",
        diff={"after": new},
    )
    return ok(new)


# ---- system params ----
@router.patch("/system-params")
async def update_system_params(body: dict, op: dict = Depends(require_admin)):
    new = sysconfig_svc.update_system_params(body or {})
    await admin_svc.audit(
        admin_id=op["id"], action="update_system_params", target_type="config", target_id="system_params",
        diff={"after": new},
    )
    return ok(new)


@router.post("/system-params/reset")
async def reset_system_params(op: dict = Depends(require_admin)):
    new = sysconfig_svc.reset_system_params()
    await admin_svc.audit(
        admin_id=op["id"], action="reset_system_params", target_type="config", target_id="system_params",
    )
    return ok(new)


# ---- LLM ----
@router.get("/llm")
async def get_llm(_: dict = Depends(require_admin)):
    return ok(sysconfig_svc.get_llm_config())


@router.patch("/llm/budget")
async def update_budget(body: dict, op: dict = Depends(require_super_admin)):
    if "budget_monthly_usd" not in body or "budget_alert_threshold" not in body:
        raise APIError(400, ErrorCode.VALIDATION_ERROR, "缺少 budget_monthly_usd / budget_alert_threshold")
    new = sysconfig_svc.update_llm_budget(
        budget_monthly_usd=float(body["budget_monthly_usd"]),
        budget_alert_threshold=float(body["budget_alert_threshold"]),
    )
    await admin_svc.audit(
        admin_id=op["id"], action="update_llm_budget", target_type="config", target_id="llm.budget",
        diff={"after": {"budget_monthly_usd": new["budget_monthly_usd"], "budget_alert_threshold": new["budget_alert_threshold"]}},
    )
    return ok(new)


@router.patch("/llm/models/{model_id}")
async def update_model(model_id: str, body: dict, op: dict = Depends(require_admin)):
    new = sysconfig_svc.update_llm_model(model_id, body or {})
    await admin_svc.audit(
        admin_id=op["id"], action="update_llm_model", target_type="llm_model", target_id=model_id,
        diff={"after": new},
    )
    return ok(new)


# ---- announcements ----
@router.get("/announcements")
async def list_anns(_: dict = Depends(require_admin)):
    return ok({"items": sysconfig_svc.list_announcements()})


@router.post("/announcements")
async def create_ann(body: dict, op: dict = Depends(require_admin)):
    rec = sysconfig_svc.create_announcement(
        title=body.get("title", ""),
        body=body.get("body", ""),
        level=body.get("level", "info"),
        audience_scope=body.get("audience_scope", "all"),
        status=body.get("status", "draft"),
    )
    await admin_svc.audit(
        admin_id=op["id"], action="create_announcement", target_type="announcement", target_id=rec["id"],
    )
    return ok(rec)


@router.patch("/announcements/{ann_id}")
async def update_ann(ann_id: str, body: dict, op: dict = Depends(require_admin)):
    rec = sysconfig_svc.update_announcement(ann_id, body or {})
    await admin_svc.audit(
        admin_id=op["id"], action="update_announcement", target_type="announcement", target_id=ann_id,
    )
    return ok(rec)


@router.delete("/announcements/{ann_id}")
async def delete_ann(ann_id: str, op: dict = Depends(require_admin)):
    sysconfig_svc.delete_announcement(ann_id)
    await admin_svc.audit(
        admin_id=op["id"], action="delete_announcement", target_type="announcement", target_id=ann_id,
    )
    return ok({"deleted": True})
