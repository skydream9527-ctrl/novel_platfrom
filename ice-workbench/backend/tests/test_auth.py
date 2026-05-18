from __future__ import annotations

import pytest

from app.seed.runner import bootstrap
from app.services import auth_svc


@pytest.mark.asyncio
async def test_password_login_success(isolated_data_root):
    await bootstrap()
    result = await auth_svc.password_login("admin", "admin123")
    assert result["user"]["auth_role"] == "super_admin"
    assert result["tokens"]["access_token"]


@pytest.mark.asyncio
async def test_password_login_wrong(isolated_data_root):
    await bootstrap()
    from app.core.errors import APIError

    with pytest.raises(APIError) as exc:
        await auth_svc.password_login("admin", "nope")
    assert exc.value.error_code == "INVALID_CREDENTIALS"
