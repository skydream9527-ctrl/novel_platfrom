# Task Workspace Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add task workspace with C3 hybrid snapshot (agent+skill), W3 tiered collaboration (viewer/editor/owner), R2 import-and-freeze for external content, and multi-conversation parallelism — implementing the design at [`../specs/2026-05-12-task-workspace-design.md`](../specs/2026-05-12-task-workspace-design.md).

**Architecture:** Extends existing `task_svc` / `public_task_svc` / `file_svc` with three new services (`agent_snapshot_svc`, `conversation_svc`, `join_request_svc`, `feishu_import_svc`). All cross-file writes use existing `file_transaction`; per-cid `fcntl` locks protect LLM-inflight conversations. No schema migration — new JSON files are lazy-created.

**Tech Stack:** FastAPI + pydantic v2, SQLite index cache via `core.storage.index_db`, filesystem-first per existing G3 dual-write pattern, pytest + isolated `DATA_ROOT` fixture (`conftest.py`).

**Working directory for all commands:** `/Users/mi/Desktop/web_workspace/backend` unless noted otherwise.

---

## File Structure

**New files:**
- `backend/app/services/agent_snapshot_svc.py` — snapshot create/refresh, version compute
- `backend/app/services/conversation_svc.py` — multi-conversation CRUD + per-cid inflight lock
- `backend/app/services/join_request_svc.py` — join request CRUD
- `backend/app/services/feishu_import_svc.py` — feishu doc fetcher (SSRF-safe)
- `backend/app/api/v1/conversations.py` — conversation endpoints
- `backend/app/schemas/task_workspace.py` — new pydantic schemas

**Modified files:**
- `backend/app/core/errors.py` — new error codes
- `backend/app/core/storage/paths.py` — new path helpers (agent/, skills/, snapshot.json, imported/, INDEX.json, join_requests.json)
- `backend/app/core/deps.py` — `get_task_role` dependency
- `backend/app/services/task_svc.py` — hook snapshot into create; add `agent_update_available`
- `backend/app/services/public_task_svc.py` — freeze/thaw snapshot on share/unshare
- `backend/app/services/experience_card_svc.py` — forbid approved→rejected
- `backend/app/services/file_svc.py` — `list_task_files` returns `scope`; import/refresh entrypoints delegate
- `backend/app/api/v1/tasks.py` — agent refresh + join request endpoints
- `backend/app/api/v1/files.py` — import + refresh endpoints
- `backend/app/main.py` — register conversations router

---

## Phase 0 — Foundations

### Task 1: Add error codes

**Files:**
- Modify: `backend/app/core/errors.py`

- [ ] **Step 1: Edit errors.py to append new error codes**

Append inside `class ErrorCode:` (alphabetically grouped with existing):

```python
    # Task workspace
    CONVERSATION_INFLIGHT = "CONVERSATION_INFLIGHT"
    JOIN_ALREADY_PENDING = "JOIN_ALREADY_PENDING"
    JOIN_ALREADY_MEMBER = "JOIN_ALREADY_MEMBER"
    AGENT_SNAPSHOT_STALE = "AGENT_SNAPSHOT_STALE"
    IMPORT_SOURCE_NOT_SUPPORTED = "IMPORT_SOURCE_NOT_SUPPORTED"
    IMPORT_SOURCE_NOT_ACCESSIBLE = "IMPORT_SOURCE_NOT_ACCESSIBLE"
    IMPORT_DUPLICATE = "IMPORT_DUPLICATE"
    IMPORT_FETCH_FAILED = "IMPORT_FETCH_FAILED"
    FEISHU_DISABLED = "FEISHU_DISABLED"
    FILE_REFRESH_FORBIDDEN = "FILE_REFRESH_FORBIDDEN"
    CARD_STATUS_IMMUTABLE = "CARD_STATUS_IMMUTABLE"
```

- [ ] **Step 2: Commit**

```bash
git add backend/app/core/errors.py
git commit -m "feat(errors): add task workspace error codes"
```

---

### Task 2: Extend storage paths

**Files:**
- Modify: `backend/app/core/storage/paths.py`

- [ ] **Step 1: Read current paths.py to find insertion point**

Run: `cat backend/app/core/storage/paths.py | sed -n '50,95p'`
Expected: see `task_files_uploaded`, `task_files_meta` — insert new helpers right after.

- [ ] **Step 2: Add path helpers**

Append inside the `Paths` class (after `task_files_meta`):

```python
    # C3 snapshot & multi-conversation & imports

    def task_agent_dir(self, task_id: str) -> Path:
        return self.task_dir(task_id) / "agent"

    def task_agent_json(self, task_id: str) -> Path:
        return self.task_agent_dir(task_id) / "agent.json"

    def task_agent_prompt_dir(self, task_id: str) -> Path:
        return self.task_agent_dir(task_id) / "prompt"

    def task_agent_system_md(self, task_id: str) -> Path:
        return self.task_agent_prompt_dir(task_id) / "system.md"

    def task_agent_cards_md(self, task_id: str) -> Path:
        return self.task_agent_prompt_dir(task_id) / "cards.md"

    def task_skills_dir(self, task_id: str) -> Path:
        return self.task_dir(task_id) / "skills"

    def task_skills_index(self, task_id: str) -> Path:
        return self.task_skills_dir(task_id) / "INDEX.json"

    def task_skill_md(self, task_id: str, skill_id: str) -> Path:
        return self.task_skills_dir(task_id) / skill_id / "SKILL.md"

    def task_snapshot(self, task_id: str) -> Path:
        return self.task_dir(task_id) / "snapshot.json"

    def task_join_requests(self, task_id: str) -> Path:
        return self.task_dir(task_id) / "join_requests.json"

    def task_conversations_index(self, task_id: str) -> Path:
        return self.task_dir(task_id) / "conversations" / "INDEX.json"

    def task_conversation_lock(self, task_id: str, conv_id: str) -> Path:
        return self.task_dir(task_id) / "conversations" / f"{conv_id}.lock"

    def task_files_imported(self, task_id: str) -> Path:
        return self.task_dir(task_id) / "files" / "imported"

    def task_files_imported_meta(self, task_id: str, file_id: str) -> Path:
        return self.task_files_imported(task_id) / ".meta" / f"{file_id}.json"

    # Source-of-truth agent files (shared across tasks)

    def agent_prompt_system_md(self, agent_id: str) -> Path:
        return self.agents / agent_id / "prompt" / "system.md"

    def agent_prompt_cards_md(self, agent_id: str) -> Path:
        return self.agents / agent_id / "prompt" / "cards.md"

    def agent_json(self, agent_id: str) -> Path:
        return self.agents / agent_id / "agent.json"
```

- [ ] **Step 3: Commit**

```bash
git add backend/app/core/storage/paths.py
git commit -m "feat(storage): add task workspace path helpers"
```

---

### Task 3: Role derivation dependency

**Files:**
- Modify: `backend/app/core/deps.py`
- Test: `backend/tests/test_task_role.py`

- [ ] **Step 1: Read current deps.py**

Run: `cat backend/app/core/deps.py`
Note the `get_current_user` / `require_admin` patterns — follow them.

- [ ] **Step 2: Write the failing test**

Create `backend/tests/test_task_role.py`:

```python
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
```

- [ ] **Step 3: Run test to verify it fails**

Run: `pytest backend/tests/test_task_role.py -v`
Expected: FAIL with `ImportError: cannot import name 'TaskRole'`.

- [ ] **Step 4: Implement `derive_task_role` + `get_task_role`**

Append to `backend/app/core/deps.py`:

```python
import enum

from fastapi import Depends

from ..core.errors import APIError, ErrorCode
from ..core.storage import get_paths, read_json


class TaskRole(str, enum.Enum):
    OWNER = "owner"
    EDITOR = "editor"
    VIEWER = "viewer"
    ADMIN = "admin"  # cross-cutting: admin gets owner-equivalent access


def derive_task_role(
    task_meta: dict, collaborators: list[dict], *, user_id: str, is_admin: bool
) -> TaskRole | None:
    if is_admin:
        return TaskRole.ADMIN
    if task_meta.get("owner_id") == user_id:
        return TaskRole.OWNER
    for c in collaborators:
        if c.get("user_id") == user_id and c.get("status") == "active":
            role = c.get("role")
            if role == "owner":
                return TaskRole.OWNER
            if role == "editor":
                return TaskRole.EDITOR
    if (
        task_meta.get("visibility") == "public"
        and task_meta.get("publish_status") == "published"
    ):
        return TaskRole.VIEWER
    return None


async def get_task_role(task_id: str, user: dict = Depends(get_current_user)) -> TaskRole:
    paths = get_paths()
    meta = read_json(paths.task_meta(task_id))
    if not meta:
        raise APIError(404, ErrorCode.RESOURCE_NOT_FOUND, "任务不存在")
    collabs = read_json(paths.task_collaborators(task_id), default=[]) or []
    role = derive_task_role(meta, collabs, user_id=user["id"], is_admin=bool(user.get("is_admin")))
    if role is None:
        raise APIError(403, ErrorCode.PERMISSION_DENIED, "无权访问该任务")
    return role


def require_task_role(*allowed: TaskRole):
    """Handler-side gate factory. Usage: Depends(require_task_role(TaskRole.EDITOR, TaskRole.OWNER, TaskRole.ADMIN))."""

    async def checker(role: TaskRole = Depends(get_task_role)) -> TaskRole:
        if role not in allowed:
            raise APIError(403, ErrorCode.PERMISSION_DENIED, "当前身份无此权限")
        return role

    return checker
```

- [ ] **Step 5: Run test to verify pass**

Run: `pytest backend/tests/test_task_role.py -v`
Expected: 7 passed.

- [ ] **Step 6: Commit**

```bash
git add backend/app/core/deps.py backend/tests/test_task_role.py
git commit -m "feat(deps): add get_task_role with W3 role derivation"
```

---

## Phase 1 — Agent & Skill Snapshot

### Task 4: Create `agent_snapshot_svc` with version compute

**Files:**
- Create: `backend/app/services/agent_snapshot_svc.py`
- Test: `backend/tests/test_agent_snapshot.py`

- [ ] **Step 1: Write failing test**

Create `backend/tests/test_agent_snapshot.py`:

```python
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
```

- [ ] **Step 2: Run test to verify fail**

Run: `cd backend && pytest tests/test_agent_snapshot.py -v`
Expected: FAIL (ModuleNotFoundError).

- [ ] **Step 3: Implement the service**

Create `backend/app/services/agent_snapshot_svc.py`:

