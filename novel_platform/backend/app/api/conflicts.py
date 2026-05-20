import json
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.database import get_db
from ..core.deps import get_current_user
from ..models.models import Annotation, Chapter, Character, Conflict, Foreshadowing, Task, User

router = APIRouter(prefix="/conflicts", tags=["conflicts"])


class ConflictCreate(BaseModel):
    task_id: int
    title: str
    description: str = ""
    conflict_type: str = "external"  # external / internal / interpersonal
    priority: str = "medium"  # high / medium / low
    introduced_chapter_id: int | None = None
    related_characters: list[int] = []


class ConflictUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    conflict_type: str | None = None
    status: str | None = None
    priority: str | None = None
    introduced_chapter_id: int | None = None
    resolved_chapter_id: int | None = None
    related_characters: list[int] | None = None


class ForeshadowingCreate(BaseModel):
    task_id: int
    title: str
    description: str = ""
    foreshadowing_type: str = "plot"  # plot / character / world / item
    planted_chapter_id: int | None = None
    hints: list[dict] = []  # [{"chapter_id": 1, "description": "..."}]


class ForeshadowingUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    foreshadowing_type: str | None = None
    status: str | None = None
    planted_chapter_id: int | None = None
    revealed_chapter_id: int | None = None
    hints: list[dict] | None = None


