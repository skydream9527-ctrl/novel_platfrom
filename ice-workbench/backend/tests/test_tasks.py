from __future__ import annotations

import pytest

from app.seed.runner import bootstrap
from app.services import task_svc


@pytest.mark.asyncio
async def test_create_and_list_task(isolated_data_root):
    await bootstrap()
    from app.core.storage import get_index_db

    db = get_index_db()
    row = await db.fetchone("SELECT id FROM users_index WHERE auth_role = 'super_admin'")
    uid = row["id"]
    task = await task_svc.create_task(
        name="Demo Q2 复盘", paradigm="biz", owner_id=uid, agent_id="biz-insight"
    )
    assert task["id"]
    items = await task_svc.list_user_tasks(uid)
    assert any(t["id"] == task["id"] for t in items)
    detail = await task_svc.get_task(task["id"], uid)
    assert detail["name"] == "Demo Q2 复盘"