```python
"""Agent & skill snapshot into task workspace (C3 hybrid).

- Agent: copies agent.json + prompt/system.md + prompt/cards.md into
  tasks/{tid}/agent/. Missing cards.md → create empty file (for bootstrap
  symmetry).
- Skills: writes tasks/{tid}/skills/INDEX.json; for agentic skills, also
  copies SKILL.md into tasks/{tid}/skills/<sid>/.
- Version: sha256 over sorted concat of agents/<aid>/prompt/*.md contents.
"""
from __future__ import annotations

import hashlib
import shutil
from pathlib import Path

from ..core.storage import get_paths, read_json, write_json
from . import skill_svc


def compute_agent_version(agent_id: str) -> str | None:
    paths = get_paths()
    pdir = paths.agents / agent_id / "prompt"
    if not pdir.exists():
        return None
    h = hashlib.sha256()
    for md in sorted(pdir.glob("*.md")):
        h.update(md.name.encode())
        h.update(b"\0")
        h.update(md.read_bytes())
        h.update(b"\0")
    return h.hexdigest()


def snapshot_agent_into_task(*, task_id: str, agent_id: str | None) -> None:
    """Copy source agent files into tasks/{tid}/agent/. Idempotent (overwrites)."""
    if not agent_id:
        return
    paths = get_paths()
    src_prompt = paths.agents / agent_id / "prompt"
    dst_prompt = paths.task_agent_prompt_dir(task_id)
    dst_prompt.mkdir(parents=True, exist_ok=True)

    # agent.json
    src_json = paths.agent_json(agent_id)
    if src_json.exists():
        shutil.copyfile(src_json, paths.task_agent_json(task_id))

    # system.md
    src_sys = paths.agent_prompt_system_md(agent_id)
    if src_sys.exists():
        shutil.copyfile(src_sys, paths.task_agent_system_md(task_id))
    else:
        paths.task_agent_system_md(task_id).write_text("")

    # cards.md (ensure exists even if source doesn't — bootstrap symmetry)
    src_cards = paths.agent_prompt_cards_md(agent_id)
    if src_cards.exists():
        shutil.copyfile(src_cards, paths.task_agent_cards_md(task_id))
    else:
        paths.task_agent_cards_md(task_id).write_text("")


def snapshot_skills_into_task(*, task_id: str, skill_ids: list[str]) -> None:
    """Write INDEX.json for all selected skills; copy SKILL.md for agentic ones."""
    paths = get_paths()
    paths.task_skills_dir(task_id).mkdir(parents=True, exist_ok=True)
    catalog = {s["id"]: s for s in skill_svc.list_all()}
    index: list[dict] = []
    for sid in skill_ids:
        s = catalog.get(sid)
        if not s:
            continue
        entry = {
            "id": s["id"],
            "name": s.get("name"),
            "description": s.get("description"),
            "category": s.get("category"),
            "tool_entry": s.get("tool_entry"),
            "source_version": None,
        }
        if s.get("category") == "agentic":
            src = paths.skills / sid / "SKILL.md"
            if src.exists():
                dst = paths.task_skill_md(task_id, sid)
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(src, dst)
                import hashlib as _h

                entry["source_version"] = _h.sha256(src.read_bytes()).hexdigest()
        index.append(entry)
    write_json(paths.task_skills_index(task_id), index)


def read_snapshot(task_id: str) -> dict | None:
    return read_json(get_paths().task_snapshot(task_id))


def write_initial_snapshot(*, task_id: str, agent_id: str | None) -> dict:
    snap = {
        "mode": "live",
        "agent_source_version": compute_agent_version(agent_id) if agent_id else None,
        "frozen_at": None,
        "frozen_by": None,
        "last_manual_update_at": None,
        "last_manual_update_by": None,
    }
    write_json(get_paths().task_snapshot(task_id), snap)
    return snap
```

- [ ] **Step 4: Run test to verify pass**

Run: `cd backend && pytest tests/test_agent_snapshot.py -v`
Expected: 6 passed.

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/agent_snapshot_svc.py backend/tests/test_agent_snapshot.py
git commit -m "feat(services): add agent_snapshot_svc for C3 hybrid snapshot"
```

---

### Task 5: Hook snapshot into `create_task`

**Files:**
- Modify: `backend/app/services/task_svc.py:27-110` (the existing `create_task`)
- Test: `backend/tests/test_task_create_snapshot.py`

- [ ] **Step 1: Write failing test**

Create `backend/tests/test_task_create_snapshot.py`:

```python
from __future__ import annotations

import pytest

from app.core.storage import get_paths, read_json, write_json
from app.services import task_svc


@pytest.fixture
async def agent_and_user(isolated_data_root):
    paths = get_paths()
    (paths.agents / "a1" / "prompt").mkdir(parents=True)
    (paths.agents / "a1" / "prompt" / "system.md").write_text("you are a1")
    (paths.agents / "a1" / "prompt" / "cards.md").write_text("rule1")
    write_json(paths.agent_json("a1"), {"id": "a1", "name": "A1"})
    # user dir so user_tasks_index writes cleanly
    (paths.users / "u1").mkdir(parents=True)
    write_json(paths.users / "u1" / "tasks.json", [])
    return paths


@pytest.mark.asyncio
async def test_create_task_snapshots_agent(agent_and_user):
    paths = agent_and_user
    t = await task_svc.create_task(
        name="T", paradigm="data", owner_id="u1", agent_id="a1",
        description=None, initial_prompt=None, skill_ids=[], visibility="private",
    )
    tid = t["id"]
    assert paths.task_agent_system_md(tid).read_text() == "you are a1"
    assert paths.task_agent_cards_md(tid).read_text() == "rule1"
    assert paths.task_agent_json(tid).exists()
    snap = read_json(paths.task_snapshot(tid))
    assert snap["mode"] == "live"
    assert snap["agent_source_version"] is not None
    assert len(snap["agent_source_version"]) == 64
    assert snap["frozen_at"] is None


@pytest.mark.asyncio
async def test_create_task_without_agent_has_null_version(agent_and_user):
    paths = agent_and_user
    t = await task_svc.create_task(
        name="T", paradigm="general", owner_id="u1", agent_id=None,
        description=None, initial_prompt=None, skill_ids=[], visibility="private",
    )
    snap = read_json(paths.task_snapshot(t["id"]))
    assert snap["mode"] == "live"
    assert snap["agent_source_version"] is None


@pytest.mark.asyncio
async def test_create_task_writes_skill_index(agent_and_user):
    paths = agent_and_user
    (paths.skills / "helper").mkdir(parents=True)
    (paths.skills / "helper" / "SKILL.md").write_text(
        "---\nname: helper\ndescription: h\n---\nbody"
    )
    t = await task_svc.create_task(
        name="T", paradigm="data", owner_id="u1", agent_id="a1",
        description=None, initial_prompt=None, skill_ids=["helper"], visibility="private",
    )
    idx = read_json(paths.task_skills_index(t["id"]))
    assert [x["id"] for x in idx] == ["helper"]
```

- [ ] **Step 2: Run test to verify fail**

Run: `cd backend && pytest tests/test_task_create_snapshot.py -v`
Expected: FAIL — snapshot.json not created.

- [ ] **Step 3: Modify `task_svc.create_task`**

In `backend/app/services/task_svc.py`, add import at top:

```python
from . import agent_snapshot_svc
```

Inside the `with file_transaction(paths_to_lock) as tx:` block of `create_task`, **after** the `tx.write_json(paths.task_experience_cards(tid), [])` line and **before** the `user_index = tx.read_json(...)` line, insert:

```python
        # C3 snapshot (Task 5): agent + skills + snapshot.json
        tx.makedirs([
            paths.task_agent_prompt_dir(tid),
            paths.task_skills_dir(tid),
            paths.task_files_imported(tid),
            paths.task_files_imported(tid) / ".meta",
        ])
        # Agent files are plain shutil copies (not transactional) because they
        # live outside the tx's managed paths; the tx still holds the meta lock.
        agent_snapshot_svc.snapshot_agent_into_task(task_id=tid, agent_id=agent_id)
        agent_snapshot_svc.snapshot_skills_into_task(task_id=tid, skill_ids=skill_ids or [])
        snap = {
            "mode": "live",
            "agent_source_version": agent_snapshot_svc.compute_agent_version(agent_id) if agent_id else None,
            "frozen_at": None,
            "frozen_by": None,
            "last_manual_update_at": None,
            "last_manual_update_by": None,
        }
        tx.write_json(paths.task_snapshot(tid), snap)
```

- [ ] **Step 4: Run test to verify pass**

Run: `cd backend && pytest tests/test_task_create_snapshot.py -v`
Expected: 3 passed.

- [ ] **Step 5: Run full task-related suite to catch regressions**

Run: `cd backend && pytest tests/ -v -k "task or storage"`
Expected: all green.

- [ ] **Step 6: Commit**

```bash
git add backend/app/services/task_svc.py backend/tests/test_task_create_snapshot.py
git commit -m "feat(task): snapshot agent+skills on task creation"
```

---

### Task 6: `build_system_prompt` mode-aware

**Files:**
- Modify: `backend/app/services/experience_card_svc.py:257-` (`build_system_prompt`)
- Test: `backend/tests/test_build_prompt_modes.py`

- [ ] **Step 1: Read current implementation**

Run: `cat backend/app/services/experience_card_svc.py | sed -n '257,300p'`
Note exact signature.

- [ ] **Step 2: Write failing test**

Create `backend/tests/test_build_prompt_modes.py`:

```python
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
```

- [ ] **Step 3: Run test to verify fail**

Run: `cd backend && pytest tests/test_build_prompt_modes.py -v`
Expected: FAIL — `build_system_prompt_for_task` doesn't exist.

- [ ] **Step 4: Add `build_system_prompt_for_task`**

Append to `backend/app/services/experience_card_svc.py`:

```python
def build_system_prompt_for_task(task_id: str) -> str:
    """Mode-aware prompt build (spec 4.2).

    - system.md: always read from task snapshot
    - cards.md: live → source (with fallback); frozen → snapshot
    - skills catalog: from task's skills INDEX
    """
    paths = get_paths()
    snap = read_json(paths.task_snapshot(task_id)) or {"mode": "live"}
    meta = read_json(paths.task_meta(task_id)) or {}
    agent_id = meta.get("agent_id")

    system_md = ""
    sys_path = paths.task_agent_system_md(task_id)
    if sys_path.exists():
        system_md = sys_path.read_text()

    if snap.get("mode") == "frozen":
        cards_md = _safe_read(paths.task_agent_cards_md(task_id))
    else:
        src = paths.agent_prompt_cards_md(agent_id) if agent_id else None
        if src and src.exists():
            cards_md = src.read_text()
        else:
            cards_md = _safe_read(paths.task_agent_cards_md(task_id))

    skills_catalog = read_json(paths.task_skills_index(task_id), default=[]) or []
    skill_lines = "\n".join(f"- {s['id']}: {s.get('description', '')}" for s in skills_catalog)

    parts = [system_md]
    if cards_md.strip():
        parts.append("## Approved Experience Cards\n" + cards_md)
    if skill_lines:
        parts.append("## Available Skills\n" + skill_lines)
    return "\n\n".join(parts).strip()


def _safe_read(path) -> str:
    try:
        return path.read_text()
    except (FileNotFoundError, OSError):
        return ""
```

- [ ] **Step 5: Run test to verify pass**

Run: `cd backend && pytest tests/test_build_prompt_modes.py -v`
Expected: 3 passed.

- [ ] **Step 6: Commit**

```bash
git add backend/app/services/experience_card_svc.py backend/tests/test_build_prompt_modes.py
git commit -m "feat(prompt): mode-aware prompt build reading snapshot vs source cards"
```

> **Note for executor:** Existing callers of `build_system_prompt(agent_id)` may remain valid for non-task contexts. `build_system_prompt_for_task(task_id)` is the new task-scoped entrypoint. Follow-up tasks may migrate callers — out of scope for this task.

---

## Phase 2 — Share/Unshare Freeze & Thaw

### Task 7: `share_task` freezes snapshot

**Files:**
- Modify: `backend/app/services/public_task_svc.py` (`share_task`)
- Test: `backend/tests/test_share_freeze.py`

- [ ] **Step 1: Write failing test**

Create `backend/tests/test_share_freeze.py`:

```python
from __future__ import annotations

