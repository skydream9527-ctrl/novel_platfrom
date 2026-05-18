from __future__ import annotations

import pytest

from app.core.errors import APIError, ErrorCode
from app.core.storage import get_paths, write_json
from app.services import conversation_svc


@pytest.fixture
def task_and_conv(isolated_data_root):
    paths = get_paths()
    tid = "t1"
    (paths.task_dir(tid) / "conversations").mkdir(parents=True)
    write_json(paths.task_meta(tid), {"id": tid})
    write_json(paths.task_conversations_index(tid), [
        {"id": "c1", "title": "t", "created_by": "u1", "created_at": "x",
         "last_message_at": "x", "message_count": 0},
    ])
    return tid


def test_lock_same_cid_raises_409(task_and_conv):
    tid = task_and_conv
    with conversation_svc.acquire_inflight_lock(task_id=tid, conv_id="c1"):
        with pytest.raises(APIError) as ei:
            with conversation_svc.acquire_inflight_lock(task_id=tid, conv_id="c1"):
                pass
        assert ei.value.error_code == ErrorCode.CONVERSATION_INFLIGHT


def test_lock_different_cids_both_held(task_and_conv):
    tid = task_and_conv
    paths = get_paths()
    write_json(paths.task_conversations_index(tid), [
        {"id": "c1", "title": "t", "created_by": "u1", "created_at": "x",
         "last_message_at": "x", "message_count": 0},
        {"id": "c2", "title": "t", "created_by": "u1", "created_at": "x",
         "last_message_at": "x", "message_count": 0},
    ])
    with conversation_svc.acquire_inflight_lock(task_id=tid, conv_id="c1"):
        with conversation_svc.acquire_inflight_lock(task_id=tid, conv_id="c2"):
            pass  # no raise


def test_lock_released_after_context_exit(task_and_conv):
    tid = task_and_conv
    with conversation_svc.acquire_inflight_lock(task_id=tid, conv_id="c1"):
        pass
    # should be reusable now
    with conversation_svc.acquire_inflight_lock(task_id=tid, conv_id="c1"):
        pass
