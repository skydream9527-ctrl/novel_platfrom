from __future__ import annotations

import pytest

from app.core.storage import get_paths, read_json, write_json
from app.services import public_task_svc, task_svc


@pytest.fixture
async def shared_task(isolated_data_root):
    paths = get_paths()
    (paths.agents / "a1" / "prompt").mkdir(parents=True)
    paths.agent_prompt_system_md("a1").write_text("SYS")
    paths.agent_prompt_cards_md("a1").write_text("CARDS")
    write_json(paths.agent_json("a1"), {"id": "a1"})
    (paths.users / "u1").mkdir()
    write_json(paths.users / "u1" / "tasks.json", [])
    from app.core.storage import get_index_db
    db = get_index_db()
    await db.init()
    t = await task_svc.create_task(
        name="T", paradigm="data", owner_id="u1", agent_id="a1",
        description=None, initial_prompt=None, skill_ids=[], visibility="private",
    )
    await public_task_svc.share_task(task_id=t["id"], owner_id="u1")
    # seed a pending join request
    write_json(paths.task_join_requests(t["id"]), [
        {"id": "r1", "user_id": "u-asker", "message": "in", "status": "pending",
         "created_at": "2026-05-12T00:00:00+00:00"},
    ])
    return paths, t["id"]


@pytest.mark.asyncio
async def test_unshare_thaws_and_rejects_joins(shared_task):
    paths, tid = shared_task
    await public_task_svc.unshare_task(task_id=tid, owner_id="u1")

    snap = read_json(paths.task_snapshot(tid))
    assert snap["mode"] == "live"

    jr = read_json(paths.task_join_requests(tid))
    assert jr[0]["status"] == "rejected"
    assert jr[0]["reviewed_by"] == "u1"
    assert jr[0].get("reject_reason") == "task_unshared"

    meta = read_json(paths.task_meta(tid))
    assert meta["visibility"] == "private"