import pytest

from app.core.storage import get_paths, read_json, write_json
from app.services import public_task_svc, task_svc


@pytest.fixture
async def task_with_snapshot(isolated_data_root):
    paths = get_paths()
    (paths.agents / "a1" / "prompt").mkdir(parents=True)
    paths.agent_prompt_system_md("a1").write_text("SYS-v1")
    paths.agent_prompt_cards_md("a1").write_text("CARDS-v1")
    write_json(paths.agent_json("a1"), {"id": "a1"})
    (paths.users / "u1").mkdir()
    write_json(paths.users / "u1" / "tasks.json", [])
    t = await task_svc.create_task(
        name="T", paradigm="data", owner_id="u1", agent_id="a1",
        description=None, initial_prompt=None, skill_ids=[], visibility="private",
    )
    return paths, t["id"]


@pytest.mark.asyncio
async def test_share_task_freezes_snapshot(task_with_snapshot):
    paths, tid = task_with_snapshot
    # simulate cards update happening just before share
    paths.agent_prompt_cards_md("a1").write_text("CARDS-v2")
    await public_task_svc.share_task(task_id=tid, owner_id="u1")

    snap = read_json(paths.task_snapshot(tid))
    assert snap["mode"] == "frozen"
    assert snap["frozen_at"] is not None
    assert snap["frozen_by"] == "u1"
    # snapshot's cards.md was refreshed to v2 at freeze moment
    assert paths.task_agent_cards_md(tid).read_text() == "CARDS-v2"


@pytest.mark.asyncio
async def test_share_task_requires_owner(task_with_snapshot):
    paths, tid = task_with_snapshot
    from app.core.errors import APIError
    with pytest.raises(APIError):
        await public_task_svc.share_task(task_id=tid, owner_id="some-other-user")
```

- [ ] **Step 2: Run test to verify fail**

Run: `cd backend && pytest tests/test_share_freeze.py -v`
Expected: FAIL — snapshot still `mode=live`.

- [ ] **Step 3: Modify `share_task`**

In `backend/app/services/public_task_svc.py`, find the `share_task` function. **After** the `meta["shared_at"] = _now()` line and **before** `write_json(paths.task_meta(task_id), meta)`, insert:

```python
    # Freeze snapshot (spec 4.3)
    from . import agent_snapshot_svc
    agent_id = meta.get("agent_id")
    if agent_id:
        # Re-copy cards.md from source at freeze moment
        src_cards = paths.agent_prompt_cards_md(agent_id)
        if src_cards.exists():
            paths.task_agent_cards_md(task_id).write_text(src_cards.read_text())
        new_version = agent_snapshot_svc.compute_agent_version(agent_id)
    else:
        new_version = None
    snap = read_json(paths.task_snapshot(task_id)) or {}
    snap.update({
        "mode": "frozen",
        "agent_source_version": new_version,
        "frozen_at": _now(),
        "frozen_by": owner_id,
    })
    write_json(paths.task_snapshot(task_id), snap)
```

- [ ] **Step 4: Run test**

Run: `cd backend && pytest tests/test_share_freeze.py -v`
Expected: 2 passed.

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/public_task_svc.py backend/tests/test_share_freeze.py
git commit -m "feat(share): freeze snapshot on share, copying current cards"
```

---

### Task 8: `unshare_task` thaws + rejects pending joins

**Files:**
- Modify: `backend/app/services/public_task_svc.py` (`unshare_task`)
- Test: `backend/tests/test_unshare_thaw.py`

- [ ] **Step 1: Write failing test**

Create `backend/tests/test_unshare_thaw.py`:

```python
from __future__ import annotations

import pytest

from app.core.storage import get_paths, read_json, write_json
from app.services import public_task_svc, task_svc


@pytest.fixture
async def shared_task(isolated_data_root):
    paths = get_paths()
    (paths.agents / "a1" / "prompt").mkdir(parents=True)
    paths.agent_prompt_system_md("a1").write_text("SYS")
    paths.agent_prompt_cards_md("a1").write_text("CARDS")
    write_json(paths.agent_json("a1"), {"id": "a1"})
    (paths.users / "u1").mkdir()
    write_json(paths.users / "u1" / "tasks.json", [])
    t = await task_svc.create_task(
        name="T", paradigm="data", owner_id="u1", agent_id="a1",
        description=None, initial_prompt=None, skill_ids=[], visibility="private",
    )
    await public_task_svc.share_task(task_id=t["id"], owner_id="u1")
    # seed a pending join request
    write_json(paths.task_join_requests(t["id"]), [
        {"id": "r1", "user_id": "u-asker", "message": "in", "status": "pending",
         "created_at": "2026-05-12T00:00:00+00:00"},
    ])
    return paths, t["id"]


@pytest.mark.asyncio
async def test_unshare_thaws_and_rejects_joins(shared_task):
    paths, tid = shared_task
    await public_task_svc.unshare_task(task_id=tid, owner_id="u1")

    snap = read_json(paths.task_snapshot(tid))
    assert snap["mode"] == "live"

    jr = read_json(paths.task_join_requests(tid))
    assert jr[0]["status"] == "rejected"
    assert jr[0]["reviewed_by"] == "u1"
    assert jr[0].get("reject_reason") == "task_unshared"

    meta = read_json(paths.task_meta(tid))
    assert meta["visibility"] == "private"
```

- [ ] **Step 2: Run to verify fail**

Run: `cd backend && pytest tests/test_unshare_thaw.py -v`
Expected: FAIL.

- [ ] **Step 3: Modify `unshare_task`**

In `public_task_svc.unshare_task`, after the existing `write_json(paths.task_meta(...))`, insert:

```python
    # Thaw snapshot (spec 4.3)
    snap = read_json(paths.task_snapshot(task_id)) or {}
    if snap.get("mode") == "frozen":
        snap["mode"] = "live"
        snap["frozen_at"] = None
        snap["frozen_by"] = None
        write_json(paths.task_snapshot(task_id), snap)

    # Reject all pending join requests
    jr_path = paths.task_join_requests(task_id)
    requests = read_json(jr_path, default=[]) or []
    changed = False
    for r in requests:
        if r.get("status") == "pending":
            r["status"] = "rejected"
            r["reviewed_at"] = _now()
            r["reviewed_by"] = owner_id
            r["reject_reason"] = "task_unshared"
            changed = True
    if changed:
        write_json(jr_path, requests)
```

- [ ] **Step 4: Run tests**

Run: `cd backend && pytest tests/test_unshare_thaw.py -v`
Expected: 1 passed.

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/public_task_svc.py backend/tests/test_unshare_thaw.py
git commit -m "feat(unshare): thaw snapshot and auto-reject pending join requests"
```

---

## Phase 3 — Agent Refresh Button

### Task 9: `agent_update_available` in `get_task`

**Files:**
- Modify: `backend/app/services/task_svc.py` (`get_task`)
- Test: `backend/tests/test_agent_update_flag.py`

- [ ] **Step 1: Write failing test**

Create `backend/tests/test_agent_update_flag.py`:

```python
from __future__ import annotations

import pytest

from app.core.storage import get_paths, read_json, write_json
from app.services import public_task_svc, task_svc


@pytest.fixture
async def public_task(isolated_data_root):
    paths = get_paths()
    (paths.agents / "a1" / "prompt").mkdir(parents=True)
    paths.agent_prompt_system_md("a1").write_text("SYS")
    paths.agent_prompt_cards_md("a1").write_text("CARDS-v1")
    write_json(paths.agent_json("a1"), {"id": "a1"})
    (paths.users / "u1").mkdir()
    write_json(paths.users / "u1" / "tasks.json", [])
    t = await task_svc.create_task(
        name="T", paradigm="data", owner_id="u1", agent_id="a1",
        description=None, initial_prompt=None, skill_ids=[], visibility="private",
    )
    await public_task_svc.share_task(task_id=t["id"], owner_id="u1")
    return paths, t["id"]


@pytest.mark.asyncio
async def test_flag_false_when_private(isolated_data_root):
    paths = get_paths()
    (paths.agents / "a1" / "prompt").mkdir(parents=True)
    paths.agent_prompt_system_md("a1").write_text("SYS")
    paths.agent_prompt_cards_md("a1").write_text("CARDS")
    write_json(paths.agent_json("a1"), {"id": "a1"})
    (paths.users / "u1").mkdir()
    write_json(paths.users / "u1" / "tasks.json", [])
    t = await task_svc.create_task(
        name="T", paradigm="data", owner_id="u1", agent_id="a1",
        description=None, initial_prompt=None, skill_ids=[], visibility="private",
    )
    paths.agent_prompt_cards_md("a1").write_text("CARDS-v2")  # source drifts
    detail = await task_svc.get_task(t["id"], "u1")
    assert detail["agent_update_available"] is False


@pytest.mark.asyncio
async def test_flag_true_when_public_and_source_drifted(public_task):
    paths, tid = public_task
    paths.agent_prompt_cards_md("a1").write_text("CARDS-v2")
    detail = await task_svc.get_task(tid, "u1")
    assert detail["agent_update_available"] is True


@pytest.mark.asyncio
async def test_flag_false_when_source_missing(public_task):
    paths, tid = public_task
    paths.agent_prompt_cards_md("a1").unlink()
    paths.agent_prompt_system_md("a1").unlink()
    detail = await task_svc.get_task(tid, "u1")
    assert detail["agent_update_available"] is False


@pytest.mark.asyncio
async def test_flag_false_when_in_sync(public_task):
    _, tid = public_task
    detail = await task_svc.get_task(tid, "u1")
    assert detail["agent_update_available"] is False
```

- [ ] **Step 2: Run to verify fail**

Run: `cd backend && pytest tests/test_agent_update_flag.py -v`
Expected: FAIL.

- [ ] **Step 3: Modify `task_svc.get_task`**

In `backend/app/services/task_svc.py`, locate the `get_task` function (around the `return {**meta, "workspace": workspace, "collaborators": collaborators}` line). Replace the return statement with:

```python
    from . import agent_snapshot_svc
    snap = read_json(paths.task_snapshot(task_id)) or {}
    agent_update_available = False
    if meta.get("visibility") == "public":
        aid = meta.get("agent_id")
        if aid:
            current_version = agent_snapshot_svc.compute_agent_version(aid)
            if current_version and current_version != snap.get("agent_source_version"):
                agent_update_available = True

    return {
        **meta,
        "workspace": workspace,
        "collaborators": collaborators,
        "snapshot": snap,
        "agent_update_available": agent_update_available,
    }
```

- [ ] **Step 4: Run test**

Run: `cd backend && pytest tests/test_agent_update_flag.py -v`
Expected: 4 passed.

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/task_svc.py backend/tests/test_agent_update_flag.py
git commit -m "feat(task): compute agent_update_available on get_task"
```

---

### Task 10: Agent refresh endpoint with stale guard

**Files:**
- Modify: `backend/app/services/agent_snapshot_svc.py` (add `refresh_task_snapshot`)
- Modify: `backend/app/api/v1/tasks.py` (add POST endpoint)
- Test: `backend/tests/test_agent_refresh.py`

