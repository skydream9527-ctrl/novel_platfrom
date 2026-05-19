import json
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.database import get_db
from ..core.deps import get_current_user
from ..models.models import TimelineEvent, Task, Chapter, Character

router = APIRouter(prefix="/timeline", tags=["timeline"])


class TimelineEventCreate(BaseModel):
    task_id: int
    chapter_id: int | None = None
    title: str
    description: str = ""
    event_type: str = "scene"  # scene / plot / background / flashback
    story_date: str = ""
    story_date_order: int = 0
    duration: str = ""
    location: str = ""
    characters: list[int] = []
    is_milestone: bool = False


class TimelineEventUpdate(BaseModel):
    chapter_id: int | None = None
    title: str | None = None
    description: str | None = None
    event_type: str | None = None
    story_date: str | None = None
    story_date_order: int | None = None
    duration: str | None = None
    location: str | None = None
    characters: list[int] | None = None
    is_milestone: bool | None = None


class TimelineEventMove(BaseModel):
    new_story_date_order: int


@router.get("/by-task/{task_id}")
async def get_timeline(task_id: int, user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """获取时间线"""
    # 验证任务所有权
    task_result = await db.execute(
        select(Task).where(Task.id == task_id, Task.owner_id == user.id)
    )
    if not task_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Task not found")

    result = await db.execute(
        select(TimelineEvent)
        .where(TimelineEvent.task_id == task_id)
        .order_by(TimelineEvent.story_date_order)
    )
    events = result.scalars().all()

    # 获取角色信息
    events_data = []
    for event in events:
        # 获取关联章节信息
        chapter_info = None
        if event.chapter_id:
            chapter_result = await db.execute(
                select(Chapter).where(Chapter.id == event.chapter_id)
            )
            chapter = chapter_result.scalar_one_or_none()
            if chapter:
                chapter_info = {
                    "id": chapter.id,
                    "title": chapter.title,
                    "order_index": chapter.order_index,
                }

        # 获取角色信息
        character_ids = json.loads(event.characters) if event.characters else []
        characters_info = []
        if character_ids:
            chars_result = await db.execute(
                select(Character).where(Character.id.in_(character_ids))
            )
            characters_info = [
                {"id": c.id, "name": c.name}
                for c in chars_result.scalars().all()
            ]

        events_data.append({
            "id": event.id,
            "task_id": event.task_id,
            "chapter_id": event.chapter_id,
            "title": event.title,
            "description": event.description,
            "event_type": event.event_type,
            "story_date": event.story_date,
            "story_date_order": event.story_date_order,
            "duration": event.duration,
            "location": event.location,
            "is_milestone": event.is_milestone,
            "created_at": event.created_at.isoformat(),
            "updated_at": event.updated_at.isoformat(),
            "chapter": chapter_info,
            "characters": characters_info,
        })

    return events_data


@router.post("/events")
async def create_event(req: TimelineEventCreate, user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """创建时间线事件"""
    # 验证任务所有权
    task_result = await db.execute(
        select(Task).where(Task.id == req.task_id, Task.owner_id == user.id)
    )
    if not task_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Task not found")

    # 如果有关联章节，验证章节存在
    if req.chapter_id:
        chapter_result = await db.execute(
            select(Chapter).where(Chapter.id == req.chapter_id)
        )
        if not chapter_result.scalar_one_or_none():
            raise HTTPException(status_code=404, detail="Chapter not found")

    event = TimelineEvent(
        task_id=req.task_id,
        chapter_id=req.chapter_id,
        title=req.title,
        description=req.description,
        event_type=req.event_type,
        story_date=req.story_date,
        story_date_order=req.story_date_order,
        duration=req.duration,
        location=req.location,
        characters=json.dumps(req.characters),
        is_milestone=req.is_milestone,
    )
    db.add(event)
    await db.commit()
    await db.refresh(event)

    return {
        "id": event.id,
        "title": event.title,
        "event_type": event.event_type,
    }


@router.patch("/events/{event_id}")
async def update_event(event_id: int, req: TimelineEventUpdate, user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """更新时间线事件"""
    result = await db.execute(select(TimelineEvent).where(TimelineEvent.id == event_id))
    event = result.scalar_one_or_none()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    if req.chapter_id is not None:
        event.chapter_id = req.chapter_id
    if req.title is not None:
        event.title = req.title
    if req.description is not None:
        event.description = req.description
    if req.event_type is not None:
        event.event_type = req.event_type
    if req.story_date is not None:
        event.story_date = req.story_date
    if req.story_date_order is not None:
        event.story_date_order = req.story_date_order
    if req.duration is not None:
        event.duration = req.duration
    if req.location is not None:
        event.location = req.location
    if req.characters is not None:
        event.characters = json.dumps(req.characters)
    if req.is_milestone is not None:
        event.is_milestone = req.is_milestone

    await db.commit()

    return {"ok": True}


@router.delete("/events/{event_id}")
async def delete_event(event_id: int, user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """删除时间线事件"""
    result = await db.execute(select(TimelineEvent).where(TimelineEvent.id == event_id))
    event = result.scalar_one_or_none()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    await db.delete(event)
    await db.commit()

    return {"ok": True}


@router.patch("/events/{event_id}/move")
async def move_event(event_id: int, req: TimelineEventMove, user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """移动时间线事件"""
    result = await db.execute(select(TimelineEvent).where(TimelineEvent.id == event_id))
    event = result.scalar_one_or_none()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    event.story_date_order = req.new_story_date_order
    await db.commit()

    return {"ok": True}


@router.post("/from-chapters")
async def generate_from_chapters(task_id: int, user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """从章节自动生成时间线"""
    # 验证任务所有权
    task_result = await db.execute(
        select(Task).where(Task.id == task_id, Task.owner_id == user.id)
    )
    if not task_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Task not found")

    # 获取所有章节
    result = await db.execute(
        select(Chapter)
        .where(Chapter.task_id == task_id)
        .order_by(Chapter.order_index)
    )
    chapters = result.scalars().all()

    # 为每个章节创建时间线事件
    created_count = 0
    for i, chapter in enumerate(chapters):
        # 检查是否已有该章节的事件
        existing = await db.execute(
            select(TimelineEvent).where(
                and_(
                    TimelineEvent.task_id == task_id,
                    TimelineEvent.chapter_id == chapter.id
                )
            )
        )
        if existing.scalar_one_or_none():
            continue

        event = TimelineEvent(
            task_id=task_id,
            chapter_id=chapter.id,
            title=chapter.title,
            description=f"第 {chapter.order_index + 1} 章",
            event_type="scene",
            story_date_order=i,
        )
        db.add(event)
        created_count += 1

    await db.commit()

    return {"created": created_count}


@router.get("/conflicts")
async def check_conflicts(task_id: int, user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """检查时间线冲突"""
    # 验证任务所有权
    task_result = await db.execute(
        select(Task).where(Task.id == task_id, Task.owner_id == user.id)
    )
    if not task_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Task not found")

    # 获取所有事件
    result = await db.execute(
        select(TimelineEvent)
        .where(TimelineEvent.task_id == task_id)
        .order_by(TimelineEvent.story_date_order)
    )
    events = result.scalars().all()

    conflicts = []

    # 检查角色时间冲突
    for i, event1 in enumerate(events):
        chars1 = json.loads(event1.characters) if event1.characters else []
        if not chars1:
            continue

        for j in range(i + 1, len(events)):
            event2 = events[j]
            chars2 = json.loads(event2.characters) if event2.characters else []

            # 检查是否有相同角色
            common_chars = set(chars1) & set(chars2)
            if common_chars and event1.location != event2.location:
                # 获取角色名称
                chars_result = await db.execute(
                    select(Character).where(Character.id.in_(list(common_chars)))
                )
                char_names = [c.name for c in chars_result.scalars().all()]

                conflicts.append({
                    "type": "character_location_conflict",
                    "event1": {
                        "id": event1.id,
                        "title": event1.title,
                        "location": event1.location,
                    },
                    "event2": {
                        "id": event2.id,
                        "title": event2.title,
                        "location": event2.location,
                    },
                    "characters": char_names,
                    "description": f"角色 {', '.join(char_names)} 同时出现在不同地点",
                })

    return {
        "conflicts": conflicts,
        "total": len(conflicts),
    }
