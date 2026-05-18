from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from ...core.deps import get_current_user
from ...core.errors import ok
from ...core.storage import get_index_db
from ...services import agents_svc, file_svc

router = APIRouter()


@router.get("")
async def search(
    q: str = Query(..., min_length=1),
    type: str | None = Query(None),
    user: dict = Depends(get_current_user),
):
    db = get_index_db()
    out: dict[str, list[dict]] = {"tasks": [], "agents": [], "skills": [], "files": []}
    if type in (None, "task"):
        rows = await db.fetchall(
            "SELECT id, name, paradigm, owner_id FROM tasks_index WHERE name LIKE ? LIMIT 20",
            [f"%{q}%"],
        )
        out["tasks"] = [{"id": r["id"], "name": r["name"], "paradigm": r["paradigm"]} for r in rows]
    if type in (None, "agent"):
        out["agents"] = [a for a in agents_svc.list_agents() if q.lower() in a["name"].lower()]
    if type in (None, "skill"):
        out["skills"] = [s for s in agents_svc.list_skills() if q.lower() in s["name"].lower()]
    if type in (None, "file"):
        out["files"] = [
            f for f in await file_svc.list_public_files() if q.lower() in f["name"].lower()
        ]
    return ok(out)
