from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.database import get_db
from ..core.deps import get_current_user
from ..models.models import Snippet

router = APIRouter(prefix="/snippets", tags=["snippets"])


class SnippetCreate(BaseModel):
    title: str
    content: str
    category: str = "general"  # scene / dialogue / description / general
    tags: str = ""


class SnippetUpdate(BaseModel):
    title: str | None = None
    content: str | None = None
    category: str | None = None
    tags: str | None = None


@router.get("/")
async def list_snippets(user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """获取用户的所有片段"""
    result = await db.execute(
        select(Snippet)
        .where(Snippet.user_id == user.id)
        .order_by(Snippet.usage_count.desc())
    )
    snippets = result.scalars().all()
    return [
        {
            "id": s.id,
            "title": s.title,
            "content": s.content,
            "category": s.category,
            "tags": s.tags,
            "usage_count": s.usage_count,
            "created_at": s.created_at.isoformat() if s.created_at else None,
        }
        for s in snippets
    ]


@router.get("/by-category/{category}")
async def list_by_category(category: str, user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """按分类获取片段"""
    result = await db.execute(
        select(Snippet)
        .where(Snippet.user_id == user.id, Snippet.category == category)
        .order_by(Snippet.usage_count.desc())
    )
    snippets = result.scalars().all()
    return [
        {
            "id": s.id,
            "title": s.title,
            "content": s.content,
            "category": s.category,
            "tags": s.tags,
            "usage_count": s.usage_count,
        }
        for s in snippets
    ]


@router.post("/")
async def create_snippet(req: SnippetCreate, user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """创建片段"""
    snippet = Snippet(
        user_id=user.id,
        title=req.title,
        content=req.content,
        category=req.category,
        tags=req.tags,
    )
    db.add(snippet)
    await db.commit()
    await db.refresh(snippet)

    return {
        "id": snippet.id,
        "title": snippet.title,
        "content": snippet.content,
        "category": snippet.category,
    }


@router.patch("/{snippet_id}")
async def update_snippet(snippet_id: int, req: SnippetUpdate, user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """更新片段"""
    result = await db.execute(
        select(Snippet).where(Snippet.id == snippet_id, Snippet.user_id == user.id)
    )
    snippet = result.scalar_one_or_none()
    if not snippet:
        raise HTTPException(status_code=404, detail="Snippet not found")

    if req.title is not None:
        snippet.title = req.title
    if req.content is not None:
        snippet.content = req.content
    if req.category is not None:
        snippet.category = req.category
    if req.tags is not None:
        snippet.tags = req.tags

    await db.commit()
    return {"ok": True}


@router.post("/{snippet_id}/use")
async def use_snippet(snippet_id: int, user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """使用片段（增加使用次数）"""
    result = await db.execute(
        select(Snippet).where(Snippet.id == snippet_id, Snippet.user_id == user.id)
    )
    snippet = result.scalar_one_or_none()
    if not snippet:
        raise HTTPException(status_code=404, detail="Snippet not found")

    snippet.usage_count += 1
    await db.commit()

    return {"ok": True, "content": snippet.content}


@router.delete("/{snippet_id}")
async def delete_snippet(snippet_id: int, user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """删除片段"""
    result = await db.execute(
        select(Snippet).where(Snippet.id == snippet_id, Snippet.user_id == user.id)
    )
    snippet = result.scalar_one_or_none()
    if not snippet:
        raise HTTPException(status_code=404, detail="Snippet not found")

    await db.delete(snippet)
    await db.commit()
    return {"ok": True}
