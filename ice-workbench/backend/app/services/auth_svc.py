"""Auth service. Source of truth = users/{uid}/profile.json; index in cache."""
from __future__ import annotations

from datetime import datetime, timezone

from ..core.config import get_settings
from ..core.errors import APIError, ErrorCode
from ..core.security import create_access_token, create_refresh_token, verify_password
from ..core.storage import file_transaction, get_index_db, get_paths, read_json


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


async def load_user_by_id(user_id: str) -> dict | None:
    p = get_paths().user_profile(user_id)
    return read_json(p) or None


async def load_user_by_email(email: str) -> dict | None:
    db = get_index_db()
    row = await db.fetchone(
        "SELECT id FROM users_index WHERE email = ? COLLATE NOCASE LIMIT 1", [email]
    )
    if not row:
        return None
    return await load_user_by_id(row["id"])


async def password_login(email: str, password: str) -> dict:
    """Password login. super_admin gate per D85.

    super_admin must use Feishu IF feishu is configured AND the user is already bound.
    Bootstrap escape: when FEISHU not configured globally, password login is allowed
    so the platform can be operated without external IdP.
    """
    s = get_settings()
    user = await load_user_by_email(email)
    if not user:
        raise APIError(401, ErrorCode.INVALID_CREDENTIALS, "账号或密码错误")
    if user.get("status") == "disabled":
        raise APIError(403, ErrorCode.ACCOUNT_DISABLED, "账号已被禁用")
    if user["auth_role"] == "super_admin" and s.feishu_enabled and user.get("feishu_user_id"):
        raise APIError(403, ErrorCode.SUPER_ADMIN_REQUIRES_FEISHU, "super_admin 必须使用飞书登录")
    if not verify_password(password, user.get("password_hash")):
        raise APIError(401, ErrorCode.INVALID_CREDENTIALS, "账号或密码错误")
    return await _issue_tokens_and_touch(user)


async def feishu_login(
    feishu_user_id: str,
    email: str | None,
    name: str | None = None,
    avatar_url: str | None = None,
) -> dict:
    """Used by /auth/feishu/oauth/callback after Feishu API verifies the code.

    Behavior:
    - existing user (matched by email or feishu_user_id) → auto-bind on first
      login + issue tokens
    - no existing user:
        toggle `enable_feishu_auto_register`=true (default) → auto-provision
            a new `auth_role=user` account, bind feishu, issue tokens
        toggle false → 403 FEISHU_ACCOUNT_NOT_WHITELISTED
    """
    user = None
    if email:
        user = await load_user_by_email(email)
    if not user:
        # try lookup by feishu_user_id (in case email scope wasn't granted)
        from ..core.storage import get_index_db as _idb

        row = await _idb().fetchone(
            "SELECT id FROM users_index WHERE feishu_user_id = ? LIMIT 1",
            [feishu_user_id],
        )
        if row:
            user = await load_user_by_id(row["id"])

    if not user:
        from . import sysconfig_svc

        if not sysconfig_svc.get_toggles().get("enable_feishu_auto_register", True):
            raise APIError(
                403,
                ErrorCode.FEISHU_ACCOUNT_NOT_WHITELISTED,
                "飞书账号未在白名单内，且自动注册已关闭。请联系管理员开启 enable_feishu_auto_register，或在 /admin/users 手动添加。",
            )
        return await _auto_provision_from_feishu(
            feishu_user_id=feishu_user_id, email=email, name=name, avatar_url=avatar_url
        )

    if user.get("feishu_user_id") and user["feishu_user_id"] != feishu_user_id:
        raise APIError(409, ErrorCode.FEISHU_BINDING_CONFLICT, "飞书账号已绑定至其他用户")
    user["feishu_user_id"] = feishu_user_id
    user["feishu_bound_at"] = _now()
    if name and not user.get("name"):
        user["name"] = name
    if avatar_url and not user.get("avatar_url"):
        user["avatar_url"] = avatar_url
    return await _issue_tokens_and_touch(user)


async def _auto_provision_from_feishu(
    *,
    feishu_user_id: str,
    email: str | None,
    name: str | None,
    avatar_url: str | None,
) -> dict:
    """Create a fresh `auth_role=user` account bound to the Feishu identity."""
    import uuid

    from ..core.security import hash_password
    from ..core.storage import get_index_db, get_paths

    paths = get_paths()
    db = get_index_db()
    uid = uuid.uuid4().hex
    # email is the public username; if scope didn't include it, synthesize a
    # feishu-suffixed handle so the system invariant (unique email) holds.
    fallback_email = email or f"feishu-{feishu_user_id[:12]}@auto.local"
    profile = {
        "id": uid,
        "email": fallback_email,
        "name": name or fallback_email.split("@")[0],
        "auth_role": "user",
        "status": "active",
        "password_hash": hash_password(uuid.uuid4().hex),  # random; cannot password-login
        "feishu_user_id": feishu_user_id,
        "feishu_bound_at": _now(),
        "team": None,
        "title": None,
        "avatar_url": avatar_url,
        "created_at": _now(),
        "last_login_at": None,
        "auto_provisioned": True,
    }
    with file_transaction([paths.user_profile(uid), paths.user_tasks_index(uid)]) as tx:
        tx.makedirs(
            [
                paths.user_dir(uid) / "tasks",
                paths.user_dir(uid) / "notifications",
                paths.user_dir(uid) / "audit",
            ]
        )
        tx.write_json(paths.user_profile(uid), profile)
        tx.write_json(paths.user_tasks_index(uid), [])
        tx.write_json(paths.user_settings(uid), {"theme": "dark"})
    await db.upsert(
        "users_index",
        {
            "id": uid,
            "email": profile["email"],
            "name": profile["name"],
            "auth_role": "user",
            "status": "active",
            "feishu_user_id": feishu_user_id,
            "last_login_at": None,
            "password_hash": profile["password_hash"],
            "created_at": profile["created_at"],
        },
    )
    return await _issue_tokens_and_touch(profile)


async def _issue_tokens_and_touch(user: dict) -> dict:
    s = get_settings()
    user["last_login_at"] = _now()
    paths = get_paths()
    with file_transaction([paths.user_profile(user["id"])]) as tx:
        tx.write_json(paths.user_profile(user["id"]), user)
    db = get_index_db()
    await db.execute(
        "UPDATE users_index SET last_login_at = ?, feishu_user_id = COALESCE(?, feishu_user_id) WHERE id = ?",
        [user["last_login_at"], user.get("feishu_user_id"), user["id"]],
    )
    return {
        "user": _to_public(user),
        "tokens": {
            "access_token": create_access_token(user["id"], user["auth_role"]),
            "refresh_token": create_refresh_token(user["id"]),
            "token_type": "bearer",
            "expires_in": s.ICE_ACCESS_TOKEN_TTL_MIN * 60,
        },
    }


def _to_public(user: dict) -> dict:
    return {
        "id": user["id"],
        "email": user.get("email", ""),
        "name": user.get("name", ""),
        "auth_role": user.get("auth_role", "user"),
        "avatar_url": user.get("avatar_url"),
        "feishu_bound": bool(user.get("feishu_user_id")),
        "team": user.get("team"),
        "title": user.get("title"),
    }
