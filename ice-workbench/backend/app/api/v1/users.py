from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from ...core.deps import get_current_user
from ...core.errors import ok
from ...core.storage import get_index_db
from ...services.auth_svc import _to_public

router = APIRouter()


@router.get("/me")
async def me(user: dict = Depends(get_current_user)):
    return ok(_to_public(user))


@router.get("/search")
async def search_users(q: str = Query(..., min_length=1), user: dict = Depends(get_current_user)):
    db = get_index_db()
    rows = await db.fetchall(
        """SELECT id, email, name, auth_role, feishu_user_id FROM users_index
        WHERE name LIKE ? OR email LIKE ? LIMIT 20""",
        [f"%{q}%", f"%{q}%"],
    )
    items = [
        {
            "id": r["id"],
            "email": r["email"],
            "name": r["name"],
            "auth_role": r["auth_role"],
            "feishu_bound": bool(r["feishu_user_id"]),
        }
        for r in rows
    ]
    return ok({"items": items, "total": len(items)})
