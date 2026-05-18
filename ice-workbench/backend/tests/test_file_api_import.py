from __future__ import annotations

import pytest
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.core import deps
from app.core.storage import get_index_db, get_paths, write_json
from app.services import task_svc


@pytest.mark.asyncio
async def test_import_endpoint_happy(isolated_data_root, monkeypatch):
    paths = get_paths()
    (paths.agents / "a1" / "prompt").mkdir(parents=True)
    paths.agent_prompt_system_md("a1").write_text("s")
    paths.agent_prompt_cards_md("a1").write_text("c")
    write_json(paths.agent_json("a1"), {"id": "a1"})
    (paths.users / "u1").mkdir()
    write_json(paths.users / "u1" / "tasks.json", [])
    # IMPORTANT: init sqlite index (required by task_svc.create_task)
    db = get_index_db()
    await db.init()
    t = await task_svc.create_task(
        name="T", paradigm="data", owner_id="u1", agent_id="a1",
        description=None, initial_prompt=None, skill_ids=[], visibility="private",
    )

    async def fake_fetch(**kwargs):
        return ("Doc", "hello body")
    monkeypatch.setattr("app.services.feishu_import_svc.fetch_document", fake_fetch)
    monkeypatch.setattr(
        "app.services.feishu_import_svc.parse_feishu_url",
        lambda url: {"obj_type": "docx", "obj_token": "X"},
    )

    async def fake_user():
        return {"id": "u1", "is_admin": False}
    app.dependency_overrides[deps.get_current_user] = fake_user

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        r = await ac.post(
            "/api/v1/files/import",
            data={
                "task_id": t["id"],
                "source_type": "feishu_doc",
                "source_url": "https://acme.feishu.cn/docx/X",
            },
        )
        assert r.status_code == 200, r.text
        assert r.json()["data"]["scope"] == "imported"

    app.dependency_overrides.clear()
