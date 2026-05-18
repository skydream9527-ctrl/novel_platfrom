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
from datetime import datetime, timezone

from ..core.errors import APIError, ErrorCode
from ..core.storage import file_transaction, get_paths, read_json, write_json
from . import skill_svc


def _now() -> str:
    return datetime.now(tz=timezone.utc).isoformat()


def compute_agent_version(agent_id: str) -> str | None:
    paths = get_paths()
    pdir = paths.agents / agent_id / "prompt"
    if not pdir.exists():
        return None
    md_files = sorted(pdir.glob("*.md"))
    if not md_files:
        return None
    h = hashlib.sha256()
    for md in md_files:
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
                entry["source_version"] = hashlib.sha256(src.read_bytes()).hexdigest()
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

    try:
        from . import admin_svc
        await admin_svc.audit(
            admin_id=user_id,
            action="refresh_task_agent_snapshot",
            target_type="task",
            target_id=task_id,
            diff={"before": current_version, "after": new_version, "diff": diff_summary},
        )
    except Exception:
        pass  # audit must never block business path

    return {"changed": True, "new_version": new_version, "diff_summary": diff_summary}


def _safe_read_text(path) -> str:
    try:
        return path.read_text()
    except (FileNotFoundError, OSError):
        return ""
