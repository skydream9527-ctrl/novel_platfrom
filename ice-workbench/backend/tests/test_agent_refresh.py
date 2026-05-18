from __future__ import annotations

import pytest

from app.core.errors import APIError, ErrorCode
from app.core.storage import get_paths, read_json, write_json
from app.services import agent_snapshot_svc, public_task_svc, task_svc


@pytest.fixture
async def public_task(isolated_data_root):
    paths = get_paths()
    (paths.agents / "a1" / "prompt").mkdir(parents=True)
    paths.agent_prompt_system_md("a1").write_text("SYS")
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
    await public_task_svc.share_task(task_id=t["id"], owner_id="u1")
    return paths, t["id"]


@pytest.mark.asyncio
async def test_refresh_updates_snapshot_and_returns_diff(public_task):
    paths, tid = public_task
    paths.agent_prompt_cards_md("a1").write_text("CARDS-v1\nCARDS-v2-add")
    res = await agent_snapshot_svc.refresh_task_snapshot(
        task_id=tid, user_id="u1", expected_version=None,
    )
    assert res["changed"] is True
    assert paths.task_agent_cards_md(tid).read_text() == "CARDS-v1\nCARDS-v2-add"
    snap = read_json(paths.task_snapshot(tid))
    assert snap["last_manual_update_by"] == "u1"
    assert snap["last_manual_update_at"] is not None


@pytest.mark.asyncio
async def test_refresh_no_change_returns_changed_false(public_task):
    _, tid = public_task
    res = await agent_snapshot_svc.refresh_task_snapshot(
        task_id=tid, user_id="u1", expected_version=None,
    )
    assert res["changed"] is False


@pytest.mark.asyncio
async def test_refresh_stale_expected_version_raises_409(public_task):
    paths, tid = public_task
    paths.agent_prompt_cards_md("a1").write_text("CARDS-v2")
    with pytest.raises(APIError) as ei:
        await agent_snapshot_svc.refresh_task_snapshot(
            task_id=tid, user_id="u1", expected_version="not-the-current-version",
        )
    assert ei.value.error_code == ErrorCode.AGENT_SNAPSHOT_STALE
