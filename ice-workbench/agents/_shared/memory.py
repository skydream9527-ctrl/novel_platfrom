from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

MAX_RECENT_MESSAGES = 20
MEMORY_SUMMARY_MAX_CHARS = 2000


@dataclass
class SessionMessage:
    role: str
    content: str
    metadata: dict[str, Any] = field(default_factory=dict)


class SessionStore:
    def __init__(self, storage_dir: Path | None = None):
        self._sessions: dict[str, list[SessionMessage]] = {}
        self._storage_dir = storage_dir
        if storage_dir:
            storage_dir.mkdir(parents=True, exist_ok=True)

    def get_messages(self, session_id: str, limit: int = MAX_RECENT_MESSAGES) -> list[dict]:
        messages = self._sessions.get(session_id, [])
        recent = messages[-limit:] if len(messages) > limit else messages
        return [{"role": m.role, "content": m.content} for m in recent]

    def add_message(self, session_id: str, role: str, content: str, metadata: dict | None = None) -> None:
        if session_id not in self._sessions:
            self._sessions[session_id] = []
        self._sessions[session_id].append(
            SessionMessage(role=role, content=content, metadata=metadata or {})
        )

    def get_recent_memory(self, session_id: str) -> str:
        messages = self._sessions.get(session_id, [])
        if not messages:
            return ""

        summary_parts = []
        for msg in messages[-10:]:
            prefix = "用户" if msg.role == "user" else "助手"
            text = msg.content[:200]
            summary_parts.append(f"{prefix}: {text}")

        summary = "\n".join(summary_parts)
        if len(summary) > MEMORY_SUMMARY_MAX_CHARS:
            summary = summary[:MEMORY_SUMMARY_MAX_CHARS] + "..."
        return summary

    def clear_session(self, session_id: str) -> None:
        self._sessions.pop(session_id, None)

    def save_to_disk(self, session_id: str) -> None:
        if not self._storage_dir:
            return
        messages = self._sessions.get(session_id, [])
        data = [{"role": m.role, "content": m.content, "metadata": m.metadata} for m in messages]
        path = self._storage_dir / f"{session_id}.json"
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2))

    def load_from_disk(self, session_id: str) -> bool:
        if not self._storage_dir:
            return False
        path = self._storage_dir / f"{session_id}.json"
        if not path.exists():
            return False
        try:
            data = json.loads(path.read_text())
            self._sessions[session_id] = [
                SessionMessage(role=m["role"], content=m["content"], metadata=m.get("metadata", {}))
                for m in data
            ]
            return True
        except (json.JSONDecodeError, KeyError):
            logger.warning("Failed to load session %s from disk", session_id)
            return False
