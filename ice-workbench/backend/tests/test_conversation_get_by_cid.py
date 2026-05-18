from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from app.core import deps
from app.core.storage import get_paths, write_json
from app.main import app
from app.services import conversation_svc, task_svc


@pytest.mark.asyncio
async def test_get_conversation_by_cid_returns_messages(isolated_data_root):
    paths = get_paths()
    (paths.users / "u1").mkdir()
    write_json(paths.users / "u1" / "tasks.json", [])
    (paths.agents / "a1" / "prompt").mkdir(parents=True)
    paths.agent_prompt_system_md("a1").write_text("s")
    paths.agent_prompt_cards_md("a1").write_text("c")
    write_json(paths.agent_json("a1"), {"id": "a1"})
    from app.core.storage import get_index_db

    db = get_index_db()
    await db.init()
    t = await task_svc.create_task(
        name="T", paradigm="data", owner_id="u1", agent_id="a1",
        description=None, initial_prompt=None, skill_ids=[], visibility="private",
    )
    # Create conv + write one message
    conv = await conversation_svc.create_conversation(task_id=t["id"], created_by="u1", title="c1")
    jsonl = paths.task_conversation(t["id"], conv["id"])
    jsonl.parent.mkdir(parents=True, exist_ok=True)
    import json
    jsonl.write_text(json.dumps({"id": "m1", "role": "user", "content": "hi"}) + "\n")

    async def fake_user():
        return {"id": "u1", "is_admin": False}

    app.dependency_overrides[deps.get_current_user] = fake_user
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            r = await ac.get(f"/api/v1/tasks/{t['id']}/conversations/{conv['id']}")
            assert r.status_code == 200, r.text
            body = r.json()["data"]
            assert body["conversation_id"] == conv["id"]
            assert len(body["messages"]) == 1
            assert body["messages"][0]["content"] == "hi"

        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            r = await ac.get(f"/api/v1/tasks/{t['id']}/conversations/nonexistent")
            assert r.status_code == 404
    finally:
        app.dependency_overrides.clear()
