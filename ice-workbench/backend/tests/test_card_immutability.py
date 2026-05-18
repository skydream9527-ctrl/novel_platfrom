from __future__ import annotations

import pytest

from app.core.errors import APIError, ErrorCode
from app.core.storage import get_paths, write_json
from app.services import experience_card_svc


@pytest.fixture
async def approved_card(isolated_data_root):
    paths = get_paths()
    tid = "t1"
    (paths.task_dir(tid)).mkdir(parents=True)
    card = {
        "id": "c1", "task_id": tid, "agent_id": "a1", "author_id": "u1",
        "title": "t", "rule": "r", "status": "approved",
        "approved_by": "admin1", "approved_at": "2026-05-10T00:00:00+00:00",
        "created_at": "2026-05-10T00:00:00+00:00",
    }
    write_json(paths.task_experience_cards(tid), [card])
    await experience_card_svc.ensure_index()
    from app.core.storage import get_index_db
    db = get_index_db()
    await db.upsert("experience_cards_index", {
        "id": "c1", "task_id": tid, "agent_id": "a1", "author_id": "u1",
        "status": "approved", "title": "t", "created_at": card["created_at"],
    })
    return tid


@pytest.mark.asyncio
async def test_approved_to_rejected_is_forbidden(approved_card):
    with pytest.raises(APIError) as ei:
        await experience_card_svc.update_status(
            card_id="c1", new_status="rejected", operator_id="admin1",
        )
    assert ei.value.error_code == ErrorCode.CARD_STATUS_IMMUTABLE


@pytest.mark.asyncio
async def test_approved_to_approved_is_noop(approved_card):
    res = await experience_card_svc.update_status(
        card_id="c1", new_status="approved", operator_id="admin1",
    )
    assert res["status"] == "approved"
