import re
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.database import get_db
from ..core.deps import get_current_user
from ..models.models import Link, Task, Chapter, Note, Character, Source

router = APIRouter(prefix="/links", tags=["links"])


class LinkCreate(BaseModel):
    task_id: int
    source_type: str  # chapter / note / character / source
    source_id: int
    target_type: str  # chapter / note / character / source
    target_id: int
    anchor_text: str | None = None


class LinkParseRequest(BaseModel):
    content: str
    task_id: int


# 正则表达式匹配 [[wiki link]] 语法
WIKI_LINK_PATTERN = re.compile(r'\[\[([^\]]+)\]\]')


def parse_wiki_links(content: str) -> list[dict]:
    """解析内容中的 wiki link 语法"""
    links = []
    for match in WIKI_LINK_PATTERN.finditer(content):
        link_text = match.group(1)
        # 解析链接类型和名称
        if ':' in link_text:
            # 格式：[[类型:名称]] 如 [[角色:张三]]
            parts = link_text.split(':', 1)
            link_type = parts[0].strip()
            link_name = parts[1].strip()
        else:
            # 格式：[[名称]] 默认为章节
            link_type = 'chapter'
            link_name = link_text.strip()

        links.append({
            'type': link_type,
            'name': link_name,
            'full_match': match.group(0),
            'start': match.start(),
            'end': match.end()
        })
    return links


async def resolve_link_target(db: AsyncSession, task_id: int, link_type: str, link_name: str) -> dict | None:
    """解析链接目标，返回目标类型和ID"""
    type_mapping = {
        'chapter': (Chapter, 'chapter'),
        '角色': (Character, 'character'),
        'character': (Character, 'character'),
        '笔记': (Note, 'note'),
        'note': (Note, 'note'),
        '素材': (Source, 'source'),
        'source': (Source, 'source'),
    }

    if link_type not in type_mapping:
        return None

    model_class, target_type = type_mapping[link_type]

    # 根据名称查找目标
    if target_type == 'chapter':
        result = await db.execute(
            select(model_class).where(
                and_(
                    model_class.task_id == task_id,
                    model_class.title == link_name
                )
            )
        )
    elif target_type == 'character':
        result = await db.execute(
            select(model_class).where(
                and_(
                    model_class.task_id == task_id,
                    model_class.name == link_name
                )
            )
        )
    elif target_type == 'note':
        result = await db.execute(
            select(model_class).where(
                and_(
                    model_class.task_id == task_id,
                    model_class.title == link_name
                )
            )
        )
    elif target_type == 'source':
        result = await db.execute(
            select(model_class).where(
                and_(
                    model_class.task_id == task_id,
                    model_class.name == link_name
                )
            )
        )
    else:
        return None

    target = result.scalar_one_or_none()
    if target:
        return {
            'type': target_type,
            'id': target.id
        }
    return None


