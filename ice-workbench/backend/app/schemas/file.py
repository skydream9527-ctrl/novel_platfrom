from __future__ import annotations

from pydantic import BaseModel


class FileMeta(BaseModel):
    id: str
    name: str
    path: str
    scope: str
    task_id: str | None = None
    file_type: str | None = None
    format: str | None = None
    size_bytes: int = 0
    is_pinned: bool = False
    created_at: str | None = None
