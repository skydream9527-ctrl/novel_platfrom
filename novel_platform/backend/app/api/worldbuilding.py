import json
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.database import get_db
from ..core.deps import get_current_user
from ..models.models import WorldbuildingCategory, WorldbuildingEntry, Task, Character

router = APIRouter(prefix="/worldbuilding", tags=["worldbuilding"])


class CategoryCreate(BaseModel):
    task_id: int
    name: str
    icon: str = "📁"
    description: str = ""
    sort_order: int = 0


class CategoryUpdate(BaseModel):
    name: str | None = None
    icon: str | None = None
    description: str | None = None
    sort_order: int | None = None


class EntryCreate(BaseModel):
    task_id: int
    category_id: int
    title: str
    content: str = ""
    attributes: dict = {}
    related_entries: list[int] = []
    related_characters: list[int] = []


class EntryUpdate(BaseModel):
    title: str | None = None
    content: str | None = None
    attributes: dict | None = None
    related_entries: list[int] | None = None
    related_characters: list[int] | None = None


# 预设分类模板
PRESET_CATEGORIES = [
    {"name": "地理", "icon": "🌍", "description": "大陆、城市、山脉、河流"},
    {"name": "势力", "icon": "🏛️", "description": "国家、组织、家族"},
    {"name": "魔法体系", "icon": "✨", "description": "法术分类、魔法规则、魔法物品"},
    {"name": "科技设定", "icon": "🔬", "description": "科技水平、发明创造、交通工具"},
    {"name": "历史", "icon": "📜", "description": "历史事件、朝代更替、重要战争"},
    {"name": "种族", "icon": "👥", "description": "种族特征、文化习俗、语言"},
    {"name": "物品", "icon": "⚔️", "description": "重要道具、神器、武器"},
    {"name": "规则", "icon": "📏", "description": "世界运行规则、限制条件"},
]


