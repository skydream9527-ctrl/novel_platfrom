"""/admin/usage — daily trend, by-dimension, monthly summary, CSV."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response

from ...core.deps import require_admin
from ...core.errors import ok
from ...services import usage_svc

router = APIRouter()


@router.get("/summary")
async def summary(_: dict = Depends(require_admin)):
    return ok(await usage_svc.month_summary())


@router.get("/daily")
async def daily(days: int = Query(30, ge=1, le=180), _: dict = Depends(require_admin)):
    return ok({"items": await usage_svc.daily_trend(days=days)})


@router.get("/by-dimension")
async def by_dim(
    dimension: str = Query(..., description="model|user_id|agent_id|task_id"),
    days: int = Query(30, ge=1, le=180),
    limit: int = Query(20, ge=1, le=100),
    _: dict = Depends(require_admin),
):
    return ok({"items": await usage_svc.by_dimension(dimension=dimension, days=days, limit=limit)})


@router.get("/export.csv")
async def export_csv(days: int = Query(30, ge=1, le=180), _: dict = Depends(require_admin)):
    body = await usage_svc.export_csv(days=days)
    return Response(
        content=body,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=usage-{days}d.csv"},
    )
