from __future__ import annotations

import pytest

from app.core.errors import APIError, ErrorCode
from app.core.storage import get_index_db, get_paths, read_json, write_json
from app.services import file_svc, task_svc


@pytest.fixture
async def task_and_deps(isolated_data_root, monkeypatch):
    db = get_index_db()
    await db.init()
    paths = get_paths()
    (paths.agents / "a1" / "prompt").mkdir(parents=True)
    paths.agent_prompt_system_md("a1").write_text("s")
    paths.agent_prompt_cards_md("a1").write_text("c")
    write_json(paths.agent_json("a1"), {"id": "a1"})
    (paths.users / "u1").mkdir()
    write_json(paths.users / "u1" / "tasks.json", [])
    t = await task_svc.create_task(
        name="T", paradigm="data", owner_id="u1", agent_id="a1",
        description=None, initial_prompt=None, skill_ids=[], visibility="private",
    )

    async def fake_fetch(**kwargs):
        return ("Doc Title", "doc body content")
    monkeypatch.setattr(
        "app.services.feishu_import_svc.fetch_document", fake_fetch
    )
    monkeypatch.setattr(
        "app.services.feishu_import_svc.parse_feishu_url",
        lambda url: {"obj_type": "docx", "obj_token": "ABCD"},
    )
    return paths, t["id"]


@pytest.mark.asyncio
async def test_import_feishu_creates_file(task_and_deps):
    paths, tid = task_and_deps
    meta = await file_svc.import_external(
        task_id=tid, user_id="u1",
        source_type="feishu_doc",
        source_url="https://acme.feishu.cn/docx/ABCD",
        source_ref=None,
    )
    assert meta["scope"] == "imported"
    body = (paths.task_files_imported(tid) / f"{meta['file_id']}.md").read_text()
    assert "doc body content" in body
    meta_file = read_json(paths.task_files_imported_meta(tid, meta["file_id"]))
    assert meta_file["source_url"] == "https://acme.feishu.cn/docx/ABCD"
    assert meta_file["last_refreshed_at"] is None


@pytest.mark.asyncio
async def test_import_duplicate_returns_409(task_and_deps):
    paths, tid = task_and_deps
    await file_svc.import_external(
        task_id=tid, user_id="u1", source_type="feishu_doc",
        source_url="https://acme.feishu.cn/docx/ABCD", source_ref=None,
    )
    with pytest.raises(APIError) as ei:
        await file_svc.import_external(
            task_id=tid, user_id="u1", source_type="feishu_doc",
            source_url="https://acme.feishu.cn/docx/ABCD", source_ref=None,
        )
    assert ei.value.error_code == ErrorCode.IMPORT_DUPLICATE
