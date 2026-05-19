from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.database import get_db
from ..core.deps import get_current_user
from ..models.models import Chapter, ChapterVersion, Task, WritingLog
from ..utils.file_sync import delete_chapter_file, get_task_dir, sync_chapter_to_file

router = APIRouter(prefix="/chapters", tags=["chapters"])


class ChapterCreate(BaseModel):
    task_id: int
    title: str = "新章节"
    content: str = ""
    status: str = "draft"


class ChapterUpdate(BaseModel):
    title: str | None = None
    content: str | None = None
    order_index: int | None = None
    status: str | None = None
    scheduled_date: datetime | None = None
    completed_date: datetime | None = None


@router.get("/by-task/{task_id}")
async def list_chapters(
    task_id: int,
    view: str = Query("list", description="视图类型: list/kanban/calendar/timeline"),
    status: str | None = Query(None, description="按状态筛选"),
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Verify task ownership
    task = await db.execute(select(Task).where(Task.id == task_id, Task.owner_id == user.id))
    if not task.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Task not found")

    # 构建查询
    query = select(Chapter).where(Chapter.task_id == task_id)

    # 按状态筛选
    if status:
        query = query.where(Chapter.status == status)

    # 根据视图类型排序
    if view == "timeline":
        query = query.order_by(Chapter.order_index)
    elif view == "calendar":
        query = query.order_by(Chapter.created_at.desc())
    else:
        query = query.order_by(Chapter.order_index)

    result = await db.execute(query)
    chapters = result.scalars().all()

    return [
        {
            "id": c.id,
            "title": c.title,
            "content": c.content,
            "order_index": c.order_index,
            "version": c.version,
            "status": c.status,
            "scheduled_date": c.scheduled_date.isoformat() if c.scheduled_date else None,
            "completed_date": c.completed_date.isoformat() if c.completed_date else None,
            "word_count": len(c.content) if c.content else 0,
            "updated_at": c.updated_at.isoformat() if c.updated_at else None,
            "created_at": c.created_at.isoformat() if c.created_at else None,
        }
        for c in chapters
    ]


@router.get("/by-task/{task_id}/stats")
async def get_chapter_stats(task_id: int, user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """获取章节统计数据"""
    # Verify task ownership
    task = await db.execute(select(Task).where(Task.id == task_id, Task.owner_id == user.id))
    if not task.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Task not found")

    # 统计各状态的章节数量
    result = await db.execute(
        select(
            Chapter.status,
            func.count(Chapter.id).label("count")
        ).where(Chapter.task_id == task_id).group_by(Chapter.status)
    )
    stats = {row.status: row.count for row in result.all()}

    # 计算总字数
    result = await db.execute(
        select(func.sum(func.length(Chapter.content))).where(Chapter.task_id == task_id)
    )
    total_words = result.scalar() or 0

    return {
        "status_counts": stats,
        "total_chapters": sum(stats.values()),
        "total_words": total_words,
    }


@router.get("/{chapter_id}")
async def get_chapter(chapter_id: int, user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Chapter).where(Chapter.id == chapter_id).join(Task).where(Task.owner_id == user.id)
    )
    chapter = result.scalar_one_or_none()
    if not chapter:
        raise HTTPException(status_code=404, detail="Chapter not found")
    return {
        "id": chapter.id,
        "task_id": chapter.task_id,
        "title": chapter.title,
        "content": chapter.content,
        "order_index": chapter.order_index,
        "version": chapter.version,
        "updated_at": chapter.updated_at.isoformat() if chapter.updated_at else None,
    }


@router.post("/")
async def create_chapter(req: ChapterCreate, user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Task).where(Task.id == req.task_id, Task.owner_id == user.id))
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    # Get max order_index
    result = await db.execute(
        select(Chapter.order_index).where(Chapter.task_id == req.task_id).order_by(Chapter.order_index.desc())
    )
    max_idx = result.scalar()
    next_idx = (max_idx + 1) if max_idx is not None else 0

    chapter = Chapter(
        task_id=req.task_id,
        title=req.title,
        content=req.content,
        order_index=next_idx,
        status=req.status
    )
    db.add(chapter)
    await db.commit()
    await db.refresh(chapter)

    if task.directory_path:
        sync_chapter_to_file(task.directory_path, chapter)

    return {
        "id": chapter.id,
        "title": chapter.title,
        "order_index": chapter.order_index,
        "status": chapter.status,
    }


@router.patch("/{chapter_id}")
async def update_chapter(
    chapter_id: int, req: ChapterUpdate, user=Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Chapter).where(Chapter.id == chapter_id).join(Task).where(Task.owner_id == user.id)
    )
    chapter = result.scalar_one_or_none()
    if not chapter:
        raise HTTPException(status_code=404, detail="Chapter not found")

    if req.title is not None:
        chapter.title = req.title
    if req.content is not None:
        # Save current version before updating
        ver = ChapterVersion(
            chapter_id=chapter.id,
            version=chapter.version,
            title=chapter.title,
            content=chapter.content,
        )
        db.add(ver)
        chapter.content = req.content
        chapter.version += 1
    if req.order_index is not None:
        chapter.order_index = req.order_index
    if req.status is not None:
        chapter.status = req.status
        # 如果状态变为 final，记录完成日期
        if req.status == "final" and not chapter.completed_date:
            chapter.completed_date = datetime.now()
    if req.scheduled_date is not None:
        chapter.scheduled_date = req.scheduled_date
    if req.completed_date is not None:
        chapter.completed_date = req.completed_date

    await db.commit()

    dir_path = await get_task_dir(db, chapter.task_id)
    if dir_path:
        sync_chapter_to_file(dir_path, chapter)

    return {"ok": True, "version": chapter.version, "status": chapter.status}


