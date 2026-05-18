from __future__ import annotations

import pytest

from app.core.storage import get_paths, read_json, write_json
from app.services import public_task_svc, task_svc


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
async def test_flag_false_when_private(isolated_data_root):
    paths = get_paths()
    (paths.agents / "a1" / "prompt").mkdir(parents=True)
    paths.agent_prompt_system_md("a1").write_text("SYS")
    paths.agent_prompt_cards_md("a1").write_text("CARDS")
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
    paths.agent_prompt_cards_md("a1").write_text("CARDS-v2")  # source drifts
    detail = await task_svc.get_task(t["id"], "u1")
    assert detail["agent_update_available"] is False


@pytest.mark.asyncio
async def test_flag_true_when_public_and_source_drifted(public_task):
    paths, tid = public_task
    paths.agent_prompt_cards_md("a1").write_text("CARDS-v2")
    detail = await task_svc.get_task(tid, "u1")
    assert detail["agent_update_available"] is True


@pytest.mark.asyncio
async def test_flag_false_when_source_missing(public_task):
    paths, tid = public_task
    paths.agent_prompt_cards_md("a1").unlink()
    paths.agent_prompt_system_md("a1").unlink()
    detail = await task_svc.get_task(tid, "u1")
    assert detail["agent_update_available"] is False


@pytest.mark.asyncio
async def test_flag_false_when_in_sync(public_task):
    _, tid = public_task
    detail = await task_svc.get_task(tid, "u1")
    assert detail["agent_update_available"] is False
