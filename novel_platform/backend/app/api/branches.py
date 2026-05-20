from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.database import get_db
from ..core.deps import get_current_user
from ..models.models import Chapter, ChapterBranch, Task

router = APIRouter(prefix="/branches", tags=["branches"])


class BranchCreate(BaseModel):
    chapter_id: int
    name: str
    content: str = ""


class BranchUpdate(BaseModel):
    name: str | None = None
    content: str | None = None


@router.get("/by-chapter/{chapter_id}")
async def list_branches(chapter_id: int, user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """获取章节的所有分支"""
    # Verify ownership
    result = await db.execute(
        select(Chapter).where(Chapter.id == chapter_id).join(Task).where(Task.owner_id == user.id)
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Chapter not found")

    result = await db.execute(
        select(ChapterBranch)
        .where(ChapterBranch.chapter_id == chapter_id)
        .order_by(ChapterBranch.created_at.desc())
    )
    branches = result.scalars().all()
    return [
        {
            "id": b.id,
            "chapter_id": b.chapter_id,
            "name": b.name,
            "content": b.content,
            "is_active": b.is_active,
            "created_at": b.created_at.isoformat() if b.created_at else None,
        }
        for b in branches
    ]


@router.post("/")
async def create_branch(req: BranchCreate, user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """创建分支"""
    # Verify ownership
    result = await db.execute(
        select(Chapter).where(Chapter.id == req.chapter_id).join(Task).where(Task.owner_id == user.id)
    )
    chapter = result.scalar_one_or_none()
    if not chapter:
        raise HTTPException(status_code=404, detail="Chapter not found")

    # If no content provided, use current chapter content
    content = req.content or chapter.content

    branch = ChapterBranch(
        chapter_id=req.chapter_id,
        name=req.name,
        content=content,
    )
    db.add(branch)
    await db.commit()
    await db.refresh(branch)

    return {
        "id": branch.id,
        "chapter_id": branch.chapter_id,
        "name": branch.name,
        "content": branch.content,
    }


@router.patch("/{branch_id}")
async def update_branch(branch_id: int, req: BranchUpdate, user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """更新分支"""
    result = await db.execute(
        select(ChapterBranch)
        .where(ChapterBranch.id == branch_id)
        .join(Chapter)
        .join(Task)
        .where(Task.owner_id == user.id)
    )
    branch = result.scalar_one_or_none()
    if not branch:
        raise HTTPException(status_code=404, detail="Branch not found")

    if req.name is not None:
        branch.name = req.name
    if req.content is not None:
        branch.content = req.content

    await db.commit()
    return {"ok": True}


@router.post("/{branch_id}/activate")
async def activate_branch(branch_id: int, user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """激活分支（将分支内容应用到章节）"""
    result = await db.execute(
        select(ChapterBranch)
        .where(ChapterBranch.id == branch_id)
        .join(Chapter)
        .join(Task)
        .where(Task.owner_id == user.id)
    )
    branch = result.scalar_one_or_none()
    if not branch:
        raise HTTPException(status_code=404, detail="Branch not found")

    # Get the chapter
    chapter_result = await db.execute(
        select(Chapter).where(Chapter.id == branch.chapter_id)
    )
    chapter = chapter_result.scalar_one_or_none()
    if not chapter:
        raise HTTPException(status_code=404, detail="Chapter not found")

    # Deactivate all branches for this chapter
    all_branches = await db.execute(
        select(ChapterBranch).where(ChapterBranch.chapter_id == branch.chapter_id)
    )
    for b in all_branches.scalars().all():
        b.is_active = 0

    # Activate this branch and update chapter
    branch.is_active = 1
    chapter.content = branch.content

    await db.commit()
    return {"ok": True}


@router.delete("/{branch_id}")
async def delete_branch(branch_id: int, user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """删除分支"""
    result = await db.execute(
        select(ChapterBranch)
        .where(ChapterBranch.id == branch_id)
        .join(Chapter)
        .join(Task)
        .where(Task.owner_id == user.id)
    )
    branch = result.scalar_one_or_none()
    if not branch:
        raise HTTPException(status_code=404, detail="Branch not found")

    await db.delete(branch)
    await db.commit()
    return {"ok": True}