- [ ] **Step 1: Write failing test**

Create `backend/tests/test_agent_refresh.py`:

```python
from __future__ import annotations

import pytest

from app.core.errors import APIError, ErrorCode
from app.core.storage import get_paths, read_json, write_json
from app.services import agent_snapshot_svc, public_task_svc, task_svc


@pytest.fixture
async def public_task(isolated_data_root):
    paths = get_paths()
    (paths.agents / "a1" / "prompt").mkdir(parents=True)
    paths.agent_prompt_system_md("a1").write_text("SYS")
    paths.agent_prompt_cards_md("a1").write_text("CARDS-v1")
    write_json(paths.agent_json("a1"), {"id": "a1"})
    (paths.users / "u1").mkdir()
    write_json(paths.users / "u1" / "tasks.json", [])
    t = await task_svc.create_task(
        name="T", paradigm="data", owner_id="u1", agent_id="a1",
        description=None, initial_prompt=None, skill_ids=[], visibility="private",
    )
    await public_task_svc.share_task(task_id=t["id"], owner_id="u1")
    return paths, t["id"]


@pytest.mark.asyncio
async def test_refresh_updates_snapshot_and_returns_diff(public_task):
    paths, tid = public_task
    paths.agent_prompt_cards_md("a1").write_text("CARDS-v1\nCARDS-v2-add")
    res = await agent_snapshot_svc.refresh_task_snapshot(
        task_id=tid, user_id="u1", expected_version=None,
    )
    assert res["changed"] is True
    assert paths.task_agent_cards_md(tid).read_text() == "CARDS-v1\nCARDS-v2-add"
    snap = read_json(paths.task_snapshot(tid))
    assert snap["last_manual_update_by"] == "u1"
    assert snap["last_manual_update_at"] is not None


@pytest.mark.asyncio
async def test_refresh_no_change_returns_changed_false(public_task):
    _, tid = public_task
    res = await agent_snapshot_svc.refresh_task_snapshot(
        task_id=tid, user_id="u1", expected_version=None,
    )
    assert res["changed"] is False


@pytest.mark.asyncio
async def test_refresh_stale_expected_version_raises_409(public_task):
    paths, tid = public_task
    paths.agent_prompt_cards_md("a1").write_text("CARDS-v2")
    with pytest.raises(APIError) as ei:
        await agent_snapshot_svc.refresh_task_snapshot(
            task_id=tid, user_id="u1", expected_version="not-the-current-version",
        )
    assert ei.value.error_code == ErrorCode.AGENT_SNAPSHOT_STALE
```

- [ ] **Step 2: Run to verify fail**

Run: `cd backend && pytest tests/test_agent_refresh.py -v`
Expected: FAIL (no `refresh_task_snapshot`).

- [ ] **Step 3: Add `refresh_task_snapshot` to agent_snapshot_svc**

Append to `backend/app/services/agent_snapshot_svc.py`:

```python
from datetime import datetime, timezone

from ..core.errors import APIError, ErrorCode
from ..core.storage import file_transaction


def _now() -> str:
    return datetime.now(tz=timezone.utc).isoformat()


async def refresh_task_snapshot(
    *, task_id: str, user_id: str, expected_version: str | None
) -> dict:
    """Spec 4.4. Owner/admin pulls latest source agent into task snapshot.

    - expected_version, when provided, must match current snapshot.agent_source_version
      (optimistic concurrency). Mismatch → AGENT_SNAPSHOT_STALE 409.
    """
    paths = get_paths()
    meta = read_json(paths.task_meta(task_id))
    if not meta:
        raise APIError(404, ErrorCode.RESOURCE_NOT_FOUND, "任务不存在")
    agent_id = meta.get("agent_id")
    if not agent_id:
        raise APIError(400, ErrorCode.VALIDATION_ERROR, "任务未绑定 Agent")

    snap_path = paths.task_snapshot(task_id)
    with file_transaction([snap_path]) as tx:
        snap = tx.read_json(snap_path, default={"mode": "live"})
        current_version = snap.get("agent_source_version")
        if expected_version is not None and expected_version != current_version:
            raise APIError(409, ErrorCode.AGENT_SNAPSHOT_STALE, "Agent 快照已被他人更新，请刷新后重试")
        new_version = compute_agent_version(agent_id)
        if new_version is None:
            raise APIError(404, ErrorCode.RESOURCE_NOT_FOUND, "源 Agent 已下架")
        if new_version == current_version:
            return {"changed": False, "new_version": current_version}

        # Compute diff summary before overwrite
        old_cards = _safe_read_text(paths.task_agent_cards_md(task_id))
        new_cards = _safe_read_text(paths.agent_prompt_cards_md(agent_id))
        old_system = _safe_read_text(paths.task_agent_system_md(task_id))
        new_system = _safe_read_text(paths.agent_prompt_system_md(agent_id))
        diff_summary = {
            "cards_added": max(new_cards.count("\n") - old_cards.count("\n"), 0),
            "cards_removed": max(old_cards.count("\n") - new_cards.count("\n"), 0),
            "system_changed": old_system != new_system,
        }

        snapshot_agent_into_task(task_id=task_id, agent_id=agent_id)
        snap["agent_source_version"] = new_version
        snap["last_manual_update_at"] = _now()
        snap["last_manual_update_by"] = user_id
        tx.write_json(snap_path, snap)

    return {"changed": True, "new_version": new_version, "diff_summary": diff_summary}


def _safe_read_text(path) -> str:
    try:
        return path.read_text()
    except (FileNotFoundError, OSError):
        return ""
```

- [ ] **Step 4: Add API endpoint**

In `backend/app/api/v1/tasks.py`, append:

```python
from ...core.deps import TaskRole, require_task_role
from ...services import agent_snapshot_svc


@router.post("/{task_id}/agent/refresh")
async def refresh_agent_snapshot(
    task_id: str,
    body: dict | None = None,
    role: TaskRole = Depends(require_task_role(TaskRole.OWNER, TaskRole.ADMIN)),
    user: dict = Depends(get_current_user),
):
    expected = (body or {}).get("expected_agent_source_version")
    result = await agent_snapshot_svc.refresh_task_snapshot(
        task_id=task_id, user_id=user["id"], expected_version=expected,
    )
    return ok(result)
```

- [ ] **Step 5: Run tests**

Run: `cd backend && pytest tests/test_agent_refresh.py -v`
Expected: 3 passed.

- [ ] **Step 6: Commit**

```bash
git add backend/app/services/agent_snapshot_svc.py backend/app/api/v1/tasks.py backend/tests/test_agent_refresh.py
git commit -m "feat(api): POST /tasks/{id}/agent/refresh with stale guard"
```

---

## Phase 4 — Experience Card Immutability

### Task 11: Forbid approved→rejected transition

**Files:**
- Modify: `backend/app/services/experience_card_svc.py` (`update_status`)
- Test: `backend/tests/test_card_immutability.py`

- [ ] **Step 1: Write failing test**

Create `backend/tests/test_card_immutability.py`:

```python
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
```

- [ ] **Step 2: Run to verify fail**

Run: `cd backend && pytest tests/test_card_immutability.py -v`
Expected: FAIL.

- [ ] **Step 3: Modify `update_status`**

In `backend/app/services/experience_card_svc.py`, in `update_status`, after the `if new_status not in {"approved", "rejected", "draft"}:` block, insert:

```python
    # Spec 4.9: approved is terminal
    if target.get("status") == "approved" and new_status == "rejected":
        raise APIError(409, ErrorCode.CARD_STATUS_IMMUTABLE, "已审批通过的卡片不可回滚")
```

(Note: `target` is the card dict — ensure this insert happens **after** the card is loaded, and **before** the status assignment. Locate the point where `target["status"] = new_status` is set and put the guard right above it.)

- [ ] **Step 4: Run test**