@router.get("/categories/by-task/{task_id}")
async def get_categories(task_id: int, user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """获取世界观分类"""
    result = await db.execute(
        select(WorldbuildingCategory)
        .where(WorldbuildingCategory.task_id == task_id)
        .order_by(WorldbuildingCategory.sort_order)
    )
    categories = result.scalars().all()

    categories_data = []
    for cat in categories:
        # 获取条目数量
        entries_count_result = await db.execute(
            select(WorldbuildingEntry).where(WorldbuildingEntry.category_id == cat.id)
        )
        entries_count = len(entries_count_result.scalars().all())

        categories_data.append({
            "id": cat.id,
            "task_id": cat.task_id,
            "name": cat.name,
            "icon": cat.icon,
            "description": cat.description,
            "sort_order": cat.sort_order,
            "entries_count": entries_count,
            "created_at": cat.created_at.isoformat(),
        })

    return categories_data


@router.post("/categories")
async def create_category(req: CategoryCreate, user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """创建世界观分类"""
    category = WorldbuildingCategory(
        task_id=req.task_id,
        name=req.name,
        icon=req.icon,
        description=req.description,
        sort_order=req.sort_order,
    )
    db.add(category)
    await db.commit()
    await db.refresh(category)

    return {
        "id": category.id,
        "name": category.name,
        "icon": category.icon,
    }


@router.patch("/categories/{cat_id}")
async def update_category(cat_id: int, req: CategoryUpdate, user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """更新世界观分类"""
    result = await db.execute(select(WorldbuildingCategory).where(WorldbuildingCategory.id == cat_id))
    category = result.scalar_one_or_none()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")

    if req.name is not None:
        category.name = req.name
    if req.icon is not None:
        category.icon = req.icon
    if req.description is not None:
        category.description = req.description
    if req.sort_order is not None:
        category.sort_order = req.sort_order

    await db.commit()

    return {"ok": True}


@router.delete("/categories/{cat_id}")
async def delete_category(cat_id: int, user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """删除世界观分类"""
    result = await db.execute(select(WorldbuildingCategory).where(WorldbuildingCategory.id == cat_id))
    category = result.scalar_one_or_none()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")

    await db.delete(category)
    await db.commit()

    return {"ok": True}


@router.post("/categories/presets")
async def create_preset_categories(task_id: int, user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """创建预设分类"""
    # 验证任务所有权
    task_result = await db.execute(
        select(Task).where(Task.id == task_id, Task.owner_id == user.id)
    )
    if not task_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Task not found")

    created_count = 0
    for i, preset in enumerate(PRESET_CATEGORIES):
        # 检查是否已存在
        existing = await db.execute(
            select(WorldbuildingCategory).where(
                and_(
                    WorldbuildingCategory.task_id == task_id,
                    WorldbuildingCategory.name == preset["name"]
                )
            )
        )
        if existing.scalar_one_or_none():
            continue

        category = WorldbuildingCategory(
            task_id=task_id,
            name=preset["name"],
            icon=preset["icon"],
            description=preset["description"],
            sort_order=i,
        )
        db.add(category)
        created_count += 1

    await db.commit()

    return {"created": created_count}


@router.get("/entries/by-task/{task_id}")
async def get_entries(
    task_id: int,
    category_id: int | None = Query(None, description="按分类筛选"),
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取世界观条目"""
    query = select(WorldbuildingEntry).where(WorldbuildingEntry.task_id == task_id)
    if category_id:
        query = query.where(WorldbuildingEntry.category_id == category_id)

    result = await db.execute(query.order_by(WorldbuildingEntry.created_at))
    entries = result.scalars().all()

    entries_data = []
    for entry in entries:
        # 获取分类信息
        cat_result = await db.execute(
            select(WorldbuildingCategory).where(WorldbuildingCategory.id == entry.category_id)
        )
        category = cat_result.scalar_one_or_none()

        entries_data.append({
            "id": entry.id,
            "task_id": entry.task_id,
            "category_id": entry.category_id,
            "title": entry.title,
            "content": entry.content,
            "attributes": json.loads(entry.attributes) if entry.attributes else {},
            "related_entries": json.loads(entry.related_entries) if entry.related_entries else [],
            "related_characters": json.loads(entry.related_characters) if entry.related_characters else [],
            "category": {
                "id": category.id,
                "name": category.name,
                "icon": category.icon,
            } if category else None,
            "created_at": entry.created_at.isoformat(),
            "updated_at": entry.updated_at.isoformat(),
        })

    return entries_data


@router.post("/entries")
async def create_entry(req: EntryCreate, user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """创建世界观条目"""
    entry = WorldbuildingEntry(
        task_id=req.task_id,
        category_id=req.category_id,
        title=req.title,
        content=req.content,
        attributes=json.dumps(req.attributes),
        related_entries=json.dumps(req.related_entries),
        related_characters=json.dumps(req.related_characters),
    )
    db.add(entry)
    await db.commit()
    await db.refresh(entry)

    return {
        "id": entry.id,
        "title": entry.title,
    }


@router.patch("/entries/{entry_id}")
async def update_entry(entry_id: int, req: EntryUpdate, user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """更新世界观条目"""
    result = await db.execute(select(WorldbuildingEntry).where(WorldbuildingEntry.id == entry_id))
    entry = result.scalar_one_or_none()
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")

    if req.title is not None:
        entry.title = req.title
    if req.content is not None:
        entry.content = req.content
    if req.attributes is not None:
        entry.attributes = json.dumps(req.attributes)
    if req.related_entries is not None:
        entry.related_entries = json.dumps(req.related_entries)
    if req.related_characters is not None:
        entry.related_characters = json.dumps(req.related_characters)

    await db.commit()

    return {"ok": True}


@router.delete("/entries/{entry_id}")
async def delete_entry(entry_id: int, user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """删除世界观条目"""
    result = await db.execute(select(WorldbuildingEntry).where(WorldbuildingEntry.id == entry_id))
    entry = result.scalar_one_or_none()
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")

    await db.delete(entry)
    await db.commit()

    return {"ok": True}


@router.get("/search")
async def search_entries(
    task_id: int,
    q: str = Query(..., description="搜索关键词"),
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """搜索世界观条目"""
    result = await db.execute(
        select(WorldbuildingEntry).where(
            and_(
                WorldbuildingEntry.task_id == task_id,
                WorldbuildingEntry.title.contains(q) | WorldbuildingEntry.content.contains(q)
            )
        )
    )
    entries = result.scalars().all()

    return [
        {
            "id": entry.id,
            "title": entry.title,
            "content": entry.content[:200] if entry.content else "",
            "category_id": entry.category_id,
        }
        for entry in entries
    ]
