from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.database import get_db
from ..core.deps import get_current_user
from ..models.models import Tag, ContentTag, Chapter, Note, Source

router = APIRouter(prefix="/tags", tags=["tags"])


class TagCreate(BaseModel):
    task_id: int
    name: str
    color: str | None = None


class TagUpdate(BaseModel):
    name: str | None = None
    color: str | None = None


class ContentTagAssign(BaseModel):
    tag_id: int
    content_type: str  # chapter / note / source
    content_id: int


class ContentTagUnassign(BaseModel):
    tag_id: int
    content_type: str
    content_id: int


@router.get("/by-task/{task_id}")
async def list_tags(task_id: int, user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """获取任务下的所有标签"""
    result = await db.execute(
        select(Tag).where(Tag.task_id == task_id).order_by(Tag.name)
    )
    tags = result.scalars().all()

    # 获取每个标签的使用次数
    tag_list = []
    for tag in tags:
        count_result = await db.execute(
            select(func.count(ContentTag.id)).where(ContentTag.tag_id == tag.id)
        )
        usage_count = count_result.scalar() or 0

        tag_list.append({
            "id": tag.id,
            "task_id": tag.task_id,
            "name": tag.name,
            "color": tag.color,
            "usage_count": usage_count,
            "created_at": tag.created_at.isoformat(),
        })

    return tag_list


@router.post("/")
async def create_tag(req: TagCreate, user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """创建标签"""
    # 检查标签名是否已存在
    existing = await db.execute(
        select(Tag).where(
            and_(
                Tag.task_id == req.task_id,
                Tag.name == req.name
            )
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Tag name already exists")

    tag = Tag(
        task_id=req.task_id,
        name=req.name,
        color=req.color
    )
    db.add(tag)
    await db.commit()
    await db.refresh(tag)

    return {
        "id": tag.id,
        "name": tag.name,
        "color": tag.color,
    }


@router.patch("/{tag_id}")
async def update_tag(tag_id: int, req: TagUpdate, user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """更新标签"""
    result = await db.execute(select(Tag).where(Tag.id == tag_id))
    tag = result.scalar_one_or_none()
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")

    if req.name is not None:
        # 检查新名称是否与其他标签冲突
        existing = await db.execute(
            select(Tag).where(
                and_(
                    Tag.task_id == tag.task_id,
                    Tag.name == req.name,
                    Tag.id != tag_id
                )
            )
        )
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=409, detail="Tag name already exists")
        tag.name = req.name

    if req.color is not None:
        tag.color = req.color

    await db.commit()

    return {"ok": True}


@router.delete("/{tag_id}")
async def delete_tag(tag_id: int, user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """删除标签"""
    result = await db.execute(select(Tag).where(Tag.id == tag_id))
    tag = result.scalar_one_or_none()
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")

    await db.delete(tag)
    await db.commit()

    return {"ok": True}


@router.post("/assign")
async def assign_tag(req: ContentTagAssign, user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """为内容添加标签"""
    # 验证标签是否存在
    tag_result = await db.execute(select(Tag).where(Tag.id == req.tag_id))
    if not tag_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Tag not found")

    # 验证内容是否存在
    content_exists = await verify_content_exists(db, req.content_type, req.content_id)
    if not content_exists:
        raise HTTPException(status_code=404, detail=f"Content {req.content_type}:{req.content_id} not found")

    # 检查是否已关联
    existing = await db.execute(
        select(ContentTag).where(
            and_(
                ContentTag.tag_id == req.tag_id,
                ContentTag.content_type == req.content_type,
                ContentTag.content_id == req.content_id
            )
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Tag already assigned to this content")

    content_tag = ContentTag(
        tag_id=req.tag_id,
        content_type=req.content_type,
        content_id=req.content_id
    )
    db.add(content_tag)
    await db.commit()

    return {"ok": True}


@router.delete("/unassign")
async def unassign_tag(req: ContentTagUnassign, user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """移除内容标签"""
    result = await db.execute(
        select(ContentTag).where(
            and_(
                ContentTag.tag_id == req.tag_id,
                ContentTag.content_type == req.content_type,
                ContentTag.content_id == req.content_id
            )
        )
    )
    content_tag = result.scalar_one_or_none()
    if not content_tag:
        raise HTTPException(status_code=404, detail="Content tag not found")

    await db.delete(content_tag)
    await db.commit()

    return {"ok": True}


@router.get("/{tag_id}/content")
async def get_tag_content(
    tag_id: int,
    content_type: str | None = None,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取标签下的所有内容"""
    # 验证标签是否存在
    tag_result = await db.execute(select(Tag).where(Tag.id == tag_id))
    tag = tag_result.scalar_one_or_none()
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")

    # 构建查询
    query = select(ContentTag).where(ContentTag.tag_id == tag_id)
    if content_type:
        query = query.where(ContentTag.content_type == content_type)

    result = await db.execute(query)
    content_tags = result.scalars().all()

    # 获取内容详情
    content_list = []
    for ct in content_tags:
        content_info = await get_content_detail(db, ct.content_type, ct.content_id)
        if content_info:
            content_list.append({
                "content_type": ct.content_type,
                "content_id": ct.content_id,
                **content_info
            })

    return {
        "tag": {
            "id": tag.id,
            "name": tag.name,
            "color": tag.color,
        },
        "content": content_list,
        "total": len(content_list)
    }


@router.get("/by-content/{content_type}/{content_id}")
async def get_content_tags(
    content_type: str,
    content_id: int,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取内容的所有标签"""
    result = await db.execute(
        select(ContentTag).where(
            and_(
                ContentTag.content_type == content_type,
                ContentTag.content_id == content_id
            )
        )
    )
    content_tags = result.scalars().all()

    # 获取标签详情
    tags = []
    for ct in content_tags:
        tag_result = await db.execute(select(Tag).where(Tag.id == ct.tag_id))
        tag = tag_result.scalar_one_or_none()
        if tag:
            tags.append({
                "id": tag.id,
                "name": tag.name,
                "color": tag.color,
            })

    return tags


async def verify_content_exists(db: AsyncSession, content_type: str, content_id: int) -> bool:
    """验证内容是否存在"""
    if content_type == 'chapter':
        result = await db.execute(select(Chapter).where(Chapter.id == content_id))
    elif content_type == 'note':
        result = await db.execute(select(Note).where(Note.id == content_id))
    elif content_type == 'source':
        result = await db.execute(select(Source).where(Source.id == content_id))
    else:
        return False

    return result.scalar_one_or_none() is not None


async def get_content_detail(db: AsyncSession, content_type: str, content_id: int) -> dict | None:
    """获取内容的详细信息"""
    if content_type == 'chapter':
        result = await db.execute(select(Chapter).where(Chapter.id == content_id))
        chapter = result.scalar_one_or_none()
        if chapter:
            return {
                "title": chapter.title,
                "word_count": len(chapter.content) if chapter.content else 0,
                "created_at": chapter.created_at.isoformat(),
            }
    elif content_type == 'note':
        result = await db.execute(select(Note).where(Note.id == content_id))
        note = result.scalar_one_or_none()
        if note:
            return {
                "title": note.title,
                "word_count": len(note.content) if note.content else 0,
                "created_at": note.created_at.isoformat(),
            }
    elif content_type == 'source':
        result = await db.execute(select(Source).where(Source.id == content_id))
        source = result.scalar_one_or_none()
        if source:
            return {
                "title": source.name,
                "word_count": source.word_count or 0,
                "created_at": source.created_at.isoformat(),
            }
    return None


@router.post("/batch-assign")
async def batch_assign_tags(
    assignments: list[ContentTagAssign],
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """批量为内容添加标签"""
    assigned_count = 0
    for req in assignments:
        # 检查是否已关联
        existing = await db.execute(
            select(ContentTag).where(
                and_(
                    ContentTag.tag_id == req.tag_id,
                    ContentTag.content_type == req.content_type,
                    ContentTag.content_id == req.content_id
                )
            )
        )
        if existing.scalar_one_or_none():
            continue

        content_tag = ContentTag(
            tag_id=req.tag_id,
            content_type=req.content_type,
            content_id=req.content_id
        )
        db.add(content_tag)
        assigned_count += 1

    await db.commit()

    return {"assigned": assigned_count}