Run: `cd backend && pytest tests/test_card_immutability.py -v`
Expected: 2 passed.

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/experience_card_svc.py backend/tests/test_card_immutability.py
git commit -m "feat(cards): make approved status terminal (block approved→rejected)"
```

---

## Phase 5 — Multi-Conversation

### Task 12: `conversation_svc` module with INDEX + CRUD

**Files:**
- Create: `backend/app/services/conversation_svc.py`
- Test: `backend/tests/test_conversation_svc.py`

- [ ] **Step 1: Write failing test**

Create `backend/tests/test_conversation_svc.py`:

```python
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
```

- [ ] **Step 2: Run to verify fail**

Run: `cd backend && pytest tests/test_conversation_svc.py -v`
Expected: FAIL.

- [ ] **Step 3: Implement `conversation_svc`**

Create `backend/app/services/conversation_svc.py`:

```python
"""Multi-conversation per task (spec 3.5, 4.6)."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from pathlib import Path

from ..core.errors import APIError, ErrorCode
from ..core.storage import file_transaction, get_paths, read_json, write_json


def _now() -> str:
    return datetime.now(tz=timezone.utc).isoformat()


def _new_id() -> str:
    return uuid.uuid4().hex


async def list_conversations(*, task_id: str) -> list[dict]:
    paths = get_paths()
    return read_json(paths.task_conversations_index(task_id), default=[]) or []


async def create_conversation(*, task_id: str, created_by: str, title: str | None = None) -> dict:
    paths = get_paths()
    cid = _new_id()
    now = _now()
    entry = {
        "id": cid,
        "title": title or "新对话",
        "created_by": created_by,
        "created_at": now,
        "last_message_at": now,
        "message_count": 0,
    }
    idx_path = paths.task_conversations_index(task_id)
    with file_transaction([idx_path]) as tx:
        idx = tx.read_json(idx_path, default=[])
        idx.append(entry)
        tx.write_json(idx_path, idx)
    # Ensure conversation jsonl parent exists
    paths.task_conversation(task_id, cid).parent.mkdir(parents=True, exist_ok=True)
    return entry


async def rename_conversation(*, task_id: str, conv_id: str, title: str) -> dict:
    paths = get_paths()
    idx_path = paths.task_conversations_index(task_id)
    with file_transaction([idx_path]) as tx:
        idx = tx.read_json(idx_path, default=[])
        for item in idx:
            if item["id"] == conv_id:
                item["title"] = title
                tx.write_json(idx_path, idx)
                return item
    raise APIError(404, ErrorCode.RESOURCE_NOT_FOUND, "对话不存在")


async def delete_conversation(*, task_id: str, conv_id: str) -> None:
    paths = get_paths()
    idx_path = paths.task_conversations_index(task_id)
    with file_transaction([idx_path]) as tx:
        idx = tx.read_json(idx_path, default=[])
        idx = [c for c in idx if c["id"] != conv_id]
        tx.write_json(idx_path, idx)
    jsonl = paths.task_conversation(task_id, conv_id)
    if jsonl.exists():
        jsonl.unlink()
    lock = paths.task_conversation_lock(task_id, conv_id)
    if lock.exists():
        lock.unlink()


async def get_or_create_default(*, task_id: str, created_by: str) -> dict:
    items = await list_conversations(task_id=task_id)
    if items:
        items.sort(key=lambda c: c.get("last_message_at") or "", reverse=True)
        return items[0]
    return await create_conversation(task_id=task_id, created_by=created_by, title="默认对话")


async def touch_last_message(*, task_id: str, conv_id: str) -> None:
    """Bump last_message_at + message_count. Call after each successful message write."""
    paths = get_paths()
    idx_path = paths.task_conversations_index(task_id)
    with file_transaction([idx_path]) as tx:
        idx = tx.read_json(idx_path, default=[])
        for item in idx:
            if item["id"] == conv_id:
                item["last_message_at"] = _now()
                item["message_count"] = int(item.get("message_count", 0)) + 1
                tx.write_json(idx_path, idx)
                return
```

- [ ] **Step 4: Run test**

Run: `cd backend && pytest tests/test_conversation_svc.py -v`
Expected: 5 passed.

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/conversation_svc.py backend/tests/test_conversation_svc.py
git commit -m "feat(conversation): multi-conversation CRUD with INDEX.json"
```

---

### Task 13: Per-cid inflight lock

**Files:**
- Modify: `backend/app/services/conversation_svc.py` (add `acquire_inflight_lock`)
- Test: `backend/tests/test_conversation_lock.py`

- [ ] **Step 1: Write failing test**

Create `backend/tests/test_conversation_lock.py`:

```python
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
```

- [ ] **Step 2: Run to verify fail**

Run: `cd backend && pytest tests/test_conversation_lock.py -v`
Expected: FAIL.

- [ ] **Step 3: Add `acquire_inflight_lock`**

Append to `backend/app/services/conversation_svc.py`:

```python
import fcntl
from contextlib import contextmanager


@contextmanager
def acquire_inflight_lock(*, task_id: str, conv_id: str):
    """Per-cid fcntl lock, non-blocking. Raises CONVERSATION_INFLIGHT on conflict.

    Usage:
        with acquire_inflight_lock(task_id=tid, conv_id=cid):
            # call LLM, append message to jsonl
            ...
    """
    paths = get_paths()
    lock_path = paths.task_conversation_lock(task_id, conv_id)
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    f = open(lock_path, "w")
    try:
        try:
            fcntl.flock(f.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            f.close()
            raise APIError(
                409,
                ErrorCode.CONVERSATION_INFLIGHT,
                "该对话正在处理中，请稍候",
            )
        try:
            yield
        finally:
            fcntl.flock(f.fileno(), fcntl.LOCK_UN)
    finally:
        f.close()
```

- [ ] **Step 4: Run test**

Run: `cd backend && pytest tests/test_conversation_lock.py -v`
Expected: 3 passed.

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/conversation_svc.py backend/tests/test_conversation_lock.py
git commit -m "feat(conversation): per-cid fcntl inflight lock"
```

---

### Task 14: Conversation API endpoints

**Files:**
- Create: `backend/app/api/v1/conversations.py`
- Modify: `backend/app/main.py` (register router)
- Test: `backend/tests/test_conversation_api.py`

- [ ] **Step 1: Find main.py router registration**

Run: `grep -n "include_router" backend/app/main.py`
Note the pattern (likely `app.include_router(tasks.router, prefix="/api/v1/tasks")`).

- [ ] **Step 2: Create router file**

Create `backend/app/api/v1/conversations.py`:

```python
from __future__ import annotations

from fastapi import APIRouter, Depends

from ...core.deps import TaskRole, get_current_user, require_task_role
from ...core.errors import APIError, ErrorCode, ok
from ...services import conversation_svc

router = APIRouter()


@router.get("/tasks/{task_id}/conversations")
async def list_convs(
    task_id: str,
    role: TaskRole = Depends(require_task_role(TaskRole.VIEWER, TaskRole.EDITOR, TaskRole.OWNER, TaskRole.ADMIN)),
):
    items = await conversation_svc.list_conversations(task_id=task_id)
    return ok({"items": items, "total": len(items)})


@router.post("/tasks/{task_id}/conversations")
async def create_conv(
    task_id: str,
    body: dict | None = None,
    role: TaskRole = Depends(require_task_role(TaskRole.EDITOR, TaskRole.OWNER, TaskRole.ADMIN)),
    user: dict = Depends(get_current_user),
):
    title = (body or {}).get("title")
    conv = await conversation_svc.create_conversation(
        task_id=task_id, created_by=user["id"], title=title,
    )
    return ok(conv)


@router.patch("/tasks/{task_id}/conversations/{conv_id}")
async def rename_conv(
    task_id: str,
    conv_id: str,
    body: dict,
    role: TaskRole = Depends(require_task_role(TaskRole.EDITOR, TaskRole.OWNER, TaskRole.ADMIN)),
    user: dict = Depends(get_current_user),
):
    # Creator or owner only
    items = await conversation_svc.list_conversations(task_id=task_id)
    target = next((c for c in items if c["id"] == conv_id), None)
    if not target:
        raise APIError(404, ErrorCode.RESOURCE_NOT_FOUND, "对话不存在")
    if target["created_by"] != user["id"] and role not in (TaskRole.OWNER, TaskRole.ADMIN):
        raise APIError(403, ErrorCode.PERMISSION_DENIED, "仅创建者或任务 owner 可改标题")
    title = body.get("title", "").strip()
    if not title:
        raise APIError(400, ErrorCode.VALIDATION_ERROR, "title 不能为空")
    return ok(await conversation_svc.rename_conversation(task_id=task_id, conv_id=conv_id, title=title))


@router.delete("/tasks/{task_id}/conversations/{conv_id}")
async def delete_conv(
    task_id: str,
    conv_id: str,
    role: TaskRole = Depends(require_task_role(TaskRole.EDITOR, TaskRole.OWNER, TaskRole.ADMIN)),
    user: dict = Depends(get_current_user),
):
    items = await conversation_svc.list_conversations(task_id=task_id)
    target = next((c for c in items if c["id"] == conv_id), None)
    if not target:
        raise APIError(404, ErrorCode.RESOURCE_NOT_FOUND, "对话不存在")
    if target["created_by"] != user["id"] and role not in (TaskRole.OWNER, TaskRole.ADMIN):
        raise APIError(403, ErrorCode.PERMISSION_DENIED, "仅创建者或任务 owner 可删除")
    await conversation_svc.delete_conversation(task_id=task_id, conv_id=conv_id)
    return ok({"deleted": True})
```

- [ ] **Step 3: Register router in main.py**

In `backend/app/main.py`, find the block that imports and includes v1 routers. Add:

```python
from .api.v1 import conversations as conversations_v1
...
app.include_router(conversations_v1.router, prefix="/api/v1", tags=["conversations"])
```

(Verify the prefix matches other v1 registrations — paths inside the router already start with `/tasks/...`, so prefix is just `/api/v1`.)

- [ ] **Step 4: Write integration test**

Create `backend/tests/test_conversation_api.py`:

```python
from __future__ import annotations

import pytest
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.core.storage import get_paths, write_json


@pytest.fixture
async def client_with_task(isolated_data_root):
    paths = get_paths()
    (paths.users / "u1").mkdir()
    write_json(paths.users / "u1" / "tasks.json", [])
    (paths.agents / "a1" / "prompt").mkdir(parents=True)
    paths.agent_prompt_system_md("a1").write_text("sys")
    paths.agent_prompt_cards_md("a1").write_text("cards")
    write_json(paths.agent_json("a1"), {"id": "a1"})

    from app.services import task_svc
    t = await task_svc.create_task(
        name="T", paradigm="data", owner_id="u1", agent_id="a1",
        description=None, initial_prompt=None, skill_ids=[], visibility="private",
    )

    # Stub auth: patch get_current_user to return u1
    from app.core import deps
    async def fake_user():
        return {"id": "u1", "is_admin": False}
    app.dependency_overrides[deps.get_current_user] = fake_user

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac, t["id"]
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_create_and_list_conversation(client_with_task):
    ac, tid = client_with_task
    r = await ac.post(f"/api/v1/tasks/{tid}/conversations", json={"title": "hi"})
    assert r.status_code == 200
    cid = r.json()["data"]["id"]

    r2 = await ac.get(f"/api/v1/tasks/{tid}/conversations")
    assert r2.status_code == 200
    items = r2.json()["data"]["items"]
    assert any(c["id"] == cid for c in items)
```

- [ ] **Step 5: Run tests**

Run: `cd backend && pytest tests/test_conversation_api.py -v`
Expected: 1 passed.

- [ ] **Step 6: Commit**

```bash
git add backend/app/api/v1/conversations.py backend/app/main.py backend/tests/test_conversation_api.py
git commit -m "feat(api): conversation CRUD endpoints"
```

---

## Phase 6 — Join Requests & Collaborator Management

### Task 15: `join_request_svc`

**Files:**
- Create: `backend/app/services/join_request_svc.py`
- Test: `backend/tests/test_join_request.py`

- [ ] **Step 1: Write failing test**

Create `backend/tests/test_join_request.py`:

```python
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
```

- [ ] **Step 2: Run to verify fail**

Run: `cd backend && pytest tests/test_join_request.py -v`
Expected: FAIL.

- [ ] **Step 3: Implement service**

Create `backend/app/services/join_request_svc.py`:

```python
"""Join requests for public task collaboration (spec 3.4 / 4 / W3)."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from ..core.errors import APIError, ErrorCode
from ..core.storage import file_transaction, get_paths, read_json


def _now() -> str:
    return datetime.now(tz=timezone.utc).isoformat()


def _new_id() -> str:
    return "req_" + uuid.uuid4().hex


async def submit(*, task_id: str, user_id: str, message: str) -> dict:
    paths = get_paths()
    meta = read_json(paths.task_meta(task_id))
    if not meta:
        raise APIError(404, ErrorCode.RESOURCE_NOT_FOUND, "任务不存在")
    if meta.get("visibility") != "public" or meta.get("publish_status") != "published":
        raise APIError(400, ErrorCode.VALIDATION_ERROR, "仅对已公开的任务可申请加入")

    collabs = read_json(paths.task_collaborators(task_id), default=[]) or []
    if any(c.get("user_id") == user_id and c.get("status") == "active" for c in collabs):
        raise APIError(400, ErrorCode.JOIN_ALREADY_MEMBER, "已是任务成员")

    jr_path = paths.task_join_requests(task_id)
    with file_transaction([jr_path]) as tx:
        reqs = tx.read_json(jr_path, default=[])
        if any(r.get("user_id") == user_id and r.get("status") == "pending" for r in reqs):
            raise APIError(409, ErrorCode.JOIN_ALREADY_PENDING, "已有待处理申请")
        req = {
            "id": _new_id(),
            "user_id": user_id,
            "message": message,
            "status": "pending",
            "created_at": _now(),
            "reviewed_at": None,
            "reviewed_by": None,
        }
        reqs.append(req)
        tx.write_json(jr_path, reqs)
    return req


async def list_requests(*, task_id: str, status: str | None = None) -> list[dict]:
    paths = get_paths()
    reqs = read_json(paths.task_join_requests(task_id), default=[]) or []
    if status:
        reqs = [r for r in reqs if r.get("status") == status]
    return reqs


