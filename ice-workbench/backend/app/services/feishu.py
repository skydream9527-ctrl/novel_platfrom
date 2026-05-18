"""Feishu OAuth integration. Returns FEISHU_NOT_CONFIGURED when creds missing.

Endpoints follow the standard open.feishu.cn paths but the host is configurable
via FEISHU_HOST (so a Xiaomi-internal Lark variant on a different domain works
without code changes — only env tweak).
"""
from __future__ import annotations

import secrets
from urllib.parse import urlencode

import httpx

from ..core.config import get_settings
from ..core.errors import APIError, ErrorCode


def _host() -> str:
    return get_settings().FEISHU_HOST.rstrip("/") or "https://open.feishu.cn"


def _auth_url() -> str:
    return _host() + "/open-apis/authen/v1/index"


def _app_token_url() -> str:
    return _host() + "/open-apis/auth/v3/app_access_token/internal"


def _user_token_url() -> str:
    return _host() + "/open-apis/authen/v1/access_token"


def _user_info_url() -> str:
    return _host() + "/open-apis/authen/v1/user_info"


def assert_configured() -> None:
    s = get_settings()
    if not s.feishu_enabled:
        raise APIError(
            503,
            ErrorCode.FEISHU_NOT_CONFIGURED,
            "飞书未配置：需要在 .env 填写 FEISHU_APP_ID + FEISHU_APP_SECRET",
        )


def build_authorize_url() -> tuple[str, str]:
    """Compose the Feishu authorize URL the SPA should redirect the user to."""
    assert_configured()
    s = get_settings()
    state = secrets.token_urlsafe(16)
    qs = urlencode(
        {
            "app_id": s.FEISHU_APP_ID,
            "redirect_uri": s.FEISHU_REDIRECT_URI,
            "state": state,
            "scope": "contact:user.id contact:user.base contact:user.email",
        }
    )
    return f"{_auth_url()}?{qs}", state


async def exchange_code(code: str) -> dict:
    """Authorization code → user_access_token → user_info.

    Returns a normalized dict with `feishu_user_id`, `email`, `name`,
    `avatar_url` (any of which may be None depending on granted scopes).
    """
    assert_configured()
    s = get_settings()
    async with httpx.AsyncClient(timeout=15) as cli:
        # 1. App access token
        r = await cli.post(
            _app_token_url(),
            json={"app_id": s.FEISHU_APP_ID, "app_secret": s.FEISHU_APP_SECRET},
        )
        r.raise_for_status()
        app_token = r.json().get("app_access_token")
        if not app_token:
            raise APIError(502, "FEISHU_TOKEN_FAILED", "飞书 app_access_token 获取失败")

        # 2. Code → user access token
        r2 = await cli.post(
            _user_token_url(),
            json={"grant_type": "authorization_code", "code": code},
            headers={"Authorization": f"Bearer {app_token}"},
        )
        r2.raise_for_status()
        data = r2.json().get("data") or {}
        user_token = data.get("access_token")
        if not user_token:
            raise APIError(502, "FEISHU_TOKEN_FAILED", "飞书 user_access_token 获取失败")

        # 3. User info
        r3 = await cli.get(_user_info_url(), headers={"Authorization": f"Bearer {user_token}"})
        r3.raise_for_status()
        info = r3.json().get("data") or {}

    feishu_user_id = info.get("user_id") or info.get("open_id") or info.get("union_id")
    if not feishu_user_id:
        raise APIError(502, "FEISHU_TOKEN_FAILED", "飞书未返回用户身份")

    return {
        "feishu_user_id": feishu_user_id,
        "email": info.get("enterprise_email") or info.get("email"),
        "name": info.get("name"),
        "avatar_url": info.get("avatar_url") or info.get("avatar_thumb"),
        "mobile": info.get("mobile"),
    }
