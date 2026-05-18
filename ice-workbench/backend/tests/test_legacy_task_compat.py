from __future__ import annotations

import pytest

from app.core.storage import get_paths, read_json, write_json
from app.services import task_svc


@pytest.fixture
def legacy_task(isolated_data_root):
    """Simulate a pre-migration task directory: no snapshot.json, no agent/, no skills/."""
    paths = get_paths()
    tid = "legacy-1"
    (paths.task_dir(tid) / "conversations").mkdir(parents=True)
    (paths.task_dir(tid) / "tool_calls").mkdir(parents=True)
    (paths.task_dir(tid) / "files" / "uploaded").mkdir(parents=True)
    write_json(paths.task_meta(tid), {
        "id": tid, "name": "legacy", "paradigm": "data",
        "agent_id": None, "owner_id": "u1", "visibility": "private",
        "publish_status": "draft", "status": "active",
        "created_at": "2026-01-01T00:00:00+00:00",
        "updated_at": "2026-01-01T00:00:00+00:00",
        "skill_ids": [],
    })
    write_json(paths.task_workspace(tid), {"current_conversation_id": None})
    write_json(paths.task_collaborators(tid), [
        {"user_id": "u1", "role": "owner", "status": "active", "joined_at": "x"},
    ])
    return tid


@pytest.mark.asyncio
async def test_get_task_on_legacy_does_not_fail(legacy_task):
    detail = await task_svc.get_task(legacy_task, "u1")
    assert detail["id"] == legacy_task
    # Snapshot lazily filled with defaults
    assert detail.get("snapshot", {}).get("mode") == "live"
    assert detail["agent_update_available"] is False  # no agent_id
