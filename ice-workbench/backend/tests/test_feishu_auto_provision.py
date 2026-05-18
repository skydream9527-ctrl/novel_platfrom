"""Test the auto-provision branch of feishu_login."""
from __future__ import annotations

import pytest

from app.seed.runner import bootstrap


@pytest.mark.asyncio
async def test_feishu_auto_provision_creates_user(isolated_data_root):
    await bootstrap()

    from app.core.storage import get_index_db
    from app.services import auth_svc, sysconfig_svc

    # Default toggle is True — auto-register on
    assert sysconfig_svc.get_toggles().get("enable_feishu_auto_register") is True

    db = get_index_db()
    rows = await db.fetchall("SELECT email FROM users_index")
    before = {r["email"] for r in rows}
    assert "newbie@example.com" not in before

    result = await auth_svc.feishu_login(
        feishu_user_id="ou_aaa111",
        email="newbie@example.com",
        name="新用户",
        avatar_url="https://example.com/a.png",
    )
    assert result["user"]["email"] == "newbie@example.com"
    assert result["user"]["auth_role"] == "user"
    assert result["user"]["feishu_bound"] is True
    assert result["tokens"]["access_token"]

    # second login = same account, no dup
    result2 = await auth_svc.feishu_login(
        feishu_user_id="ou_aaa111", email="newbie@example.com", name="新用户"
    )
    assert result2["user"]["id"] == result["user"]["id"]


@pytest.mark.asyncio
async def test_feishu_auto_provision_disabled_returns_403(isolated_data_root):
    await bootstrap()

    from app.core.errors import APIError, ErrorCode
    from app.services import auth_svc, sysconfig_svc

    sysconfig_svc.update_toggles({"enable_feishu_auto_register": False})

    with pytest.raises(APIError) as exc:
        await auth_svc.feishu_login(
            feishu_user_id="ou_zzz999",
            email="stranger@example.com",
            name="陌生人",
        )
    assert exc.value.error_code == ErrorCode.FEISHU_ACCOUNT_NOT_WHITELISTED


@pytest.mark.asyncio
async def test_feishu_auto_binds_existing_user(isolated_data_root):
    await bootstrap()

    from app.services import auth_svc

    # admin already exists from seed; binding feishu to admin should succeed.
    result = await auth_svc.feishu_login(
        feishu_user_id="ou_admin",
        email="admin",
        name="系统管理员",
    )
    assert result["user"]["email"] == "admin"
    assert result["user"]["feishu_bound"] is True


@pytest.mark.asyncio
async def test_feishu_no_email_uses_synthetic_handle(isolated_data_root):
    """Email scope might not be granted by Feishu — auto-provision should
    still build a usable account using the feishu_user_id."""
    await bootstrap()
    from app.services import auth_svc

    result = await auth_svc.feishu_login(
        feishu_user_id="ou_no_email_777",
        email=None,
        name="无邮箱同学",
    )
    assert result["user"]["email"].startswith("feishu-ou_no_email_")
    assert result["user"]["name"] == "无邮箱同学"
