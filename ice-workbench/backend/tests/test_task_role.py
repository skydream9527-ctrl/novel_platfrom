from __future__ import annotations

import pytest

from app.core.deps import TaskRole, derive_task_role


@pytest.fixture
def task_meta():
    return {
        "id": "t1",
        "owner_id": "u-owner",
        "visibility": "private",
        "publish_status": "draft",
    }


def test_owner_is_owner(task_meta):
    collabs = [{"user_id": "u-owner", "role": "owner", "status": "active"}]
    assert derive_task_role(task_meta, collabs, user_id="u-owner", is_admin=False) == TaskRole.OWNER


def test_active_editor_is_editor(task_meta):
    collabs = [
        {"user_id": "u-owner", "role": "owner", "status": "active"},
        {"user_id": "u-ed", "role": "editor", "status": "active"},
    ]
    assert derive_task_role(task_meta, collabs, user_id="u-ed", is_admin=False) == TaskRole.EDITOR


def test_admin_overrides_to_admin(task_meta):
    collabs = [{"user_id": "u-owner", "role": "owner", "status": "active"}]
    assert derive_task_role(task_meta, collabs, user_id="u-admin", is_admin=True) == TaskRole.ADMIN


def test_non_collaborator_on_private_is_none(task_meta):
    collabs = [{"user_id": "u-owner", "role": "owner", "status": "active"}]
    assert derive_task_role(task_meta, collabs, user_id="u-stranger", is_admin=False) is None


def test_stranger_on_published_public_is_viewer(task_meta):
    task_meta["visibility"] = "public"
    task_meta["publish_status"] = "published"
    collabs = [{"user_id": "u-owner", "role": "owner", "status": "active"}]
    assert derive_task_role(task_meta, collabs, user_id="u-stranger", is_admin=False) == TaskRole.VIEWER


def test_stranger_on_pending_public_is_none(task_meta):
    task_meta["visibility"] = "public"
    task_meta["publish_status"] = "pending"
    collabs = [{"user_id": "u-owner", "role": "owner", "status": "active"}]
    assert derive_task_role(task_meta, collabs, user_id="u-stranger", is_admin=False) is None


def test_inactive_collaborator_falls_back_to_viewer_on_public(task_meta):
    task_meta["visibility"] = "public"
    task_meta["publish_status"] = "published"
    collabs = [{"user_id": "u-ex", "role": "editor", "status": "removed"}]
    assert derive_task_role(task_meta, collabs, user_id="u-ex", is_admin=False) == TaskRole.VIEWER
