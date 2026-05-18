from __future__ import annotations

from fastapi import APIRouter, Depends

from ...core.deps import get_current_user
from ...core.errors import ok
from ...services import skill_svc

router = APIRouter()


@router.get("")
async def list_skills(_: dict = Depends(get_current_user)):
    """Public listing — built-ins + admin-published custom skills.

    Used by CreateTask Step 3 to let users tick-bind any available skill.
    """
    items = skill_svc.list_all()
    # Hide tool_entry on the public view; users don't need it.
    sanitized = [
        {
            "id": s["id"],
            "name": s.get("name"),
            "description": s.get("description"),
            "description_zh": s.get("description_zh"),
            "category": s.get("category"),
            "builtin": s.get("builtin", False),
            "enabled": s.get("enabled", True),
        }
        for s in items
        if s.get("enabled", True)
    ]
    return ok({"items": sanitized, "total": len(sanitized)})
