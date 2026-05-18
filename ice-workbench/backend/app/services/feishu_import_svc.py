"""Feishu document import. Reuses tenant_access_token from services/feishu.py.

Scope: docx + wiki. URL host MUST end with `.feishu.cn` under `https` (SSRF
defense). No configuration override — the whitelist is hard-coded.
"""
from __future__ import annotations

from urllib.parse import urlparse

from ..core.errors import APIError, ErrorCode

SUPPORTED_OBJECTS = {"docx", "wiki"}


def parse_feishu_url(url: str) -> dict:
    """Validate host + scheme, extract {obj_type, obj_token}."""
    p = urlparse(url)
    if p.scheme != "https":
        raise APIError(400, ErrorCode.IMPORT_SOURCE_NOT_SUPPORTED, "仅支持 https")
    host = (p.hostname or "").lower()
    if not host.endswith(".feishu.cn") or host == ".feishu.cn":
        raise APIError(400, ErrorCode.IMPORT_SOURCE_NOT_SUPPORTED, "仅支持 *.feishu.cn 域名")
    # Path like /docx/<token> or /wiki/<token>
    parts = [x for x in p.path.split("/") if x]
    if len(parts) < 2:
        raise APIError(400, ErrorCode.IMPORT_SOURCE_NOT_SUPPORTED, "URL 格式不符")
    obj_type, obj_token = parts[0], parts[1]
    if obj_type not in SUPPORTED_OBJECTS:
        raise APIError(400, ErrorCode.IMPORT_SOURCE_NOT_SUPPORTED, f"不支持的对象类型 {obj_type}")
    return {"obj_type": obj_type, "obj_token": obj_token}


async def fetch_document(*, obj_type: str, obj_token: str) -> tuple[str, str]:
    """Return (title, body_markdown). Raises IMPORT_FETCH_FAILED / FEISHU_DISABLED."""
    from ..core.config import get_settings
    s = get_settings()
    if not getattr(s, "feishu_enabled", False):
        raise APIError(503, ErrorCode.FEISHU_DISABLED, "飞书集成未启用")

    from . import feishu as feishu_svc  # existing tenant token provider

    token = await feishu_svc.get_tenant_access_token()
    import httpx

    headers = {"Authorization": f"Bearer {token}"}
    timeout = httpx.Timeout(30.0)
    async with httpx.AsyncClient(timeout=timeout) as client:
        if obj_type == "wiki":
            # wiki → resolve to docx obj_token first
            r = await client.get(
                f"https://open.feishu.cn/open-apis/wiki/v2/spaces/get_node",
                params={"token": obj_token},
                headers=headers,
            )
            if r.status_code == 403:
                raise APIError(403, ErrorCode.IMPORT_SOURCE_NOT_ACCESSIBLE, "飞书文档不可访问")
            if r.status_code >= 400:
                raise APIError(502, ErrorCode.IMPORT_FETCH_FAILED, f"wiki resolve failed {r.status_code}")
            node = (r.json().get("data") or {}).get("node") or {}
            obj_token = node.get("obj_token") or obj_token
            obj_type = node.get("obj_type") or "docx"

        r = await client.get(
            f"https://open.feishu.cn/open-apis/docx/v1/documents/{obj_token}/raw_content",
            headers=headers,
        )
        if r.status_code == 403:
            raise APIError(403, ErrorCode.IMPORT_SOURCE_NOT_ACCESSIBLE, "飞书文档不可访问")
        if r.status_code >= 400:
            raise APIError(502, ErrorCode.IMPORT_FETCH_FAILED, f"fetch failed {r.status_code}")
        data = r.json().get("data") or {}
        body = data.get("content") or ""

        # separately fetch title (optional best-effort)
        title = obj_token
        tr = await client.get(
            f"https://open.feishu.cn/open-apis/docx/v1/documents/{obj_token}",
            headers=headers,
        )
        if tr.status_code == 200:
            td = (tr.json().get("data") or {}).get("document") or {}
            title = td.get("title") or title

    return title, body