# 冲突相关接口
@router.get("/by-task/{task_id}")
async def get_conflicts(
    task_id: int,
    status: str | None = Query(None, description="按状态筛选"),
    conflict_type: str | None = Query(None, description="按类型筛选"),
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取所有冲突"""
    query = select(Conflict).where(Conflict.task_id == task_id)
    if status:
        query = query.where(Conflict.status == status)
    if conflict_type:
        query = query.where(Conflict.conflict_type == conflict_type)

    result = await db.execute(query.order_by(Conflict.created_at))
    conflicts = result.scalars().all()

    conflicts_data = []
    for conflict in conflicts:
        # 获取相关角色信息
        character_ids = json.loads(conflict.related_characters) if conflict.related_characters else []
        characters_info = []
        if character_ids:
            chars_result = await db.execute(
                select(Character).where(Character.id.in_(character_ids))
            )
            characters_info = [{"id": c.id, "name": c.name} for c in chars_result.scalars().all()]

        # 获取章节信息
        introduced_chapter = None
        if conflict.introduced_chapter_id:
            chapter_result = await db.execute(
                select(Chapter).where(Chapter.id == conflict.introduced_chapter_id)
            )
            chapter = chapter_result.scalar_one_or_none()
            if chapter:
                introduced_chapter = {"id": chapter.id, "title": chapter.title}

        resolved_chapter = None
        if conflict.resolved_chapter_id:
            chapter_result = await db.execute(
                select(Chapter).where(Chapter.id == conflict.resolved_chapter_id)
            )
            chapter = chapter_result.scalar_one_or_none()
            if chapter:
                resolved_chapter = {"id": chapter.id, "title": chapter.title}

        conflicts_data.append({
            "id": conflict.id,
            "task_id": conflict.task_id,
            "title": conflict.title,
            "description": conflict.description,
            "conflict_type": conflict.conflict_type,
            "status": conflict.status,
            "priority": conflict.priority,
            "introduced_chapter": introduced_chapter,
            "resolved_chapter": resolved_chapter,
            "characters": characters_info,
            "created_at": conflict.created_at.isoformat(),
            "updated_at": conflict.updated_at.isoformat(),
        })

    return conflicts_data


@router.post("/")
async def create_conflict(req: ConflictCreate, user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """创建冲突"""
    conflict = Conflict(
        task_id=req.task_id,
        title=req.title,
        description=req.description,
        conflict_type=req.conflict_type,
        priority=req.priority,
        introduced_chapter_id=req.introduced_chapter_id,
        related_characters=json.dumps(req.related_characters),
    )
    db.add(conflict)
    await db.commit()
    await db.refresh(conflict)

    return {
        "id": conflict.id,
        "title": conflict.title,
        "status": conflict.status,
    }


@router.patch("/{conflict_id}")
async def update_conflict(conflict_id: int, req: ConflictUpdate, user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """更新冲突"""
    result = await db.execute(select(Conflict).where(Conflict.id == conflict_id))
    conflict = result.scalar_one_or_none()
    if not conflict:
        raise HTTPException(status_code=404, detail="Conflict not found")

    if req.title is not None:
        conflict.title = req.title
    if req.description is not None:
        conflict.description = req.description
    if req.conflict_type is not None:
        conflict.conflict_type = req.conflict_type
    if req.status is not None:
        conflict.status = req.status
    if req.priority is not None:
        conflict.priority = req.priority
    if req.introduced_chapter_id is not None:
        conflict.introduced_chapter_id = req.introduced_chapter_id
    if req.resolved_chapter_id is not None:
        conflict.resolved_chapter_id = req.resolved_chapter_id
    if req.related_characters is not None:
        conflict.related_characters = json.dumps(req.related_characters)

    await db.commit()

    return {"ok": True}


@router.delete("/{conflict_id}")
async def delete_conflict(conflict_id: int, user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """删除冲突"""
    result = await db.execute(select(Conflict).where(Conflict.id == conflict_id))
    conflict = result.scalar_one_or_none()
    if not conflict:
        raise HTTPException(status_code=404, detail="Conflict not found")

    await db.delete(conflict)
    await db.commit()

    return {"ok": True}


@router.get("/unresolved")
async def get_unresolved_conflicts(task_id: int, user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """获取未解决的冲突"""
    result = await db.execute(
        select(Conflict).where(
            and_(
                Conflict.task_id == task_id,
                Conflict.status != "resolved"
            )
        ).order_by(Conflict.priority.desc(), Conflict.created_at)
    )
    conflicts = result.scalars().all()

    return [
        {
            "id": c.id,
            "title": c.title,
            "status": c.status,
            "priority": c.priority,
            "conflict_type": c.conflict_type,
        }
        for c in conflicts
    ]


# 伏笔相关接口
@router.get("/foreshadowing/by-task/{task_id}")
async def get_foreshadowing(
    task_id: int,
    status: str | None = Query(None, description="按状态筛选"),
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取所有伏笔"""
    query = select(Foreshadowing).where(Foreshadowing.task_id == task_id)
    if status:
        query = query.where(Foreshadowing.status == status)

    result = await db.execute(query.order_by(Foreshadowing.created_at))
    foreshadowing_list = result.scalars().all()

    foreshadowing_data = []
    for fs in foreshadowing_list:
        # 获取章节信息
        planted_chapter = None
        if fs.planted_chapter_id:
            chapter_result = await db.execute(
                select(Chapter).where(Chapter.id == fs.planted_chapter_id)
            )
            chapter = chapter_result.scalar_one_or_none()
            if chapter:
                planted_chapter = {"id": chapter.id, "title": chapter.title}

        revealed_chapter = None
        if fs.revealed_chapter_id:
            chapter_result = await db.execute(
                select(Chapter).where(Chapter.id == fs.revealed_chapter_id)
            )
            chapter = chapter_result.scalar_one_or_none()
            if chapter:
                revealed_chapter = {"id": chapter.id, "title": chapter.title}

        hints = json.loads(fs.hints) if fs.hints else []

        foreshadowing_data.append({
            "id": fs.id,
            "task_id": fs.task_id,
            "title": fs.title,
            "description": fs.description,
            "foreshadowing_type": fs.foreshadowing_type,
            "status": fs.status,
            "planted_chapter": planted_chapter,
            "revealed_chapter": revealed_chapter,
            "hints": hints,
            "created_at": fs.created_at.isoformat(),
            "updated_at": fs.updated_at.isoformat(),
        })

    return foreshadowing_data


@router.post("/foreshadowing")
async def create_foreshadowing(req: ForeshadowingCreate, user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """创建伏笔"""
    fs = Foreshadowing(
        task_id=req.task_id,
        title=req.title,
        description=req.description,
        foreshadowing_type=req.foreshadowing_type,
        planted_chapter_id=req.planted_chapter_id,
        hints=json.dumps(req.hints),
    )
    db.add(fs)
    await db.commit()
    await db.refresh(fs)

    return {
        "id": fs.id,
        "title": fs.title,
        "status": fs.status,
    }


@router.patch("/foreshadowing/{fs_id}")
async def update_foreshadowing(fs_id: int, req: ForeshadowingUpdate, user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """更新伏笔"""
    result = await db.execute(select(Foreshadowing).where(Foreshadowing.id == fs_id))
    fs = result.scalar_one_or_none()
    if not fs:
        raise HTTPException(status_code=404, detail="Foreshadowing not found")

    if req.title is not None:
        fs.title = req.title
    if req.description is not None:
        fs.description = req.description
    if req.foreshadowing_type is not None:
        fs.foreshadowing_type = req.foreshadowing_type
    if req.status is not None:
        fs.status = req.status
    if req.planted_chapter_id is not None:
        fs.planted_chapter_id = req.planted_chapter_id
    if req.revealed_chapter_id is not None:
        fs.revealed_chapter_id = req.revealed_chapter_id
    if req.hints is not None:
        fs.hints = json.dumps(req.hints)

    await db.commit()

    return {"ok": True}


@router.delete("/foreshadowing/{fs_id}")
async def delete_foreshadowing(fs_id: int, user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """删除伏笔"""
    result = await db.execute(select(Foreshadowing).where(Foreshadowing.id == fs_id))
    fs = result.scalar_one_or_none()
    if not fs:
        raise HTTPException(status_code=404, detail="Foreshadowing not found")

    await db.delete(fs)
    await db.commit()

    return {"ok": True}


@router.get("/foreshadowing/unresolved")
async def get_unresolved_foreshadowing(task_id: int, user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """获取未回收的伏笔"""
    result = await db.execute(
        select(Foreshadowing).where(
            and_(
                Foreshadowing.task_id == task_id,
                Foreshadowing.status != "resolved"
            )
        ).order_by(Foreshadowing.created_at)
    )
    foreshadowing_list = result.scalars().all()

    return [
        {
            "id": fs.id,
            "title": fs.title,
            "status": fs.status,
            "foreshadowing_type": fs.foreshadowing_type,
        }
        for fs in foreshadowing_list
    ]


# 审阅标注相关接口
@router.get("/annotations/by-chapter/{chapter_id}")
async def get_annotations(chapter_id: int, user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """获取章节的审阅标注"""
    from ..models.models import Annotation

    result = await db.execute(
        select(Annotation).where(Annotation.chapter_id == chapter_id)
        .order_by(Annotation.selection_start)
    )
    annotations = result.scalars().all()

    annotations_data = []
    for ann in annotations:
        # 获取用户信息
        user_result = await db.execute(select(User).where(User.id == ann.user_id))
        ann_user = user_result.scalar_one_or_none()

        annotations_data.append({
            "id": ann.id,
            "chapter_id": ann.chapter_id,
            "annotation_type": ann.annotation_type,
            "color": ann.color,
            "selection_start": ann.selection_start,
            "selection_end": ann.selection_end,
            "selected_text": ann.selected_text,
            "note": ann.note,
            "suggestion": ann.suggestion,
            "user": {
                "id": ann_user.id,
                "name": ann_user.name,
            } if ann_user else None,
            "created_at": ann.created_at.isoformat(),
        })

    return annotations_data


class AnnotationCreate(BaseModel):
    task_id: int
    chapter_id: int
    annotation_type: str  # highlight / underline / strikethrough / wavy / margin_note
    color: str | None = None
    selection_start: int
    selection_end: int
    selected_text: str | None = None
    note: str | None = None
    suggestion: str | None = None


@router.post("/annotations")
async def create_annotation(req: AnnotationCreate, user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """创建审阅标注"""
    from ..models.models import Annotation

    annotation = Annotation(
        task_id=req.task_id,
        chapter_id=req.chapter_id,
        user_id=user.id,
        annotation_type=req.annotation_type,
        color=req.color,
        selection_start=req.selection_start,
        selection_end=req.selection_end,
        selected_text=req.selected_text,
        note=req.note,
        suggestion=req.suggestion,
    )
    db.add(annotation)
    await db.commit()
    await db.refresh(annotation)

    return {
        "id": annotation.id,
        "annotation_type": annotation.annotation_type,
    }


@router.delete("/annotations/{annotation_id}")
async def delete_annotation(annotation_id: int, user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """删除审阅标注"""
    from ..models.models import Annotation

    result = await db.execute(select(Annotation).where(Annotation.id == annotation_id))
    annotation = result.scalar_one_or_none()
    if not annotation:
        raise HTTPException(status_code=404, detail="Annotation not found")

    await db.delete(annotation)
    await db.commit()

    return {"ok": True}
