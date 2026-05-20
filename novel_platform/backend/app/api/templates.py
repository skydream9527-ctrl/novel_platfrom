from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.database import get_db
from ..core.deps import get_current_user
from ..models.models import Template, User

router = APIRouter(prefix="/templates", tags=["templates"])


class TemplateCreate(BaseModel):
    name: str
    type: str
    content: str
    is_public: bool = False


class TemplateUpdate(BaseModel):
    name: str | None = None
    content: str | None = None
    is_public: bool | None = None


@router.get("/")
async def list_templates(user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Template).order_by(Template.is_builtin.desc(), Template.created_at.desc()))
    templates = result.scalars().all()
    return [
        {
            "id": t.id,
            "name": t.name,
            "type": t.type,
            "content": t.content,
            "is_builtin": t.is_builtin,
            "is_public": t.is_public,
            "author_id": t.author_id,
            "created_at": t.created_at.isoformat() if t.created_at else None,
        }
        for t in templates
    ]


@router.get("/public")
async def list_public_templates(user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """获取公共模板列表"""
    result = await db.execute(
        select(Template, User.name)
        .join(User, Template.author_id == User.id, isouter=True)
        .where(Template.is_public == True)
        .order_by(Template.created_at.desc())
    )
    rows = result.all()
    return [
        {
            "id": t.id,
            "name": t.name,
            "type": t.type,
            "content": t.content,
            "is_builtin": t.is_builtin,
            "author_name": author_name or "系统",
            "created_at": t.created_at.isoformat() if t.created_at else None,
        }
        for t, author_name in rows
    ]


@router.post("/")
async def create_template(req: TemplateCreate, user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """创建新模板"""
    template = Template(
        name=req.name,
        type=req.type,
        content=req.content,
        is_public=req.is_public,
        author_id=user.id,
        is_builtin=0,
    )
    db.add(template)
    await db.commit()
    await db.refresh(template)

    return {"id": template.id, "name": template.name, "type": template.type}


@router.patch("/{template_id}")
async def update_template(
    template_id: int,
    req: TemplateUpdate,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """更新模板"""
    result = await db.execute(
        select(Template).where(Template.id == template_id, Template.author_id == user.id)
    )
    template = result.scalar_one_or_none()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    if req.name is not None:
        template.name = req.name
    if req.content is not None:
        template.content = req.content
    if req.is_public is not None:
        template.is_public = req.is_public
    await db.commit()

    return {"ok": True}


@router.delete("/{template_id}")
async def delete_template(template_id: int, user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """删除模板"""
    result = await db.execute(
        select(Template).where(Template.id == template_id, Template.author_id == user.id)
    )
    template = result.scalar_one_or_none()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    await db.delete(template)
    await db.commit()

    return {"ok": True}


@router.post("/{template_id}/fork")
async def fork_template(template_id: int, user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """复制模板到自己的模板库"""
    result = await db.execute(select(Template).where(Template.id == template_id))
    template = result.scalar_one_or_none()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    new_template = Template(
        name=f"{template.name} (副本)",
        type=template.type,
        content=template.content,
        is_public=False,
        author_id=user.id,
        is_builtin=0,
    )
    db.add(new_template)
    await db.commit()
    await db.refresh(new_template)

    return {"id": new_template.id, "name": new_template.name}