async def review(
    *, task_id: str, req_id: str, new_status: str, operator_id: str,
    reject_reason: str | None = None,
) -> dict:
    if new_status not in {"approved", "rejected"}:
        raise APIError(400, ErrorCode.VALIDATION_ERROR, "new_status must be approved|rejected")
    paths = get_paths()
    jr_path = paths.task_join_requests(task_id)
    collab_path = paths.task_collaborators(task_id)
    with file_transaction([jr_path, collab_path]) as tx:
        reqs = tx.read_json(jr_path, default=[])
        target = next((r for r in reqs if r["id"] == req_id), None)
        if not target:
            raise APIError(404, ErrorCode.RESOURCE_NOT_FOUND, "申请不存在")
        if target.get("status") != "pending":
            raise APIError(409, ErrorCode.VALIDATION_ERROR, "申请已处理")
        target["status"] = new_status
        target["reviewed_at"] = _now()
        target["reviewed_by"] = operator_id
        if reject_reason:
            target["reject_reason"] = reject_reason
        tx.write_json(jr_path, reqs)

        if new_status == "approved":
            collabs = tx.read_json(collab_path, default=[])
            collabs.append({
                "user_id": target["user_id"],
                "role": "editor",
                "joined_at": _now(),
                "status": "active",
            })
            tx.write_json(collab_path, collabs)
    return target
```

- [ ] **Step 4: Run tests**

Run: `cd backend && pytest tests/test_join_request.py -v`
Expected: 5 passed.

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/join_request_svc.py backend/tests/test_join_request.py
git commit -m "feat(join): join request submit/review with editor promotion"
```

---

### Task 16: Join request + collaborator API endpoints

**Files:**
- Modify: `backend/app/api/v1/tasks.py`
- Test: `backend/tests/test_join_api.py`

- [ ] **Step 1: Append endpoints to tasks.py**

In `backend/app/api/v1/tasks.py`, add:

```python
from ...services import join_request_svc


@router.post("/{task_id}/join-request")
async def submit_join(
    task_id: str,
    body: dict,
    role: TaskRole = Depends(require_task_role(TaskRole.VIEWER)),
    user: dict = Depends(get_current_user),
):
    req = await join_request_svc.submit(
        task_id=task_id, user_id=user["id"], message=body.get("message", ""),
    )
    return ok(req)


@router.get("/{task_id}/join-requests")
async def list_joins(
    task_id: str,
    status: str | None = None,
    role: TaskRole = Depends(require_task_role(TaskRole.OWNER, TaskRole.ADMIN)),
):
    items = await join_request_svc.list_requests(task_id=task_id, status=status)
    return ok({"items": items, "total": len(items)})


@router.post("/{task_id}/join-requests/{req_id}/review")
async def review_join(
    task_id: str,
    req_id: str,
    body: dict,
    role: TaskRole = Depends(require_task_role(TaskRole.OWNER, TaskRole.ADMIN)),
    user: dict = Depends(get_current_user),
):
    new_status = body.get("status", "approved")
    reason = body.get("reject_reason")
    req = await join_request_svc.review(
        task_id=task_id, req_id=req_id, new_status=new_status,
        operator_id=user["id"], reject_reason=reason,
    )
    return ok(req)


@router.delete("/{task_id}/collaborators/{user_id}")
async def remove_collaborator(
    task_id: str,
    user_id: str,
    role: TaskRole = Depends(require_task_role(TaskRole.OWNER, TaskRole.ADMIN)),
):
    from ...core.storage import file_transaction, get_paths
    paths = get_paths()
    cpath = paths.task_collaborators(task_id)
    with file_transaction([cpath]) as tx:
        collabs = tx.read_json(cpath, default=[])
        target = next((c for c in collabs if c["user_id"] == user_id), None)
        if not target:
            raise APIError(404, ErrorCode.RESOURCE_NOT_FOUND, "协作者不存在")
        if target.get("role") == "owner":
            raise APIError(400, ErrorCode.VALIDATION_ERROR, "不能移除 owner")
        target["status"] = "removed"
        tx.write_json(cpath, collabs)
    return ok({"removed": True})
```

- [ ] **Step 2: Smoke test via API**

Create `backend/tests/test_join_api.py`:

```python
from __future__ import annotations

import pytest
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.core import deps
from app.core.storage import get_paths, write_json
from app.services import public_task_svc, task_svc


@pytest.fixture
async def published_task(isolated_data_root):
    paths = get_paths()
    (paths.users / "u1").mkdir()
    write_json(paths.users / "u1" / "tasks.json", [])
    (paths.agents / "a1" / "prompt").mkdir(parents=True)
    paths.agent_prompt_system_md("a1").write_text("s")
    paths.agent_prompt_cards_md("a1").write_text("c")
    write_json(paths.agent_json("a1"), {"id": "a1"})
    t = await task_svc.create_task(
        name="T", paradigm="data", owner_id="u1", agent_id="a1",
        description=None, initial_prompt=None, skill_ids=[], visibility="private",
    )
    await public_task_svc.share_task(task_id=t["id"], owner_id="u1")
    return t["id"]


@pytest.mark.asyncio
async def test_viewer_can_submit_owner_can_approve(published_task):
    tid = published_task

    async def viewer_user():
        return {"id": "u-asker", "is_admin": False}
    app.dependency_overrides[deps.get_current_user] = viewer_user

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        r = await ac.post(f"/api/v1/tasks/{tid}/join-request", json={"message": "plz"})
        assert r.status_code == 200
        rid = r.json()["data"]["id"]

    async def owner_user():
        return {"id": "u1", "is_admin": False}
    app.dependency_overrides[deps.get_current_user] = owner_user

    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        r = await ac.post(
            f"/api/v1/tasks/{tid}/join-requests/{rid}/review",
            json={"status": "approved"},
        )
        assert r.status_code == 200
        assert r.json()["data"]["status"] == "approved"

    app.dependency_overrides.clear()
```

- [ ] **Step 3: Run test**

Run: `cd backend && pytest tests/test_join_api.py -v`
Expected: 1 passed.

- [ ] **Step 4: Commit**

```bash
git add backend/app/api/v1/tasks.py backend/tests/test_join_api.py
git commit -m "feat(api): join request + collaborator remove endpoints"
```

---

## Phase 7 — External Import & Refresh

### Task 17: `feishu_import_svc` (SSRF whitelist)

**Files:**
- Create: `backend/app/services/feishu_import_svc.py`
- Test: `backend/tests/test_feishu_import.py`

- [ ] **Step 1: Write failing test**

Create `backend/tests/test_feishu_import.py`:

```python
from __future__ import annotations

import pytest

from app.core.errors import APIError, ErrorCode
from app.services import feishu_import_svc as svc


def test_parse_docx_url():
    ref = svc.parse_feishu_url("https://acme.feishu.cn/docx/ABCD1234?from=home")
    assert ref == {"obj_type": "docx", "obj_token": "ABCD1234"}


def test_parse_wiki_url():
    ref = svc.parse_feishu_url("https://acme.feishu.cn/wiki/WXYZ5678")
    assert ref == {"obj_type": "wiki", "obj_token": "WXYZ5678"}


def test_parse_rejects_non_feishu_host():
    with pytest.raises(APIError) as ei:
        svc.parse_feishu_url("https://evil.example.com/docx/ABCD1234")
    assert ei.value.error_code == ErrorCode.IMPORT_SOURCE_NOT_SUPPORTED


def test_parse_rejects_subdomain_feishu_lookalike():
    with pytest.raises(APIError):
        svc.parse_feishu_url("https://feishu.cn.evil.com/docx/X")


def test_parse_rejects_http_scheme():
    with pytest.raises(APIError):
        svc.parse_feishu_url("http://acme.feishu.cn/docx/ABCD1234")


def test_parse_unsupported_object_type():
    with pytest.raises(APIError):
        svc.parse_feishu_url("https://acme.feishu.cn/base/XYZ")
```

- [ ] **Step 2: Run to verify fail**

Run: `cd backend && pytest tests/test_feishu_import.py -v`
Expected: FAIL.

- [ ] **Step 3: Implement service**

Create `backend/app/services/feishu_import_svc.py`:

```python
"""Feishu document import. Reuses tenant_access_token from services/feishu.py.

Scope: docx + wiki. URL host MUST end with `.feishu.cn` under `https` (SSRF
defense). No configuration override — the whitelist is hard-coded.
"""
from __future__ import annotations

from urllib.parse import urlparse

from ..core.errors import APIError, ErrorCode

SUPPORTED_OBJECTS = {"docx", "wiki"}


def parse_feishu_url(url: str) -> dict:
    """Validate host + scheme, extract {obj_type, obj_token}."""
    p = urlparse(url)
    if p.scheme != "https":
        raise APIError(400, ErrorCode.IMPORT_SOURCE_NOT_SUPPORTED, "仅支持 https")
    host = (p.hostname or "").lower()
    if not host.endswith(".feishu.cn") or host == ".feishu.cn":
        raise APIError(400, ErrorCode.IMPORT_SOURCE_NOT_SUPPORTED, "仅支持 *.feishu.cn 域名")
    # Path like /docx/<token> or /wiki/<token>
    parts = [x for x in p.path.split("/") if x]
    if len(parts) < 2:
        raise APIError(400, ErrorCode.IMPORT_SOURCE_NOT_SUPPORTED, "URL 格式不符")
    obj_type, obj_token = parts[0], parts[1]
    if obj_type not in SUPPORTED_OBJECTS:
        raise APIError(400, ErrorCode.IMPORT_SOURCE_NOT_SUPPORTED, f"不支持的对象类型 {obj_type}")
    return {"obj_type": obj_type, "obj_token": obj_token}


async def fetch_document(*, obj_type: str, obj_token: str) -> tuple[str, str]:
    """Return (title, body_markdown). Raises IMPORT_FETCH_FAILED / FEISHU_DISABLED."""
    from ..core.config import get_settings
    s = get_settings()
    if not getattr(s, "feishu_enabled", False):
        raise APIError(503, ErrorCode.FEISHU_DISABLED, "飞书集成未启用")

    from . import feishu as feishu_svc  # existing tenant token provider

    token = await feishu_svc.get_tenant_access_token()
    import httpx

    headers = {"Authorization": f"Bearer {token}"}
    timeout = httpx.Timeout(30.0)
    async with httpx.AsyncClient(timeout=timeout) as client:
        if obj_type == "wiki":
            # wiki → resolve to docx obj_token first
            r = await client.get(
                f"https://open.feishu.cn/open-apis/wiki/v2/spaces/get_node",
                params={"token": obj_token},
                headers=headers,
            )
            if r.status_code == 403:
                raise APIError(403, ErrorCode.IMPORT_SOURCE_NOT_ACCESSIBLE, "飞书文档不可访问")
            if r.status_code >= 400:
                raise APIError(502, ErrorCode.IMPORT_FETCH_FAILED, f"wiki resolve failed {r.status_code}")
            node = (r.json().get("data") or {}).get("node") or {}
            obj_token = node.get("obj_token") or obj_token
            obj_type = node.get("obj_type") or "docx"

        r = await client.get(
            f"https://open.feishu.cn/open-apis/docx/v1/documents/{obj_token}/raw_content",
            headers=headers,
        )
        if r.status_code == 403:
            raise APIError(403, ErrorCode.IMPORT_SOURCE_NOT_ACCESSIBLE, "飞书文档不可访问")
        if r.status_code >= 400:
            raise APIError(502, ErrorCode.IMPORT_FETCH_FAILED, f"fetch failed {r.status_code}")
        data = r.json().get("data") or {}
        body = data.get("content") or ""

        # separately fetch title (optional best-effort)
        title = obj_token
        tr = await client.get(
            f"https://open.feishu.cn/open-apis/docx/v1/documents/{obj_token}",
            headers=headers,
        )
        if tr.status_code == 200:
            td = (tr.json().get("data") or {}).get("document") or {}
            title = td.get("title") or title

    return title, body
```

