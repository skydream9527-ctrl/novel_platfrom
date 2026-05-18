from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class TaskCreate(BaseModel):
    name: str = Field(..., max_length=120)
    paradigm: str = Field(..., description="biz|ab|wave|data|gray|general")
    agent_id: str | None = None
    description: str | None = None
    initial_prompt: str | None = None
    skill_ids: list[str] = []
    visibility: str = "private"


class TaskSummary(BaseModel):
    id: str
    name: str
    paradigm: str
    agent_id: str | None
    owner_id: str
    status: str
    visibility: str
    file_count: int = 0
    last_message_preview: str | None = None
    updated_at: str | None = None
    created_at: str | None = None
    role: str = "owner"


class TaskDetail(TaskSummary):
    description: str | None = None
    initial_prompt: str | None = None
    skill_ids: list[str] = []
    collaborators: list[dict[str, Any]] = []
    workspace: dict[str, Any] = {}