@router.get("/{chapter_id}/versions")
async def list_versions(chapter_id: int, user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Chapter).where(Chapter.id == chapter_id).join(Task).where(Task.owner_id == user.id)
    )
    chapter = result.scalar_one_or_none()
    if not chapter:
        raise HTTPException(status_code=404, detail="Chapter not found")

    result = await db.execute(
        select(ChapterVersion)
        .where(ChapterVersion.chapter_id == chapter_id)
        .order_by(ChapterVersion.version.desc())
    )
    versions = result.scalars().all()
    return [
        {
            "id": v.id,
            "version": v.version,
            "title": v.title,
            "created_at": v.created_at.isoformat() if v.created_at else None,
        }
        for v in versions
    ]


@router.get("/{chapter_id}/versions/{version}")
async def get_version(chapter_id: int, version: int, user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Chapter).where(Chapter.id == chapter_id).join(Task).where(Task.owner_id == user.id)
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Chapter not found")

    result = await db.execute(
        select(ChapterVersion).where(
            ChapterVersion.chapter_id == chapter_id, ChapterVersion.version == version
        )
    )
    ver = result.scalar_one_or_none()
    if not ver:
        raise HTTPException(status_code=404, detail="Version not found")
    return {
        "id": ver.id,
        "version": ver.version,
        "title": ver.title,
        "content": ver.content,
        "created_at": ver.created_at.isoformat() if ver.created_at else None,
    }


@router.post("/{chapter_id}/restore/{version}")
async def restore_version(chapter_id: int, version: int, user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Chapter).where(Chapter.id == chapter_id).join(Task).where(Task.owner_id == user.id)
    )
    chapter = result.scalar_one_or_none()
    if not chapter:
        raise HTTPException(status_code=404, detail="Chapter not found")

    result = await db.execute(
        select(ChapterVersion).where(
            ChapterVersion.chapter_id == chapter_id, ChapterVersion.version == version
        )
    )
    ver = result.scalar_one_or_none()
    if not ver:
        raise HTTPException(status_code=404, detail="Version not found")

    # Save current state as a new version before restoring
    current_ver = ChapterVersion(
        chapter_id=chapter.id,
        version=chapter.version,
        title=chapter.title,
        content=chapter.content,
    )
    db.add(current_ver)

    chapter.title = ver.title
    chapter.content = ver.content
    chapter.version += 1
    await db.commit()

    dir_path = await get_task_dir(db, chapter.task_id)
    if dir_path:
        sync_chapter_to_file(dir_path, chapter)

    return {"ok": True, "version": chapter.version}


@router.delete("/{chapter_id}")
async def delete_chapter(chapter_id: int, user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Chapter).where(Chapter.id == chapter_id).join(Task).where(Task.owner_id == user.id)
    )
    chapter = result.scalar_one_or_none()
    if not chapter:
        raise HTTPException(status_code=404, detail="Chapter not found")

    old_order = chapter.order_index
    old_title = chapter.title
    task_id = chapter.task_id

    await db.delete(chapter)
    await db.commit()

    dir_path = await get_task_dir(db, task_id)
    if dir_path:
        delete_chapter_file(dir_path, old_order, old_title)

    return {"ok": True}


class BatchStatusUpdate(BaseModel):
    chapter_ids: list[int]
    status: str


@router.patch("/batch/status")
async def batch_update_status(
    req: BatchStatusUpdate,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """批量更新章节状态"""
    updated_count = 0
    for chapter_id in req.chapter_ids:
        result = await db.execute(
            select(Chapter).where(Chapter.id == chapter_id).join(Task).where(Task.owner_id == user.id)
        )
        chapter = result.scalar_one_or_none()
        if chapter:
            chapter.status = req.status
            if req.status == "final" and not chapter.completed_date:
                chapter.completed_date = datetime.now()
            updated_count += 1

    await db.commit()

    return {"updated": updated_count}


class ReorderRequest(BaseModel):
    chapter_orders: list[dict]  # [{"id": 1, "order_index": 0}, ...]


@router.patch("/reorder")
async def reorder_chapters(
    req: ReorderRequest,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """批量更新章节顺序"""
    for item in req.chapter_orders:
        result = await db.execute(
            select(Chapter).where(Chapter.id == item["id"]).join(Task).where(Task.owner_id == user.id)
        )
        chapter = result.scalar_one_or_none()
        if chapter:
            chapter.order_index = item["order_index"]

    await db.commit()

    return {"ok": True}
