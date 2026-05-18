from __future__ import annotations

from pydantic import BaseModel


class NotificationItem(BaseModel):
    id: str
    kind: str
    title: str
    body: str = ""
    action_url: str | None = None
    is_read: bool = False
    created_at: str
