from __future__ import annotations

import pytest

from app.core.errors import APIError, ErrorCode
from app.core.storage import get_paths, read_json, write_json
from app.services import join_request_svc


@pytest.fixture
def public_task(isolated_data_root):
    paths = get_paths()
    tid = "t1"
    (paths.task_dir(tid)).mkdir(parents=True)
    write_json(paths.task_meta(tid), {
        "id": tid, "owner_id": "u1",
        "visibility": "public", "publish_status": "published",
    })
    write_json(paths.task_collaborators(tid), [
        {"user_id": "u1", "role": "owner", "status": "active", "joined_at": "x"},
    ])
    return tid


@pytest.mark.asyncio
async def test_submit_join_request(public_task):
    tid = public_task
    req = await join_request_svc.submit(task_id=tid, user_id="u-asker", message="me")
    assert req["status"] == "pending"
    assert req["user_id"] == "u-asker"


@pytest.mark.asyncio
async def test_submit_dedup_pending_returns_409(public_task):
    tid = public_task
    await join_request_svc.submit(task_id=tid, user_id="u-asker", message="m1")
    with pytest.raises(APIError) as ei:
        await join_request_svc.submit(task_id=tid, user_id="u-asker", message="m2")
    assert ei.value.error_code == ErrorCode.JOIN_ALREADY_PENDING


@pytest.mark.asyncio
async def test_submit_already_member_returns_400(public_task):
    tid = public_task
    with pytest.raises(APIError) as ei:
        await join_request_svc.submit(task_id=tid, user_id="u1", message="m")
    assert ei.value.error_code == ErrorCode.JOIN_ALREADY_MEMBER


@pytest.mark.asyncio
async def test_approve_adds_editor(public_task):
    tid = public_task
    req = await join_request_svc.submit(task_id=tid, user_id="u-asker", message="m")
    await join_request_svc.review(
        task_id=tid, req_id=req["id"], new_status="approved", operator_id="u1",
    )
    collabs = read_json(get_paths().task_collaborators(tid))
    assert any(c["user_id"] == "u-asker" and c["role"] == "editor" and c["status"] == "active"
               for c in collabs)


@pytest.mark.asyncio
async def test_reject_keeps_collaborator_list(public_task):
    tid = public_task
    req = await join_request_svc.submit(task_id=tid, user_id="u-asker", message="m")
    await join_request_svc.review(
        task_id=tid, req_id=req["id"], new_status="rejected", operator_id="u1",
    )
    collabs = read_json(get_paths().task_collaborators(tid))
    assert not any(c["user_id"] == "u-asker" for c in collabs)
    reqs = read_json(get_paths().task_join_requests(tid))
    assert reqs[0]["status"] == "rejected"
