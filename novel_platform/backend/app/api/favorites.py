from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.database import get_db
from ..core.deps import get_current_user
from ..models.models import FavoriteItem

router = APIRouter(prefix="/favorites", tags=["favorites"])


class FavoriteCreate(BaseModel):
    item_type: str  # chapter / character / note / source
    item_id: int


@router.get("/")
async def list_favorites(user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """获取用户的所有收藏"""
    result = await db.execute(
        select(FavoriteItem)
        .where(FavoriteItem.user_id == user.id)
        .order_by(FavoriteItem.created_at.desc())
    )
    favorites = result.scalars().all()
    return [
        {
            "id": f.id,
            "item_type": f.item_type,
            "item_id": f.item_id,
            "created_at": f.created_at.isoformat() if f.created_at else None,
        }
        for f in favorites
    ]


@router.post("/")
async def add_favorite(req: FavoriteCreate, user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """添加收藏"""
    # Check if already favorited
    existing = await db.execute(
        select(FavoriteItem).where(
            FavoriteItem.user_id == user.id,
            FavoriteItem.item_type == req.item_type,
            FavoriteItem.item_id == req.item_id,
        )
    )
    if existing.scalar_one_or_none():
        return {"ok": True, "message": "Already favorited"}

    favorite = FavoriteItem(
        user_id=user.id,
        item_type=req.item_type,
        item_id=req.item_id,
    )
    db.add(favorite)
    await db.commit()

    return {"ok": True}


@router.delete("/")
async def remove_favorite(
    item_type: str,
    item_id: int,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """移除收藏"""
    result = await db.execute(
        select(FavoriteItem).where(
            FavoriteItem.user_id == user.id,
            FavoriteItem.item_type == item_type,
            FavoriteItem.item_id == item_id,
        )
    )
    favorite = result.scalar_one_or_none()
    if not favorite:
        raise HTTPException(status_code=404, detail="Favorite not found")

    await db.delete(favorite)
    await db.commit()
    return {"ok": True}


@router.get("/check")
async def check_favorite(
    item_type: str,
    item_id: int,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """检查是否已收藏"""
    result = await db.execute(
        select(FavoriteItem).where(
            FavoriteItem.user_id == user.id,
            FavoriteItem.item_type == item_type,
            FavoriteItem.item_id == item_id,
        )
    )
    return {"favorited": result.scalar_one_or_none() is not None}
