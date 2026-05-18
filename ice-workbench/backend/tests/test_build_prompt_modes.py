from __future__ import annotations

import pytest

from app.core.storage import get_paths, write_json
from app.services import experience_card_svc as ec_svc


@pytest.fixture
def setup(isolated_data_root):
    paths = get_paths()
    # source agent
    (paths.agents / "a1" / "prompt").mkdir(parents=True)
    paths.agent_prompt_system_md("a1").write_text("SRC-SYSTEM")
    paths.agent_prompt_cards_md("a1").write_text("SRC-CARDS")
    # task dir with snapshot
    tid = "t1"
    (paths.task_dir(tid) / "agent" / "prompt").mkdir(parents=True)
    (paths.task_dir(tid) / "conversations").mkdir(parents=True)
    paths.task_agent_system_md(tid).write_text("SNAP-SYSTEM")
    paths.task_agent_cards_md(tid).write_text("SNAP-CARDS")
    write_json(paths.task_skills_index(tid), [])
    write_json(paths.task_meta(tid), {"id": tid, "agent_id": "a1"})
    return tid


def test_live_mode_reads_source_cards_but_snapshot_system(setup):
    tid = setup
    paths = get_paths()
    write_json(paths.task_snapshot(tid), {"mode": "live", "agent_source_version": "x"})
    out = ec_svc.build_system_prompt_for_task(tid)
    assert "SNAP-SYSTEM" in out
    assert "SRC-CARDS" in out
    assert "SNAP-CARDS" not in out


def test_frozen_mode_reads_snapshot_cards(setup):
    tid = setup
    paths = get_paths()
    write_json(paths.task_snapshot(tid), {"mode": "frozen", "agent_source_version": "x"})
    out = ec_svc.build_system_prompt_for_task(tid)
    assert "SNAP-SYSTEM" in out
    assert "SNAP-CARDS" in out
    assert "SRC-CARDS" not in out


def test_live_mode_falls_back_to_snapshot_if_source_agent_removed(setup):
    tid = setup
    paths = get_paths()
    write_json(paths.task_snapshot(tid), {"mode": "live", "agent_source_version": "x"})
    # simulate agent removal
    paths.agent_prompt_cards_md("a1").unlink()
    out = ec_svc.build_system_prompt_for_task(tid)
    assert "SNAP-CARDS" in out
