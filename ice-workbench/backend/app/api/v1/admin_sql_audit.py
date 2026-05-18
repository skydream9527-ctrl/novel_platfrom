"""/admin/sql-audit — list, stats, CSV."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response

from ...core.deps import require_admin
from ...core.errors import ok
from ...services import sql_audit_svc

router = APIRouter()


@router.get("")
async def list_logs(
    decision: str | None = Query(None),
    user_id: str | None = Query(None),
    agent_id: str | None = Query(None),
    task_id: str | None = Query(None),
    q: str | None = Query(None),
    days: int = Query(30, ge=1, le=180),
    limit: int = Query(200, ge=1, le=1000),
    _: dict = Depends(require_admin),
):
    items = await sql_audit_svc.list_logs(
        decision=decision, user_id=user_id, agent_id=agent_id,
        task_id=task_id, q=q, days=days, limit=limit,
    )
    return ok({"items": items, "total": len(items)})


@router.get("/stats")
async def stats(days: int = Query(30, ge=1, le=180), _: dict = Depends(require_admin)):
    return ok(await sql_audit_svc.stats(days=days))


@router.get("/export.csv")
async def export_csv(days: int = Query(30, ge=1, le=180), _: dict = Depends(require_admin)):
    body = await sql_audit_svc.export_csv(days=days)
    return Response(
        content=body,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=sql-audit-{days}d.csv"},
    )
