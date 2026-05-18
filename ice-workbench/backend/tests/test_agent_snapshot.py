from __future__ import annotations

import pytest

from app.core.storage import get_paths, write_json
from app.services import agent_snapshot_svc as svc


@pytest.fixture
def agent_fs(isolated_data_root):
    paths = get_paths()
    adir = paths.agents / "test-agent"
    (adir / "prompt").mkdir(parents=True)
    (adir / "prompt" / "system.md").write_text("you are a test agent")
    (adir / "prompt" / "cards.md").write_text("# card 1\nrule A\n")
    write_json(paths.agent_json("test-agent"), {"id": "test-agent", "name": "Test"})
    return paths, "test-agent"


def test_compute_version_is_stable(agent_fs):
    _, aid = agent_fs
    v1 = svc.compute_agent_version(aid)
    v2 = svc.compute_agent_version(aid)
    assert v1 == v2
    assert len(v1) == 64  # sha256 hex


def test_compute_version_changes_on_cards_edit(agent_fs):
    paths, aid = agent_fs
    v1 = svc.compute_agent_version(aid)
    paths.agent_prompt_cards_md(aid).write_text("# card 1\nrule A\n# card 2\nrule B\n")
    v2 = svc.compute_agent_version(aid)
    assert v1 != v2


def test_compute_version_missing_agent_returns_none(isolated_data_root):
    assert svc.compute_agent_version("nonexistent") is None


def test_snapshot_agent_copies_files(agent_fs):
    paths, aid = agent_fs
    tid = "t-test"
    (paths.task_dir(tid) / "conversations").mkdir(parents=True)
    svc.snapshot_agent_into_task(task_id=tid, agent_id=aid)
    assert paths.task_agent_system_md(tid).read_text() == "you are a test agent"
    assert paths.task_agent_cards_md(tid).read_text() == "# card 1\nrule A\n"
    assert paths.task_agent_json(tid).exists()


def test_snapshot_agent_missing_cards_creates_empty(agent_fs):
    paths, aid = agent_fs
    paths.agent_prompt_cards_md(aid).unlink()
    tid = "t-test"
    (paths.task_dir(tid) / "conversations").mkdir(parents=True)
    svc.snapshot_agent_into_task(task_id=tid, agent_id=aid)
    assert paths.task_agent_cards_md(tid).read_text() == ""


def test_snapshot_skills_index_distinguishes_agentic_vs_builtin(isolated_data_root):
    paths = get_paths()
    # agentic skill
    (paths.skills / "md-helper").mkdir(parents=True)
    (paths.skills / "md-helper" / "SKILL.md").write_text(
        "---\nname: md-helper\ndescription: test\n---\n\nHelper body"
    )
    tid = "t-sk"
    (paths.task_dir(tid) / "conversations").mkdir(parents=True)
    svc.snapshot_skills_into_task(task_id=tid, skill_ids=["md-helper", "now"])
    idx = paths.task_skills_index(tid)
    from app.core.storage import read_json

    data = read_json(idx)
    assert len(data) == 2
    by_id = {x["id"]: x for x in data}
    assert by_id["md-helper"]["category"] == "agentic"
    assert paths.task_skill_md(tid, "md-helper").read_text().startswith("---\nname: md-helper")
    # builtin `now`: logged in INDEX but no SKILL.md file
    assert by_id["now"]["category"] == "builtin"
    assert not paths.task_skill_md(tid, "now").exists()
