from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .database import get_db


async def get_current_user(db: AsyncSession = Depends(get_db)):
    from ..models.models import User

    result = await db.execute(select(User).where(User.status == "active").limit(1))
    user = result.scalar_one_or_none()
    return user


async def require_admin(user=Depends(get_current_user)):
    return user
