from __future__ import annotations

from fastapi import APIRouter, Depends

from ...core.deps import get_current_user
from ...core.errors import APIError, ErrorCode, ok
from ...services import agents_svc

router = APIRouter()


@router.get("")
async def list_agents(_: dict = Depends(get_current_user)):
    items = agents_svc.list_agents()
    return ok({"items": items, "total": len(items)})


@router.get("/{agent_id}")
async def get_agent(agent_id: str, _: dict = Depends(get_current_user)):
    a = agents_svc.get_agent(agent_id)
    if not a:
        raise APIError(404, ErrorCode.RESOURCE_NOT_FOUND, "Agent 不存在")
    return ok(a)
