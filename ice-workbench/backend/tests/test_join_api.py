from __future__ import annotations

import pytest
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.core import deps
from app.core.storage import get_index_db, get_paths, write_json
from app.services import public_task_svc, task_svc


@pytest.fixture
async def published_task(isolated_data_root):
    paths = get_paths()
    (paths.users / "u1").mkdir()
    write_json(paths.users / "u1" / "tasks.json", [])
    (paths.agents / "a1" / "prompt").mkdir(parents=True)
    paths.agent_prompt_system_md("a1").write_text("s")
    paths.agent_prompt_cards_md("a1").write_text("c")
    write_json(paths.agent_json("a1"), {"id": "a1"})
    # IMPORTANT: init sqlite index (required by task_svc.create_task)
    db = get_index_db()
    await db.init()
    t = await task_svc.create_task(
        name="T", paradigm="data", owner_id="u1", agent_id="a1",
        description=None, initial_prompt=None, skill_ids=[], visibility="private",
    )
    await public_task_svc.share_task(task_id=t["id"], owner_id="u1")
    return t["id"]


@pytest.mark.asyncio
async def test_viewer_can_submit_owner_can_approve(published_task):
    tid = published_task

    async def viewer_user():
        return {"id": "u-asker", "is_admin": False}
    app.dependency_overrides[deps.get_current_user] = viewer_user

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        r = await ac.post(f"/api/v1/tasks/{tid}/join-request", json={"message": "plz"})
        assert r.status_code == 200
        rid = r.json()["data"]["id"]

    async def owner_user():
        return {"id": "u1", "is_admin": False}
    app.dependency_overrides[deps.get_current_user] = owner_user

    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        r = await ac.post(
            f"/api/v1/tasks/{tid}/join-requests/{rid}/review",
            json={"status": "approved"},
        )
        assert r.status_code == 200
        assert r.json()["data"]["status"] == "approved"

    app.dependency_overrides.clear()