- [ ] **Step 4: Run test**

Run: `cd backend && pytest tests/test_feishu_import.py -v`
Expected: 6 passed.

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/feishu_import_svc.py backend/tests/test_feishu_import.py
git commit -m "feat(import): feishu_import_svc with SSRF-safe URL parsing"
```

---

### Task 18: Import entrypoint in `file_svc` with dedup

**Files:**
- Modify: `backend/app/services/file_svc.py`
- Test: `backend/tests/test_file_import.py`

- [ ] **Step 1: Write failing test**

Create `backend/tests/test_file_import.py`:

```python
from __future__ import annotations

import pytest

from app.core.errors import APIError, ErrorCode
from app.core.storage import get_paths, read_json, write_json
from app.services import file_svc, task_svc


@pytest.fixture
async def task_and_deps(isolated_data_root, monkeypatch):
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
```

- [ ] **Step 2: Run to verify fail**

Run: `cd backend && pytest tests/test_file_import.py -v`
Expected: FAIL.

- [ ] **Step 3: Add `import_external` to file_svc**

Append to `backend/app/services/file_svc.py`:

```python
async def import_external(
    *,
    task_id: str,
    user_id: str,
    source_type: str,
    source_url: str,
    source_ref: dict | None,
) -> dict:
    """Spec 4.7. Import external content into tasks/{tid}/files/imported/."""
    paths = get_paths()

    # Dedup: scan existing imported meta
    imp_meta_dir = paths.task_files_imported(task_id) / ".meta"
    imp_meta_dir.mkdir(parents=True, exist_ok=True)
    for mf in imp_meta_dir.glob("*.json"):
        m = read_json(mf)
        if m and m.get("source_url") == source_url:
            raise APIError(
                409, ErrorCode.IMPORT_DUPLICATE,
                f"该链接已导入，file_id={m.get('file_id')}",
                detail={"file_id": m.get("file_id")},
            )

    # Fetch
    if source_type == "feishu_doc":
        from . import feishu_import_svc
        ref = source_ref or feishu_import_svc.parse_feishu_url(source_url)
        title, body = await feishu_import_svc.fetch_document(**ref)
    elif source_type == "kb_article":
        from . import kb_svc
        if not source_ref or "kb_id" not in source_ref or "article_id" not in source_ref:
            raise APIError(400, ErrorCode.VALIDATION_ERROR, "source_ref 缺 kb_id/article_id")
        article = await kb_svc.get_article(source_ref["kb_id"], source_ref["article_id"])
        title, body = article.get("title") or "KB 文章", article.get("body") or ""
        ref = source_ref
    else:
        raise APIError(400, ErrorCode.IMPORT_SOURCE_NOT_SUPPORTED, f"不支持的 source_type: {source_type}")

    # Size cap
    data = body.encode("utf-8")
    if len(data) > MAX_SIZE_HARD_CAP_MB * 1024 * 1024:
        raise APIError(413, ErrorCode.FILE_TOO_LARGE, "文件超出大小限制")

    # Write file + meta
    file_id = str(uuid.uuid4().hex)
    safe_title = (title or "imported").replace("/", "_")[:100]
    filename = f"{safe_title}.md"
    fpath = paths.task_files_imported(task_id) / f"{file_id}.md"
    fpath.parent.mkdir(parents=True, exist_ok=True)
    fpath.write_bytes(data)
    meta = {
        "file_id": file_id,
        "filename": filename,
        "source_type": source_type,
        "source_url": source_url,
        "source_ref": ref,
        "imported_at": _now(),
        "imported_by": user_id,
        "last_refreshed_at": None,
        "last_refreshed_by": None,
        "fetch_error": None,
        "size": len(data),
    }
    write_json(paths.task_files_imported_meta(task_id, file_id), meta)

    # Update task meta counter
    task_meta_path = paths.task_meta(task_id)
    tmeta = read_json(task_meta_path) or {}
    tmeta["imported_file_count"] = int(tmeta.get("imported_file_count", 0)) + 1
    tmeta["updated_at"] = _now()
    write_json(task_meta_path, tmeta)

    return {**meta, "scope": "imported"}
```

- [ ] **Step 4: Run test**

Run: `cd backend && pytest tests/test_file_import.py -v`
Expected: 2 passed.

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/file_svc.py backend/tests/test_file_import.py
git commit -m "feat(file): import_external with dedup for kb/feishu sources"
```

---

### Task 19: Refresh imported file with permission split

**Files:**
- Modify: `backend/app/services/file_svc.py`
- Test: `backend/tests/test_file_refresh.py`

- [ ] **Step 1: Write failing test**

Create `backend/tests/test_file_refresh.py`:

```python
from __future__ import annotations

import pytest

from app.core.errors import APIError, ErrorCode
from app.core.storage import get_paths, read_json, write_json
from app.services import file_svc, task_svc


@pytest.fixture
async def imported_file(isolated_data_root, monkeypatch):
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
```

- [ ] **Step 2: Run to verify fail**

Run: `cd backend && pytest tests/test_file_refresh.py -v`
Expected: FAIL.

- [ ] **Step 3: Add `refresh_imported` to file_svc**

Append to `backend/app/services/file_svc.py`:

```python
async def refresh_imported(
    *, task_id: str, file_id: str, user_id: str, is_owner: bool, is_admin: bool,
) -> dict:
    paths = get_paths()
    meta_path = paths.task_files_imported_meta(task_id, file_id)
    meta = read_json(meta_path)
    if not meta:
        raise APIError(404, ErrorCode.RESOURCE_NOT_FOUND, "导入文件不存在")
    if not (is_owner or is_admin or meta.get("imported_by") == user_id):
        raise APIError(403, ErrorCode.FILE_REFRESH_FORBIDDEN, "无权刷新该文件")

    source_type = meta["source_type"]
    source_ref = meta.get("source_ref") or {}
    try:
        if source_type == "feishu_doc":
            from . import feishu_import_svc
            _, body = await feishu_import_svc.fetch_document(**source_ref)
        elif source_type == "kb_article":
            from . import kb_svc
            art = await kb_svc.get_article(source_ref["kb_id"], source_ref["article_id"])
            body = art.get("body") or ""
        else:
            raise APIError(400, ErrorCode.IMPORT_SOURCE_NOT_SUPPORTED, source_type)
    except APIError:
        raise
    except Exception as e:  # network / unknown
        meta["fetch_error"] = str(e)[:500]
        write_json(meta_path, meta)
        raise APIError(502, ErrorCode.IMPORT_FETCH_FAILED, f"刷新失败: {e}")

    fpath = paths.task_files_imported(task_id) / f"{file_id}.md"
    new_bytes = body.encode("utf-8")
    changed = (not fpath.exists()) or fpath.read_bytes() != new_bytes
    if changed:
        fpath.write_bytes(new_bytes)
    meta["last_refreshed_at"] = _now()
    meta["last_refreshed_by"] = user_id
    meta["fetch_error"] = None
    meta["size"] = len(new_bytes)
    write_json(meta_path, meta)
    return {"changed": changed, "size": len(new_bytes), "last_refreshed_at": meta["last_refreshed_at"]}
```

- [ ] **Step 4: Run tests**

Run: `cd backend && pytest tests/test_file_refresh.py -v`
Expected: 4 passed.

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/file_svc.py backend/tests/test_file_refresh.py
git commit -m "feat(file): refresh_imported with importer/owner permission split"
```

---

### Task 20: Import/refresh API + updated file listing

**Files:**
- Modify: `backend/app/api/v1/files.py`
- Modify: `backend/app/services/file_svc.py` (`list_task_files` scope field)
- Test: `backend/tests/test_file_api_import.py`

- [ ] **Step 1: Modify `list_task_files` to include scope + source info**

In `backend/app/services/file_svc.py`, find `list_task_files` (likely returns a flat list by iterating `files/{input,output,uploaded}`). Extend to also iterate `files/imported/` and set `scope` on each item:

```python
# In list_task_files, ensure each yielded item dict has:
#   item["scope"] = "input" | "output" | "uploaded" | "imported"
# And for imported items, also attach:
#   source_type, source_url, last_refreshed_at
# by reading the corresponding .meta/<file_id>.json.
```

Concrete addition — after the existing three scopes, add:

```python
    imported_dir = paths.task_files_imported(task_id)
    if imported_dir.exists():
        for mf in (imported_dir / ".meta").glob("*.json"):
            m = read_json(mf)
            if not m:
                continue
            body_path = imported_dir / f"{m['file_id']}.md"
            items.append({
                "file_id": m["file_id"],
                "filename": m.get("filename"),
                "size": m.get("size", body_path.stat().st_size if body_path.exists() else 0),
                "scope": "imported",
                "source_type": m.get("source_type"),
                "source_url": m.get("source_url"),
                "imported_at": m.get("imported_at"),
                "imported_by": m.get("imported_by"),
                "last_refreshed_at": m.get("last_refreshed_at"),
            })
```

(If `list_task_files` currently returns items without a `scope` key for the three existing scopes, also add `item["scope"] = "uploaded"` / `"input"` / `"output"` to each branch — grep the function body and patch uniformly.)

- [ ] **Step 2: Add API endpoints**

In `backend/app/api/v1/files.py`, append:

```python
from ...core.deps import TaskRole, require_task_role


@router.post("/import")
async def import_external(
    task_id: str = Form(...),
    source_type: str = Form(...),
    source_url: str = Form(...),
    source_ref: str | None = Form(None),  # JSON-encoded dict
    user: dict = Depends(get_current_user),
    role: TaskRole = Depends(require_task_role(TaskRole.EDITOR, TaskRole.OWNER, TaskRole.ADMIN)),
):
    import json
    ref = json.loads(source_ref) if source_ref else None
    meta = await file_svc.import_external(
        task_id=task_id, user_id=user["id"],
        source_type=source_type, source_url=source_url, source_ref=ref,
    )
    return ok(meta)


@router.post("/{file_id}/refresh")
async def refresh_imported(
    file_id: str,
    task_id: str = Form(...),
    user: dict = Depends(get_current_user),
    role: TaskRole = Depends(require_task_role(TaskRole.EDITOR, TaskRole.OWNER, TaskRole.ADMIN)),
):
    is_owner = role == TaskRole.OWNER
    is_admin = role == TaskRole.ADMIN
    result = await file_svc.refresh_imported(
        task_id=task_id, file_id=file_id, user_id=user["id"],
        is_owner=is_owner, is_admin=is_admin,
    )
    return ok(result)
```

> **Note:** `require_task_role` depends on the `task_id` path param. For these two endpoints, `task_id` is a form field, so the dependency as-written won't find it. Work around by reading `task_id` from the request inside a custom dep:

```python
from fastapi import Form

async def _task_role_from_form(
    task_id: str = Form(...),
    user: dict = Depends(get_current_user),
) -> TaskRole:
    # Reuse derive_task_role directly
    from ...core.storage import get_paths, read_json
    from ...core.deps import derive_task_role, TaskRole as _TR
    paths = get_paths()
    meta = read_json(paths.task_meta(task_id))
    if not meta:
        raise APIError(404, ErrorCode.RESOURCE_NOT_FOUND, "任务不存在")
    collabs = read_json(paths.task_collaborators(task_id), default=[]) or []
    r = derive_task_role(meta, collabs, user_id=user["id"], is_admin=bool(user.get("is_admin")))
    if r is None or r not in (_TR.EDITOR, _TR.OWNER, _TR.ADMIN):
        raise APIError(403, ErrorCode.PERMISSION_DENIED, "无权执行")
    return r
