from __future__ import annotations

import pytest

from app.core.storage import get_paths, read_json, write_json
from app.services import public_task_svc, task_svc


@pytest.fixture
async def task_with_snapshot(isolated_data_root):
    paths = get_paths()
    (paths.agents / "a1" / "prompt").mkdir(parents=True)
    paths.agent_prompt_system_md("a1").write_text("SYS-v1")
    paths.agent_prompt_cards_md("a1").write_text("CARDS-v1")
    write_json(paths.agent_json("a1"), {"id": "a1"})
    (paths.users / "u1").mkdir()
    write_json(paths.users / "u1" / "tasks.json", [])
    # IMPORTANT: init sqlite index (required by task_svc.create_task)
    from app.core.storage import get_index_db
    db = get_index_db()
    await db.init()
    t = await task_svc.create_task(
        name="T", paradigm="data", owner_id="u1", agent_id="a1",
        description=None, initial_prompt=None, skill_ids=[], visibility="private",
    )
    return paths, t["id"]


@pytest.mark.asyncio
async def test_share_task_freezes_snapshot(task_with_snapshot):
    paths, tid = task_with_snapshot
    # simulate cards update happening just before share
    paths.agent_prompt_cards_md("a1").write_text("CARDS-v2")
    await public_task_svc.share_task(task_id=tid, owner_id="u1")

    snap = read_json(paths.task_snapshot(tid))
    assert snap["mode"] == "frozen"
    assert snap["frozen_at"] is not None
    assert snap["frozen_by"] == "u1"
    # snapshot's cards.md was refreshed to v2 at freeze moment
    assert paths.task_agent_cards_md(tid).read_text() == "CARDS-v2"


@pytest.mark.asyncio
async def test_share_task_requires_owner(task_with_snapshot):
    paths, tid = task_with_snapshot
    from app.core.errors import APIError
    with pytest.raises(APIError):
        await public_task_svc.share_task(task_id=tid, owner_id="some-other-user")
