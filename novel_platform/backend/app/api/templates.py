from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.database import get_db
from ..core.deps import get_current_user
from ..models.models import Template

router = APIRouter(prefix="/templates", tags=["templates"])


@router.get("/")
async def list_templates(user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Template).order_by(Template.is_builtin.desc(), Template.created_at.desc()))
    templates = result.scalars().all()
    return [
        {"id": t.id, "name": t.name, "type": t.type, "content": t.content, "is_builtin": t.is_builtin}
        for t in templates
    ]
