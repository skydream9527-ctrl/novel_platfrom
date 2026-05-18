from __future__ import annotations

import pytest

from app.core.storage import get_index_db, get_paths, read_json, write_json
from app.services import task_svc


@pytest.fixture
async def agent_and_user(isolated_data_root):
    db = get_index_db()
    await db.init()
    paths = get_paths()
    (paths.agents / "a1" / "prompt").mkdir(parents=True)
    (paths.agents / "a1" / "prompt" / "system.md").write_text("you are a1")
    (paths.agents / "a1" / "prompt" / "cards.md").write_text("rule1")
    write_json(paths.agent_json("a1"), {"id": "a1", "name": "A1"})
    (paths.users / "u1").mkdir(parents=True)
    write_json(paths.users / "u1" / "tasks.json", [])
    return paths


@pytest.mark.asyncio
async def test_create_task_snapshots_agent(agent_and_user):
    paths = agent_and_user
    t = await task_svc.create_task(
        name="T", paradigm="data", owner_id="u1", agent_id="a1",
        description=None, initial_prompt=None, skill_ids=[], visibility="private",
    )
    tid = t["id"]
    assert paths.task_agent_system_md(tid).read_text() == "you are a1"
    assert paths.task_agent_cards_md(tid).read_text() == "rule1"
    assert paths.task_agent_json(tid).exists()
    snap = read_json(paths.task_snapshot(tid))
    assert snap["mode"] == "live"
    assert snap["agent_source_version"] is not None
    assert len(snap["agent_source_version"]) == 64
    assert snap["frozen_at"] is None


@pytest.mark.asyncio
async def test_create_task_without_agent_has_null_version(agent_and_user):
    paths = agent_and_user
    t = await task_svc.create_task(
        name="T", paradigm="general", owner_id="u1", agent_id=None,
        description=None, initial_prompt=None, skill_ids=[], visibility="private",
    )
    snap = read_json(paths.task_snapshot(t["id"]))
    assert snap["mode"] == "live"
    assert snap["agent_source_version"] is None


@pytest.mark.asyncio
async def test_create_task_writes_skill_index(agent_and_user):
    paths = agent_and_user
    (paths.skills / "helper").mkdir(parents=True)
    (paths.skills / "helper" / "SKILL.md").write_text(
        "---\nname: helper\ndescription: h\n---\nbody"
    )
    t = await task_svc.create_task(
        name="T", paradigm="data", owner_id="u1", agent_id="a1",
        description=None, initial_prompt=None, skill_ids=["helper"], visibility="private",
    )
    idx = read_json(paths.task_skills_index(t["id"]))
    assert [x["id"] for x in idx] == ["helper"]
