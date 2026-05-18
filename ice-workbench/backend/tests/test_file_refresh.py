from __future__ import annotations

import pytest

from app.core.errors import APIError, ErrorCode
from app.core.storage import get_index_db, get_paths, read_json, write_json
from app.services import file_svc, task_svc


@pytest.fixture
async def imported_file(isolated_data_root, monkeypatch):
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
    body_ref = {"v": "v1"}

    async def fake_fetch(**kwargs):
        return ("T", body_ref["v"])
    monkeypatch.setattr("app.services.feishu_import_svc.fetch_document", fake_fetch)
    monkeypatch.setattr(
        "app.services.feishu_import_svc.parse_feishu_url",
        lambda url: {"obj_type": "docx", "obj_token": "X"},
    )

    meta = await file_svc.import_external(
        task_id=t["id"], user_id="u-ed",
        source_type="feishu_doc", source_url="https://acme.feishu.cn/docx/X",
        source_ref=None,
    )
    return paths, t["id"], meta["file_id"], body_ref


@pytest.mark.asyncio
async def test_refresh_by_importer_changed(imported_file):
    paths, tid, fid, body_ref = imported_file
    body_ref["v"] = "v2"
    res = await file_svc.refresh_imported(
        task_id=tid, file_id=fid, user_id="u-ed", is_owner=False, is_admin=False,
    )
    assert res["changed"] is True
    assert (paths.task_files_imported(tid) / f"{fid}.md").read_text() == "v2"


@pytest.mark.asyncio
async def test_refresh_unchanged_source(imported_file):
    paths, tid, fid, _ = imported_file
    res = await file_svc.refresh_imported(
        task_id=tid, file_id=fid, user_id="u-ed", is_owner=False, is_admin=False,
    )
    assert res["changed"] is False


@pytest.mark.asyncio
async def test_refresh_by_other_editor_forbidden(imported_file):
    paths, tid, fid, _ = imported_file
    with pytest.raises(APIError) as ei:
        await file_svc.refresh_imported(
            task_id=tid, file_id=fid, user_id="u-other-editor",
            is_owner=False, is_admin=False,
        )
    assert ei.value.error_code == ErrorCode.FILE_REFRESH_FORBIDDEN


@pytest.mark.asyncio
async def test_refresh_by_owner_allowed(imported_file):
    paths, tid, fid, body_ref = imported_file
    body_ref["v"] = "v2"
    res = await file_svc.refresh_imported(
        task_id=tid, file_id=fid, user_id="u1", is_owner=True, is_admin=False,
    )
    assert res["changed"] is True