@router.get("/by-task/{task_id}")
async def list_links(task_id: int, user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """获取任务下的所有链接"""
    result = await db.execute(
        select(Link).where(Link.task_id == task_id).order_by(Link.created_at)
    )
    links = result.scalars().all()
    return [
        {
            "id": link.id,
            "task_id": link.task_id,
            "source_type": link.source_type,
            "source_id": link.source_id,
            "target_type": link.target_type,
            "target_id": link.target_id,
            "anchor_text": link.anchor_text,
            "created_at": link.created_at.isoformat(),
        }
        for link in links
    ]


@router.get("/backlinks/{target_type}/{target_id}")
async def get_backlinks(
    target_type: str,
    target_id: int,
    task_id: int,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取反向链接（谁引用了指定目标）"""
    result = await db.execute(
        select(Link).where(
            and_(
                Link.task_id == task_id,
                Link.target_type == target_type,
                Link.target_id == target_id
            )
        )
    )
    links = result.scalars().all()

    # 获取源内容的详细信息
    backlinks = []
    for link in links:
        source_info = await get_content_info(db, link.source_type, link.source_id)
        if source_info:
            backlinks.append({
                "link_id": link.id,
                "source_type": link.source_type,
                "source_id": link.source_id,
                "source_title": source_info.get('title', ''),
                "anchor_text": link.anchor_text,
                "created_at": link.created_at.isoformat(),
            })

    return backlinks


async def get_content_info(db: AsyncSession, content_type: str, content_id: int) -> dict | None:
    """获取内容的基本信息"""
    if content_type == 'chapter':
        result = await db.execute(select(Chapter).where(Chapter.id == content_id))
        chapter = result.scalar_one_or_none()
        if chapter:
            return {'title': chapter.title, 'type': 'chapter'}
    elif content_type == 'note':
        result = await db.execute(select(Note).where(Note.id == content_id))
        note = result.scalar_one_or_none()
        if note:
            return {'title': note.title, 'type': 'note'}
    elif content_type == 'character':
        result = await db.execute(select(Character).where(Character.id == content_id))
        character = result.scalar_one_or_none()
        if character:
            return {'title': character.name, 'type': 'character'}
    elif content_type == 'source':
        result = await db.execute(select(Source).where(Source.id == content_id))
        source = result.scalar_one_or_none()
        if source:
            return {'title': source.name, 'type': 'source'}
    return None


@router.post("/parse")
async def parse_links(req: LinkParseRequest, user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """解析内容中的链接语法"""
    parsed_links = parse_wiki_links(req.content)

    # 尝试解析每个链接的目标
    resolved_links = []
    for link_info in parsed_links:
        target = await resolve_link_target(db, req.task_id, link_info['type'], link_info['name'])
        resolved_links.append({
            **link_info,
            'resolved': target is not None,
            'target': target
        })

    return {
        "links": resolved_links,
        "total": len(resolved_links),
        "resolved": sum(1 for l in resolved_links if l['resolved'])
    }


@router.post("/")
async def create_link(req: LinkCreate, user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """创建链接"""
    # 验证源和目标是否存在
    source_info = await get_content_info(db, req.source_type, req.source_id)
    if not source_info:
        raise HTTPException(status_code=404, detail=f"Source {req.source_type}:{req.source_id} not found")

    target_info = await get_content_info(db, req.target_type, req.target_id)
    if not target_info:
        raise HTTPException(status_code=404, detail=f"Target {req.target_type}:{req.target_id} not found")

    # 检查链接是否已存在
    existing = await db.execute(
        select(Link).where(
            and_(
                Link.task_id == req.task_id,
                Link.source_type == req.source_type,
                Link.source_id == req.source_id,
                Link.target_type == req.target_type,
                Link.target_id == req.target_id
            )
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Link already exists")

    link = Link(
        task_id=req.task_id,
        source_type=req.source_type,
        source_id=req.source_id,
        target_type=req.target_type,
        target_id=req.target_id,
        anchor_text=req.anchor_text
    )
    db.add(link)
    await db.commit()
    await db.refresh(link)

    return {
        "id": link.id,
        "source_type": link.source_type,
        "source_id": link.source_id,
        "target_type": link.target_type,
        "target_id": link.target_id,
    }


@router.delete("/{link_id}")
async def delete_link(link_id: int, user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """删除链接"""
    result = await db.execute(select(Link).where(Link.id == link_id))
    link = result.scalar_one_or_none()
    if not link:
        raise HTTPException(status_code=404, detail="Link not found")

    await db.delete(link)
    await db.commit()

    return {"ok": True}


@router.post("/batch")
async def batch_create_links(
    links: list[LinkCreate],
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """批量创建链接"""
    created_links = []
    for req in links:
        # 检查链接是否已存在
        existing = await db.execute(
            select(Link).where(
                and_(
                    Link.task_id == req.task_id,
                    Link.source_type == req.source_type,
                    Link.source_id == req.source_id,
                    Link.target_type == req.target_type,
                    Link.target_id == req.target_id
                )
            )
        )
        if existing.scalar_one_or_none():
            continue

        link = Link(
            task_id=req.task_id,
            source_type=req.source_type,
            source_id=req.source_id,
            target_type=req.target_type,
            target_id=req.target_id,
            anchor_text=req.anchor_text
        )
        db.add(link)
        created_links.append(link)

    await db.commit()

    return {
        "created": len(created_links),
        "links": [
            {
                "id": link.id,
                "source_type": link.source_type,
                "source_id": link.source_id,
                "target_type": link.target_type,
                "target_id": link.target_id,
            }
            for link in created_links
        ]
    }
