from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.database import get_db
from ..core.deps import get_current_user
from ..models.models import CanvasCard, CanvasConnection, Task

router = APIRouter(prefix="/canvas", tags=["canvas"])


class CardCreate(BaseModel):
    task_id: int
    title: str
    content: str = ""
    card_type: str = "note"  # note / scene / character / event / idea
    x: float = 100
    y: float = 100
    width: float = 200
    height: float = 150
    color: str = "#ffffff"


class CardUpdate(BaseModel):
    title: str | None = None
    content: str | None = None
    card_type: str | None = None
    x: float | None = None
    y: float | None = None
    width: float | None = None
    height: float | None = None
    color: str | None = None


class ConnectionCreate(BaseModel):
    task_id: int
    source_card_id: int
    target_card_id: int
    label: str = ""
    connection_type: str = "related"  # related / causes / leads_to / part_of


class ConnectionUpdate(BaseModel):
    label: str | None = None
    connection_type: str | None = None


@router.get("/by-task/{task_id}")
async def list_canvas(task_id: int, user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """获取任务的画布数据"""
    task = await db.execute(select(Task).where(Task.id == task_id, Task.owner_id == user.id))
    if not task.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Task not found")

    # Get cards
    cards_result = await db.execute(
        select(CanvasCard).where(CanvasCard.task_id == task_id)
    )
    cards = cards_result.scalars().all()

    # Get connections
    conns_result = await db.execute(
        select(CanvasConnection).where(CanvasConnection.task_id == task_id)
    )
    connections = conns_result.scalars().all()

    return {
        "cards": [
            {
                "id": c.id,
                "title": c.title,
                "content": c.content,
                "card_type": c.card_type,
                "x": c.x,
                "y": c.y,
                "width": c.width,
                "height": c.height,
                "color": c.color,
                "created_at": c.created_at.isoformat() if c.created_at else None,
            }
            for c in cards
        ],
        "connections": [
            {
                "id": c.id,
                "source_card_id": c.source_card_id,
                "target_card_id": c.target_card_id,
                "label": c.label,
                "connection_type": c.connection_type,
            }
            for c in connections
        ],
    }


@router.post("/cards")
async def create_card(req: CardCreate, user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """创建画布卡片"""
    task = await db.execute(select(Task).where(Task.id == req.task_id, Task.owner_id == user.id))
    if not task.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Task not found")

    card = CanvasCard(
        task_id=req.task_id,
        title=req.title,
        content=req.content,
        card_type=req.card_type,
        x=req.x,
        y=req.y,
        width=req.width,
        height=req.height,
        color=req.color,
    )
    db.add(card)
    await db.commit()
    await db.refresh(card)

    return {
        "id": card.id,
        "title": card.title,
        "content": card.content,
        "card_type": card.card_type,
        "x": card.x,
        "y": card.y,
        "width": card.width,
        "height": card.height,
        "color": card.color,
    }


@router.patch("/cards/{card_id}")
async def update_card(card_id: int, req: CardUpdate, user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """更新画布卡片"""
    result = await db.execute(
        select(CanvasCard).join(Task).where(CanvasCard.id == card_id, Task.owner_id == user.id)
    )
    card = result.scalar_one_or_none()
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")

    if req.title is not None:
        card.title = req.title
    if req.content is not None:
        card.content = req.content
    if req.card_type is not None:
        card.card_type = req.card_type
    if req.x is not None:
        card.x = req.x
    if req.y is not None:
        card.y = req.y
    if req.width is not None:
        card.width = req.width
    if req.height is not None:
        card.height = req.height
    if req.color is not None:
        card.color = req.color

    await db.commit()
    return {"ok": True}


@router.delete("/cards/{card_id}")
async def delete_card(card_id: int, user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """删除画布卡片"""
    result = await db.execute(
        select(CanvasCard).join(Task).where(CanvasCard.id == card_id, Task.owner_id == user.id)
    )
    card = result.scalar_one_or_none()
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")

    # Delete related connections
    conns = await db.execute(
        select(CanvasConnection).where(
            (CanvasConnection.source_card_id == card_id) | (CanvasConnection.target_card_id == card_id)
        )
    )
    for conn in conns.scalars().all():
        await db.delete(conn)

    await db.delete(card)
    await db.commit()
    return {"ok": True}


@router.post("/connections")
async def create_connection(req: ConnectionCreate, user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """创建卡片连接"""
    task = await db.execute(select(Task).where(Task.id == req.task_id, Task.owner_id == user.id))
    if not task.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Task not found")

    conn = CanvasConnection(
        task_id=req.task_id,
        source_card_id=req.source_card_id,
        target_card_id=req.target_card_id,
        label=req.label,
        connection_type=req.connection_type,
    )
    db.add(conn)
    await db.commit()
    await db.refresh(conn)

    return {
        "id": conn.id,
        "source_card_id": conn.source_card_id,
        "target_card_id": conn.target_card_id,
        "label": conn.label,
        "connection_type": conn.connection_type,
    }


@router.patch("/connections/{connection_id}")
async def update_connection(connection_id: int, req: ConnectionUpdate, user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """更新卡片连接"""
    result = await db.execute(
        select(CanvasConnection).join(Task).where(CanvasConnection.id == connection_id, Task.owner_id == user.id)
    )
    conn = result.scalar_one_or_none()
    if not conn:
        raise HTTPException(status_code=404, detail="Connection not found")

    if req.label is not None:
        conn.label = req.label
    if req.connection_type is not None:
        conn.connection_type = req.connection_type

    await db.commit()
    return {"ok": True}


@router.delete("/connections/{connection_id}")
async def delete_connection(connection_id: int, user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """删除卡片连接"""
    result = await db.execute(
        select(CanvasConnection).join(Task).where(CanvasConnection.id == connection_id, Task.owner_id == user.id)
    )
    conn = result.scalar_one_or_none()
    if not conn:
        raise HTTPException(status_code=404, detail="Connection not found")

    await db.delete(conn)
    await db.commit()
    return {"ok": True}
