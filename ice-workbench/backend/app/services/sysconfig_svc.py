"""System configuration. Source of truth: .cache/system-config.json (cache-tier).

Settings are read-mostly; we keep them in a single JSON file for simplicity. The
file also persists across restarts (it lives next to the SQLite cache, not the
project root, since it's environment state — separate from the immutable repo).

Default values live in DEFAULTS; overrides are merged on read.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from pathlib import Path

from ..core.errors import APIError, ErrorCode
from ..core.storage import get_paths, read_json, write_json


def _now() -> str:
    return datetime.now(tz=timezone.utc).isoformat()


def _config_path() -> Path:
    return get_paths().cache / "system-config.json"


DEFAULTS: dict = {
    "toggles": {
        "enable_open_register": False,
        "enable_public_task_review": False,
        "enable_feishu_strict_whitelist": False,
        # When true (default): a user logging in via Feishu for the first time
        # gets a fresh auth_role=user account auto-created. Set false to
        # require admin-side whitelisting before Feishu login works.
        "enable_feishu_auto_register": True,
    },
    "system_params": {
        "upload_max_size_mb": 20,
        "upload_max_size_hard_cap_mb": 50,
        "context_size": 20,
        "tool_call_max_rounds": 5,
        "tool_call_timeout_s": 30,
    },
    "llm": {
        "budget_monthly_usd": 200.0,
        "budget_alert_threshold": 0.8,
        "models": [
            {"id": "ppio/pa/claude-opus-4-7", "label": "Claude Opus 4.7", "input_unit_price": 15.0, "output_unit_price": 75.0, "enabled": True},
            {"id": "ppio/pa/claude-opus-4-6", "label": "Claude Opus 4.6", "input_unit_price": 15.0, "output_unit_price": 75.0, "enabled": True},
            {"id": "ppio/pa/claude-sonnet-4-6", "label": "Claude Sonnet 4.6", "input_unit_price": 3.0, "output_unit_price": 15.0, "enabled": True},
            {"id": "azure_openai/gpt-5.4", "label": "GPT-5.4", "input_unit_price": 5.0, "output_unit_price": 25.0, "enabled": True},
            {"id": "azure_openai/gpt-5.3-codex", "label": "GPT-5.3 Codex", "input_unit_price": 5.0, "output_unit_price": 25.0, "enabled": True},
            {"id": "vertex_ai/gemini-3.1-pro-preview", "label": "Gemini 3.1 Pro", "input_unit_price": 2.5, "output_unit_price": 12.5, "enabled": True},
            {"id": "xiaomi/glm-5", "label": "GLM-5 (Xiaomi)", "input_unit_price": 1.0, "output_unit_price": 4.0, "enabled": True},
            {"id": "xiaomi/mimo-v2.5-pro", "label": "MiMo v2.5 Pro (Xiaomi)", "input_unit_price": 1.0, "output_unit_price": 4.0, "enabled": True},
        ],
    },
    "announcements": [],
}


def _read() -> dict:
    p = _config_path()
    if not p.exists():
        write_json(p, DEFAULTS)
        return _deep_copy(DEFAULTS)
    saved = read_json(p, default={}) or {}
    return _merge(_deep_copy(DEFAULTS), saved)


def _deep_copy(d: dict) -> dict:
    import copy

    return copy.deepcopy(d)


def _merge(base: dict, override: dict) -> dict:
    """Shallow merge dicts; lists are replaced (not appended)."""
    for k, v in override.items():
        if isinstance(v, dict) and isinstance(base.get(k), dict):
            base[k] = _merge(base[k], v)
        else:
            base[k] = v
    return base


def _save(cfg: dict) -> None:
    write_json(_config_path(), cfg)


# ---- public API ----


def get_full_config() -> dict:
    return _read()


def get_toggles() -> dict:
    return _read()["toggles"]


def update_toggles(patch: dict) -> dict:
    cfg = _read()
    cfg["toggles"].update({k: bool(v) for k, v in patch.items() if k in cfg["toggles"]})
    _save(cfg)
    return cfg["toggles"]


def get_system_params() -> dict:
    return _read()["system_params"]


def update_system_params(patch: dict) -> dict:
    cfg = _read()
    for k in cfg["system_params"]:
        if k in patch:
            cfg["system_params"][k] = patch[k]
    _save(cfg)
    return cfg["system_params"]


def reset_system_params() -> dict:
    cfg = _read()
    cfg["system_params"] = _deep_copy(DEFAULTS["system_params"])
    _save(cfg)
    return cfg["system_params"]


# ---- LLM models / pricing ----


def get_llm_config() -> dict:
    cfg = _read()
    return {
        "budget_monthly_usd": cfg["llm"]["budget_monthly_usd"],
        "budget_alert_threshold": cfg["llm"]["budget_alert_threshold"],
        "models": cfg["llm"]["models"],
    }


def update_llm_budget(*, budget_monthly_usd: float, budget_alert_threshold: float) -> dict:
    if budget_monthly_usd < 0:
        raise APIError(400, ErrorCode.VALIDATION_ERROR, "预算不能为负")
    if not 0 < budget_alert_threshold <= 1:
        raise APIError(400, ErrorCode.VALIDATION_ERROR, "告警阈值必须在 (0,1] 之间")
    cfg = _read()
    cfg["llm"]["budget_monthly_usd"] = float(budget_monthly_usd)
    cfg["llm"]["budget_alert_threshold"] = float(budget_alert_threshold)
    _save(cfg)
    return cfg["llm"]


def update_llm_model(model_id: str, patch: dict) -> dict:
    cfg = _read()
    found = False
    for m in cfg["llm"]["models"]:
        if m["id"] == model_id:
            for k in ("label", "input_unit_price", "output_unit_price", "enabled"):
                if k in patch:
                    m[k] = patch[k]
            found = True
            break
    if not found:
        # treat as upsert
        cfg["llm"]["models"].append(
            {
                "id": model_id,
                "label": patch.get("label", model_id),
                "input_unit_price": float(patch.get("input_unit_price", 0)),
                "output_unit_price": float(patch.get("output_unit_price", 0)),
                "enabled": bool(patch.get("enabled", True)),
            }
        )
    _save(cfg)
    return next(m for m in cfg["llm"]["models"] if m["id"] == model_id)


def get_model_pricing(model_id: str) -> tuple[float, float]:
    """Return (input_unit_price, output_unit_price) per 1M tokens."""
    cfg = _read()
    for m in cfg["llm"]["models"]:
        if m["id"] == model_id:
            return float(m["input_unit_price"]), float(m["output_unit_price"])
    return 0.0, 0.0


# ---- announcements ----


def list_announcements() -> list[dict]:
    cfg = _read()
    items = list(cfg.get("announcements") or [])
    items.sort(key=lambda a: a.get("created_at") or "", reverse=True)
    return items


def create_announcement(*, title: str, body: str, level: str, audience_scope: str, status: str) -> dict:
    if level not in {"info", "warning", "error"}:
        raise APIError(400, ErrorCode.VALIDATION_ERROR, "level 非法")
    cfg = _read()
    rec = {
        "id": uuid.uuid4().hex,
        "title": title,
        "body": body,
        "level": level,
        "audience_scope": audience_scope or "all",
        "status": status or "draft",
        "published_at": _now() if status == "published" else None,
        "created_at": _now(),
        "updated_at": _now(),
    }
    cfg.setdefault("announcements", []).append(rec)
    _save(cfg)
    return rec


def update_announcement(ann_id: str, patch: dict) -> dict:
    cfg = _read()
    items = cfg.get("announcements") or []
    for a in items:
        if a["id"] == ann_id:
            for k in ("title", "body", "level", "audience_scope", "status"):
                if k in patch:
                    a[k] = patch[k]
            if patch.get("status") == "published" and not a.get("published_at"):
                a["published_at"] = _now()
            a["updated_at"] = _now()
            cfg["announcements"] = items
            _save(cfg)
            return a
    raise APIError(404, ErrorCode.RESOURCE_NOT_FOUND, "公告不存在")


def delete_announcement(ann_id: str) -> None:
    cfg = _read()
    items = [a for a in (cfg.get("announcements") or []) if a["id"] != ann_id]
    cfg["announcements"] = items
    _save(cfg)


def list_active_announcements() -> list[dict]:
    return [a for a in list_announcements() if a.get("status") == "published"]
