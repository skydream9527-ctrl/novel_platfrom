"""Top-level directory resolution per BACKEND.md §1."""
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from ..config import get_settings


@dataclass(frozen=True)
class StoragePaths:
    root: Path

    @property
    def agents(self) -> Path:
        return self.root / "agents"

    @property
    def skills(self) -> Path:
        return self.root / "skills"

    @property
    def files(self) -> Path:
        return self.root / "files"

    @property
    def users(self) -> Path:
        return self.root / "users"

    @property
    def tasks(self) -> Path:
        return self.root / "tasks"

    @property
    def cache(self) -> Path:
        return self.root / ".cache"

    def user_dir(self, user_id: str) -> Path:
        return self.users / user_id

    def user_profile(self, user_id: str) -> Path:
        return self.user_dir(user_id) / "profile.json"

    def user_settings(self, user_id: str) -> Path:
        return self.user_dir(user_id) / "settings.json"

    def user_tasks_index(self, user_id: str) -> Path:
        return self.user_dir(user_id) / "tasks" / "index.json"

    def user_notifications(self, user_id: str, ym: str) -> Path:
        return self.user_dir(user_id) / "notifications" / f"{ym}.jsonl"

    def task_dir(self, task_id: str) -> Path:
        return self.tasks / task_id

    def task_meta(self, task_id: str) -> Path:
        return self.task_dir(task_id) / "meta.json"

    def task_workspace(self, task_id: str) -> Path:
        return self.task_dir(task_id) / "workspace.json"

    def task_collaborators(self, task_id: str) -> Path:
        return self.task_dir(task_id) / "collaborators.json"

    def task_experience_cards(self, task_id: str) -> Path:
        return self.task_dir(task_id) / "experience_cards.json"

    def task_conversation(self, task_id: str, conv_id: str) -> Path:
        return self.task_dir(task_id) / "conversations" / f"{conv_id}.jsonl"

    def task_tool_calls(self, task_id: str, conv_id: str) -> Path:
        return self.task_dir(task_id) / "tool_calls" / f"{conv_id}.jsonl"

    def task_files_input(self, task_id: str) -> Path:
        return self.task_dir(task_id) / "files" / "input"

    def task_files_output(self, task_id: str) -> Path:
        return self.task_dir(task_id) / "files" / "output"

    def task_files_uploaded(self, task_id: str) -> Path:
        return self.task_dir(task_id) / "files" / "uploaded"

    def task_files_meta(self, task_id: str) -> Path:
        return self.task_dir(task_id) / "files" / ".meta"

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


@lru_cache
def get_paths() -> StoragePaths:
    return StoragePaths(root=get_settings().DATA_ROOT)


def ensure_layout() -> None:
    p = get_paths()
    for d in (p.agents, p.skills, p.files, p.users, p.tasks, p.cache):
        d.mkdir(parents=True, exist_ok=True)
