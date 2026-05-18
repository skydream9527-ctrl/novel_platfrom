from __future__ import annotations

import pytest

from app.core.errors import APIError
from app.core.storage import get_paths, read_json, write_json
from app.services import conversation_svc


@pytest.fixture
def task_fs(isolated_data_root):
    paths = get_paths()
    tid = "t1"
    (paths.task_dir(tid) / "conversations").mkdir(parents=True)
    write_json(paths.task_meta(tid), {"id": tid, "owner_id": "u1"})
    return paths, tid


@pytest.mark.asyncio
async def test_create_conversation_appends_to_index(task_fs):
    paths, tid = task_fs
    conv = await conversation_svc.create_conversation(
        task_id=tid, created_by="u1", title="first",
    )
    idx = read_json(paths.task_conversations_index(tid))
    assert len(idx) == 1
    assert idx[0]["id"] == conv["id"]
    assert idx[0]["created_by"] == "u1"
    assert idx[0]["message_count"] == 0


@pytest.mark.asyncio
async def test_list_conversations(task_fs):
    paths, tid = task_fs
    await conversation_svc.create_conversation(task_id=tid, created_by="u1", title="c1")
    await conversation_svc.create_conversation(task_id=tid, created_by="u2", title="c2")
    items = await conversation_svc.list_conversations(task_id=tid)
    assert {i["title"] for i in items} == {"c1", "c2"}


@pytest.mark.asyncio
async def test_rename_conversation(task_fs):
    paths, tid = task_fs
    c = await conversation_svc.create_conversation(task_id=tid, created_by="u1", title="old")
    await conversation_svc.rename_conversation(task_id=tid, conv_id=c["id"], title="new")
    idx = read_json(paths.task_conversations_index(tid))
    assert idx[0]["title"] == "new"


@pytest.mark.asyncio
async def test_delete_conversation_removes_index_and_jsonl(task_fs):
    paths, tid = task_fs
    c = await conversation_svc.create_conversation(task_id=tid, created_by="u1", title="x")
    jsonl = paths.task_conversation(tid, c["id"])
    jsonl.parent.mkdir(parents=True, exist_ok=True)
    jsonl.write_text('{"id":"m1"}\n')
    await conversation_svc.delete_conversation(task_id=tid, conv_id=c["id"])
    idx = read_json(paths.task_conversations_index(tid))
    assert idx == []
    assert not jsonl.exists()


@pytest.mark.asyncio
async def test_get_or_create_default_reuses_most_recent(task_fs):
    paths, tid = task_fs
    c1 = await conversation_svc.create_conversation(task_id=tid, created_by="u1", title="c1")
    c2 = await conversation_svc.create_conversation(task_id=tid, created_by="u1", title="c2")
    # bump c1 to be more recent
    idx = read_json(paths.task_conversations_index(tid))
    for item in idx:
        if item["id"] == c1["id"]:
            item["last_message_at"] = "2099-01-01T00:00:00+00:00"
    write_json(paths.task_conversations_index(tid), idx)

    default = await conversation_svc.get_or_create_default(task_id=tid, created_by="u1")
    assert default["id"] == c1["id"]
