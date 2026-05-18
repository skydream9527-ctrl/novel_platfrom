"""Knowledge bases (D54-D58 / D119).

Source of truth: .cache/knowledge-bases.json (admin-only configuration).
Sync with feishu / mify happens via background scheduler; logs in
.cache/kb_sync_logs/{kb_id}.jsonl.

When external creds (FEISHU/MIFY) are missing, sync returns KB_SYNC_FAILED.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from pathlib import Path

import httpx

from ..core.config import get_settings
from ..core.errors import APIError, ErrorCode
from ..core.storage import append_jsonl, get_paths, read_json, read_jsonl, write_json


def _now() -> str:
    return datetime.now(tz=timezone.utc).isoformat()


def _kb_config_path() -> Path:
    return get_paths().cache / "knowledge-bases.json"


def _kb_sync_log_path(kb_id: str) -> Path:
    return get_paths().cache / "kb_sync_logs" / f"{kb_id}.jsonl"


def list_kbs() -> list[dict]:
    items = read_json(_kb_config_path(), default=[]) or []
    items.sort(key=lambda x: x.get("created_at") or "", reverse=False)
    return items


def get_kb(kb_id: str) -> dict | None:
    for k in list_kbs():
        if k["id"] == kb_id:
            return k
    return None


def create_kb(body: dict) -> dict:
    source_type = body.get("source_type")
    if source_type not in {"feishu_wiki", "mify_rag"}:
        raise APIError(400, ErrorCode.VALIDATION_ERROR, "source_type 必须为 feishu_wiki 或 mify_rag")
    rec = {
        "id": uuid.uuid4().hex,
        "name": body.get("name") or "未命名知识库",
        "description": body.get("description"),
        "source_type": source_type,
        "config": body.get("config") or {},  # space_id / dataset_id 等
        "sync_frequency": body.get("sync_frequency", "daily"),  # manual / hourly / daily / weekly
        "visibility": body.get("visibility", "all"),
        "status": "idle",
        "last_sync_at": None,
        "last_sync_summary": None,
        "doc_count": 0,
        "enabled": body.get("enabled", True),
        "created_at": _now(),
        "updated_at": _now(),
    }
    items = list_kbs()
    items.append(rec)
    write_json(_kb_config_path(), items)
    return rec


def update_kb(kb_id: str, patch: dict) -> dict:
    items = list_kbs()
    for k in items:
        if k["id"] == kb_id:
            for field in (
                "name",
                "description",
                "config",
                "sync_frequency",
                "visibility",
                "enabled",
            ):
                if field in patch:
                    k[field] = patch[field]
            k["updated_at"] = _now()
            write_json(_kb_config_path(), items)
            return k
    raise APIError(404, ErrorCode.RESOURCE_NOT_FOUND, "知识库不存在")


def delete_kb(kb_id: str) -> None:
    items = [k for k in list_kbs() if k["id"] != kb_id]
    write_json(_kb_config_path(), items)


def list_sync_logs(kb_id: str, limit: int = 50) -> list[dict]:
    rows = read_jsonl(_kb_sync_log_path(kb_id))
    return rows[-limit:][::-1]


async def test_connection(kb_id: str) -> dict:
    s = get_settings()
    kb = get_kb(kb_id)
    if not kb:
        raise APIError(404, ErrorCode.RESOURCE_NOT_FOUND, "知识库不存在")
    if kb["source_type"] == "feishu_wiki":
        if not s.feishu_enabled:
            return {"ok": False, "error_code": ErrorCode.FEISHU_NOT_CONFIGURED, "message": "飞书未配置"}
        return {"ok": True, "message": "飞书凭证已配置（实际接口连通性见 sync）"}
    if kb["source_type"] == "mify_rag":
        return {"ok": False, "error_code": "MIFY_NOT_CONFIGURED", "message": "Mify RAG 集成未实现（MVP 阶段）"}
    return {"ok": False, "error_code": "UNKNOWN", "message": "未知 source_type"}


async def sync_kb(kb_id: str, *, trigger: str = "manual") -> dict:
    """Sync once. Append a record to .cache/kb_sync_logs/{kb}.jsonl."""
    kb = get_kb(kb_id)
    if not kb:
        raise APIError(404, ErrorCode.RESOURCE_NOT_FOUND, "知识库不存在")
    started = _now()
    log: dict = {
        "id": uuid.uuid4().hex,
        "kb_id": kb_id,
        "trigger": trigger,
        "started_at": started,
        "ended_at": None,
        "status": "running",
        "added": 0,
        "updated": 0,
        "failed": 0,
        "error": None,
    }
    try:
        if kb["source_type"] == "feishu_wiki":
            res = await _sync_feishu(kb)
        elif kb["source_type"] == "mify_rag":
            res = await _sync_mify(kb)
        else:
            raise APIError(400, ErrorCode.VALIDATION_ERROR, "未知 source_type")
        log.update(res)
        log["status"] = "success"
    except APIError as e:
        log["status"] = "failed"
        log["error"] = {"code": e.error_code, "message": e.message}
    except Exception as e:
        log["status"] = "failed"
        log["error"] = {"code": ErrorCode.KB_SYNC_FAILED, "message": str(e)[:500]}
    log["ended_at"] = _now()
    append_jsonl(_kb_sync_log_path(kb_id), log)
    # update KB last sync
    items = list_kbs()
    for k in items:
        if k["id"] == kb_id:
            k["last_sync_at"] = log["ended_at"]
            k["last_sync_summary"] = {
                "status": log["status"],
                "added": log["added"],
                "updated": log["updated"],
                "failed": log["failed"],
            }
            k["status"] = "idle"
            if log["status"] == "success":
                k["doc_count"] = log["added"] + log["updated"] + (k.get("doc_count") or 0)
            break
    write_json(_kb_config_path(), items)
    return log


async def _sync_feishu(kb: dict) -> dict:
    """Real feishu sync. Requires FEISHU_APP_ID/SECRET + space_id in config.

    Returns counts. Raises APIError when creds missing.
    """
    s = get_settings()
    if not s.feishu_enabled:
        raise APIError(503, ErrorCode.KB_SYNC_FAILED, "飞书未配置")
    space_id = (kb.get("config") or {}).get("space_id")
    if not space_id:
        raise APIError(400, ErrorCode.VALIDATION_ERROR, "config.space_id 必填")
    async with httpx.AsyncClient(timeout=20) as cli:
        r = await cli.post(
            "https://open.feishu.cn/open-apis/auth/v3/app_access_token/internal",
            json={"app_id": s.FEISHU_APP_ID, "app_secret": s.FEISHU_APP_SECRET},
        )
        r.raise_for_status()
        token = r.json().get("app_access_token")
        if not token:
            raise APIError(502, ErrorCode.KB_SYNC_FAILED, "飞书 token 获取失败")
        nodes_resp = await cli.get(
            f"https://open.feishu.cn/open-apis/wiki/v2/spaces/{space_id}/nodes",
            headers={"Authorization": f"Bearer {token}"},
            params={"page_size": 50},
        )
        if nodes_resp.status_code != 200:
            raise APIError(502, ErrorCode.KB_SYNC_FAILED, f"飞书 wiki 拉取失败 ({nodes_resp.status_code})")
        items = nodes_resp.json().get("data", {}).get("items", []) or []
    return {"added": len(items), "updated": 0, "failed": 0}


async def _sync_mify(kb: dict) -> dict:
    raise APIError(503, "MIFY_NOT_CONFIGURED", "Mify RAG 集成未实现（MVP 阶段）")
