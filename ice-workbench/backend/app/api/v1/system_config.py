from __future__ import annotations

from fastapi import APIRouter

from ...core.config import get_settings
from ...core.errors import ok
from ...services import sysconfig_svc

router = APIRouter()


@router.get("/global-toggles")
async def global_toggles():
    s = get_settings()
    toggles = sysconfig_svc.get_toggles()
    params = sysconfig_svc.get_system_params()
    return ok(
        {
            **toggles,
            "feishu_enabled": s.feishu_enabled,
            "llm_enabled": s.llm_enabled,
            "kyuubi_enabled": s.kyuubi_enabled,
            "upload_max_size_mb": params["upload_max_size_mb"],
            "upload_max_size_hard_cap_mb": params["upload_max_size_hard_cap_mb"],
        }
    )


@router.get("/announcements")
async def public_announcements():
    return ok({"items": sysconfig_svc.list_active_announcements()})


@router.get("/models")
async def public_models():
    """Models that are enabled in admin settings — for ModelSelector UI.
    Authenticated read of (id + label) only; pricing stays admin-only."""
    cfg = sysconfig_svc.get_llm_config()
    items = [
        {"id": m["id"], "label": m["label"]}
        for m in cfg.get("models") or []
        if m.get("enabled", True)
    ]
    default_id = items[0]["id"] if items else sysconfig_svc.DEFAULTS["llm"]["models"][0]["id"]
    return ok({"items": items, "default": default_id})