```

And replace the `require_task_role(...)` dep in both endpoints with `Depends(_task_role_from_form)`.

- [ ] **Step 3: Smoke test**

Create `backend/tests/test_file_api_import.py`:

```python
from __future__ import annotations

import json
import pytest
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.core import deps
from app.core.storage import get_paths, write_json
from app.services import task_svc


@pytest.mark.asyncio
async def test_import_endpoint_happy(isolated_data_root, monkeypatch):
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
        return ("Doc", "hello body")
    monkeypatch.setattr("app.services.feishu_import_svc.fetch_document", fake_fetch)
    monkeypatch.setattr(
        "app.services.feishu_import_svc.parse_feishu_url",
        lambda url: {"obj_type": "docx", "obj_token": "X"},
    )

    async def fake_user():
        return {"id": "u1", "is_admin": False}
    app.dependency_overrides[deps.get_current_user] = fake_user

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        r = await ac.post(
            "/api/v1/files/import",
            data={
                "task_id": t["id"],
                "source_type": "feishu_doc",
                "source_url": "https://acme.feishu.cn/docx/X",
            },
        )
        assert r.status_code == 200, r.text
        assert r.json()["data"]["scope"] == "imported"

    app.dependency_overrides.clear()
```

- [ ] **Step 4: Run tests**

Run: `cd backend && pytest tests/test_file_api_import.py -v`
Expected: 1 passed.

- [ ] **Step 5: Commit**

```bash
git add backend/app/api/v1/files.py backend/app/services/file_svc.py backend/tests/test_file_api_import.py
git commit -m "feat(api): files/import + files/{id}/refresh endpoints"
```

---

## Phase 8 — Backward Compatibility & Final Wiring

### Task 21: Lazy-create `snapshot.json` for legacy tasks in `get_task`

**Files:**
- Modify: `backend/app/services/task_svc.py` (`get_task`)
- Test: `backend/tests/test_legacy_task_compat.py`

- [ ] **Step 1: Write failing test**

Create `backend/tests/test_legacy_task_compat.py`:

```python
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
```

- [ ] **Step 2: Run to verify fail**

Run: `cd backend && pytest tests/test_legacy_task_compat.py -v`
Expected: possibly PASS already if get_task is permissive; if FAIL, continue.

- [ ] **Step 3: Harden `get_task`**

In the `get_task` return block (from Task 9), ensure `snap` defaults to a valid shape when file is absent:

```python
snap = read_json(paths.task_snapshot(task_id)) or {
    "mode": "live",
    "agent_source_version": None,
    "frozen_at": None,
    "frozen_by": None,
    "last_manual_update_at": None,
    "last_manual_update_by": None,
}
```

(Replace the existing `snap = read_json(paths.task_snapshot(task_id)) or {}` from Task 9.)

- [ ] **Step 4: Run test**

Run: `cd backend && pytest tests/test_legacy_task_compat.py -v`
Expected: 1 passed.

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/task_svc.py backend/tests/test_legacy_task_compat.py
git commit -m "fix(task): lazy default snapshot for pre-migration task dirs"
```

---

### Task 22: Audit logging for new admin-sensitive actions

**Files:**
- Modify: `backend/app/services/agent_snapshot_svc.py`
- Modify: `backend/app/services/join_request_svc.py`
- Modify: `backend/app/services/file_svc.py`

- [ ] **Step 1: Find existing audit helper**

Run: `grep -rn "def audit\|admin_svc.audit\|audit_log" backend/app/services/ | head`
Note the call shape (e.g., `await admin_svc.audit(admin_id=..., action=..., ...)`).

- [ ] **Step 2: Wire audits**

In `agent_snapshot_svc.refresh_task_snapshot`, **just before** `return {"changed": True, ...}`:

```python
        from . import admin_svc
        try:
            await admin_svc.audit(
                admin_id=user_id,
                action="refresh_task_agent_snapshot",
                target_type="task",
                target_id=task_id,
                detail={"before": current_version, "after": new_version, "diff": diff_summary},
            )
        except Exception:
            pass  # audit must never block business path
```

In `join_request_svc.review`, right before `return target`:

```python
    try:
        from . import admin_svc
        await admin_svc.audit(
            admin_id=operator_id,
            action=f"{new_status}_join_request",
            target_type="task",
            target_id=task_id,
            detail={"request_id": req_id, "applicant": target["user_id"]},
        )
    except Exception:
        pass
```

In `file_svc.refresh_imported`, right before `return {...}`, only when `changed=True`:

```python
    if changed:
        try:
            from . import admin_svc
            await admin_svc.audit(
                admin_id=user_id,
                action="refresh_imported_file",
                target_type="task",
                target_id=task_id,
                detail={"file_id": file_id, "size": len(new_bytes)},
            )
        except Exception:
            pass
```

- [ ] **Step 3: Run full suite**

Run: `cd backend && pytest tests/ -v`
Expected: all prior tests still green; no regressions.

- [ ] **Step 4: Commit**

```bash
git add backend/app/services/agent_snapshot_svc.py backend/app/services/join_request_svc.py backend/app/services/file_svc.py
git commit -m "feat(audit): log snapshot refresh, join review, imported file refresh"
```

---

## Phase 9 — Frontend Smoke (optional, can defer)

### Task 23: Playwright smoke — import + refresh + agent update banner

**Files:**
- Create: `frontend/tests/e2e/task-workspace.spec.ts`

> **Note for executor:** This is the minimal QC gate demanded by CLAUDE.md for UI flows. If frontend wiring for the new endpoints isn't yet done, this task becomes the driver for frontend work. Plan the frontend changes (route `/tasks/:tid`, conversation tab, imported file badge, agent update banner) alongside this test. Work iteratively: get the test to read the DOM selectors, then implement the components until green.

- [ ] **Step 1: Draft smoke test (will initially fail until frontend wired)**

Create `frontend/tests/e2e/task-workspace.spec.ts`:

```typescript
import { test, expect } from "@playwright/test";

test.describe("task workspace", () => {
  test("public task shows agent update banner when source drifts", async ({ page }) => {
    // Precondition: seeded public task with agent_update_available=true
    await page.goto("/tasks/seed-public-1");
    await expect(
      page.getByTestId("agent-update-banner"),
    ).toContainText("Agent 有");
    await page.getByTestId("agent-update-button").click();
    await expect(page.getByTestId("agent-update-banner")).toBeHidden();
  });

  test("imported file shows source link and refresh button", async ({ page }) => {
    await page.goto("/tasks/seed-with-imported");
    const row = page.getByTestId("file-row-imported-1");
    await expect(row.getByTestId("file-source-badge")).toBeVisible();
    await row.getByTestId("file-refresh-button").click();
    await expect(row.getByTestId("file-refresh-toast")).toBeVisible();
  });

  test("conversation tab lists and creates", async ({ page }) => {
    await page.goto("/tasks/seed-public-1");
    await page.getByTestId("conversation-tab").click();
    await expect(page.getByTestId("conversation-list")).toBeVisible();
    await page.getByTestId("new-conversation-button").click();
    await expect(page.getByTestId("conversation-list")).toContainText("新对话");
  });
});
```

- [ ] **Step 2: Wire frontend (iterative, not fully specified here)**

Implementer should:

1. Add route `/tasks/:tid` if not already present
2. Add top-level `<AgentUpdateBanner>` component conditioned on `task.agent_update_available`
3. Add `<FileList>` branch for `scope === "imported"` showing `source_url` link + refresh button
4. Add `<ConversationTab>` with list + create form

Each component only needs enough wiring to make selectors resolve and the API calls succeed — no design polish needed in this task.

- [ ] **Step 3: Run smoke**

Run: `cd frontend && npx playwright test tests/e2e/task-workspace.spec.ts`
Expected: 3 passed.

- [ ] **Step 4: Commit**

```bash
git add frontend/
git commit -m "feat(ui): task workspace smoke — agent banner, imported file, conversation tab"
```

---

## Self-Review

**Spec coverage audit:**

| Spec section | Task(s) |
|---|---|
| 2. 目录结构 / 新文件 | Task 2 (paths), Task 5 (create hook), Task 12 (conversations) |
| 3.1 meta.json 扩展 | Task 5 (via create hook writes), Task 18 (imported_file_count) |
| 3.2 snapshot.json | Task 5, Task 21 |
| 3.3 collaborators roles | Task 3, Task 16 (remove), Task 15 (editor promotion) |
| 3.4 join_requests.json | Task 15, Task 16 |
| 3.5 conversations/INDEX.json | Task 12 |
| 3.6 imported .meta | Task 18 |
| 3.7 skills/INDEX.json | Task 4, Task 5 |
| 4.1 create_task snapshot hook | Task 5 |
| 4.2 build_system_prompt mode-aware | Task 6 |
| 4.3 share/unshare freeze/thaw | Task 7, Task 8 |
| 4.4 refresh button w/ stale guard | Task 10 |
| 4.5 agent_update_available | Task 9 |
| 4.6 multi-conversation + per-cid lock | Task 12, Task 13, Task 14 |
| 4.7 import | Task 17, Task 18 |
| 4.8 refresh imported | Task 19, Task 20 |
| 4.9 card immutability | Task 11 |
| 5. 权限矩阵 | Task 3, enforced across Tasks 10/14/16/20 |
| 6. API 清单 | Tasks 10, 14, 16, 20 |
| 6.3 错误码 | Task 1 |
| 7. 并发 | Tasks 10, 13 |
| 8. 安全 | Task 17 |
| 9. 审计 | Task 22 |
| 10. 测试清单 | Each task has matching tests (20+ test files) |
| 11. 向后兼容 | Task 21 |

**Placeholder scan:** None — all code blocks contain concrete implementations; tests reference real names.

**Type consistency:**
- `TaskRole` enum values match across Task 3, 10, 14, 16, 20
- `derive_task_role` signature consistent (takes `task_meta, collaborators, *, user_id, is_admin`)
- `snapshot_agent_into_task(*, task_id, agent_id)` / `snapshot_skills_into_task(*, task_id, skill_ids)` consistent
- `refresh_task_snapshot(*, task_id, user_id, expected_version)` — signature matches test call sites
- `import_external` / `refresh_imported` parameter naming aligned

**Remaining observations for executor:**
- Task 11 insertion point ("locate where `target['status'] = new_status`") requires reading the current function body; plan is correct but requires light navigation.
- Task 20 note about form-based `task_id` and custom role dependency is the only non-mechanical step — follow it closely.
- Existing `build_system_prompt(agent_id)` callers are left untouched (Task 6 adds `_for_task` as the new entry point). A follow-up migration of callers is out of scope for this plan.

---

## Execution Handoff

**Plan complete and saved to `docs/superpowers/plans/2026-05-12-task-workspace.md`. Two execution options:**

**1. Subagent-Driven (recommended)** — I dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** — Execute tasks in this session using executing-plans, batch execution with checkpoints

**Which approach?**
