from __future__ import annotations

import pytest
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.core.storage import get_paths, write_json


@pytest.fixture
async def client_with_task(isolated_data_root):
    paths = get_paths()
    (paths.users / "u1").mkdir()
    write_json(paths.users / "u1" / "tasks.json", [])
    (paths.agents / "a1" / "prompt").mkdir(parents=True)
    paths.agent_prompt_system_md("a1").write_text("sys")
    paths.agent_prompt_cards_md("a1").write_text("cards")
    write_json(paths.agent_json("a1"), {"id": "a1"})

    # IMPORTANT: init sqlite index (required by task_svc.create_task)
    from app.core.storage import get_index_db
    db = get_index_db()
    await db.init()

    from app.services import task_svc
    t = await task_svc.create_task(
        name="T", paradigm="data", owner_id="u1", agent_id="a1",
        description=None, initial_prompt=None, skill_ids=[], visibility="private",
    )

    # Stub auth: patch get_current_user to return u1
    from app.core import deps
    async def fake_user():
        return {"id": "u1", "is_admin": False}
    app.dependency_overrides[deps.get_current_user] = fake_user

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac, t["id"]
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_create_and_list_conversation(client_with_task):
    ac, tid = client_with_task
    r = await ac.post(f"/api/v1/tasks/{tid}/conversations", json={"title": "hi"})
    assert r.status_code == 200
    cid = r.json()["data"]["id"]

    r2 = await ac.get(f"/api/v1/tasks/{tid}/conversations")
    assert r2.status_code == 200
    items = r2.json()["data"]["items"]
    assert any(c["id"] == cid for c in items)
