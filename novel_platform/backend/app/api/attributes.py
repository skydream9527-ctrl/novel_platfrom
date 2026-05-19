import json
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select, and_, delete
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.database import get_db
from ..core.deps import get_current_user
from ..models.models import AttributeDefinition, AttributeValue, Chapter, Task

router = APIRouter(prefix="/attributes", tags=["attributes"])


class AttributeDefinitionCreate(BaseModel):
    task_id: int
    name: str
    field_type: str  # text / number / select / multi_select / date / checkbox / url
    options: list[str] | None = None
    default_value: str | None = None
    sort_order: int = 0


class AttributeDefinitionUpdate(BaseModel):
    name: str | None = None
    field_type: str | None = None
    options: list[str] | None = None
    default_value: str | None = None
    sort_order: int | None = None


class AttributeValueUpdate(BaseModel):
    definition_id: int
    chapter_id: int
    value: str | None = None


class BatchAttributeValueUpdate(BaseModel):
    values: list[AttributeValueUpdate]


@router.get("/definitions/by-task/{task_id}")
async def get_attribute_definitions(task_id: int, user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """获取任务的所有属性定义"""
    result = await db.execute(
        select(AttributeDefinition)
        .where(AttributeDefinition.task_id == task_id)
        .order_by(AttributeDefinition.sort_order)
    )
    definitions = result.scalars().all()

    return [
        {
            "id": d.id,
            "task_id": d.task_id,
            "name": d.name,
            "field_type": d.field_type,
            "options": json.loads(d.options) if d.options else None,
            "default_value": d.default_value,
            "sort_order": d.sort_order,
            "created_at": d.created_at.isoformat(),
        }
        for d in definitions
    ]


@router.post("/definitions")
async def create_attribute_definition(
    req: AttributeDefinitionCreate,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """创建属性定义"""
    # 检查名称是否已存在
    existing = await db.execute(
        select(AttributeDefinition).where(
            and_(
                AttributeDefinition.task_id == req.task_id,
                AttributeDefinition.name == req.name
            )
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Attribute name already exists")

    definition = AttributeDefinition(
        task_id=req.task_id,
        name=req.name,
        field_type=req.field_type,
        options=json.dumps(req.options) if req.options else None,
        default_value=req.default_value,
        sort_order=req.sort_order,
    )
    db.add(definition)
    await db.commit()
    await db.refresh(definition)

    return {
        "id": definition.id,
        "name": definition.name,
        "field_type": definition.field_type,
    }


@router.patch("/definitions/{def_id}")
async def update_attribute_definition(
    def_id: int,
    req: AttributeDefinitionUpdate,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """更新属性定义"""
    result = await db.execute(select(AttributeDefinition).where(AttributeDefinition.id == def_id))
    definition = result.scalar_one_or_none()
    if not definition:
        raise HTTPException(status_code=404, detail="Attribute definition not found")

    if req.name is not None:
        # 检查新名称是否冲突
        existing = await db.execute(
            select(AttributeDefinition).where(
                and_(
                    AttributeDefinition.task_id == definition.task_id,
                    AttributeDefinition.name == req.name,
                    AttributeDefinition.id != def_id
                )
            )
        )
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=409, detail="Attribute name already exists")
        definition.name = req.name

    if req.field_type is not None:
        definition.field_type = req.field_type
    if req.options is not None:
        definition.options = json.dumps(req.options)
    if req.default_value is not None:
        definition.default_value = req.default_value
    if req.sort_order is not None:
        definition.sort_order = req.sort_order

    await db.commit()

    return {"ok": True}


@router.delete("/definitions/{def_id}")
async def delete_attribute_definition(def_id: int, user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """删除属性定义"""
    result = await db.execute(select(AttributeDefinition).where(AttributeDefinition.id == def_id))
    definition = result.scalar_one_or_none()
    if not definition:
        raise HTTPException(status_code=404, detail="Attribute definition not found")

    # 删除相关的属性值
    await db.execute(
        delete(AttributeValue).where(AttributeValue.definition_id == def_id)
    )

    await db.delete(definition)
    await db.commit()

    return {"ok": True}


@router.get("/values/by-chapter/{chapter_id}")
async def get_chapter_attribute_values(chapter_id: int, user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """获取章节的所有属性值"""
    result = await db.execute(
        select(AttributeValue).where(AttributeValue.chapter_id == chapter_id)
    )
    values = result.scalars().all()

    # 获取属性定义
    value_list = []
    for v in values:
        def_result = await db.execute(
            select(AttributeDefinition).where(AttributeDefinition.id == v.definition_id)
        )
        definition = def_result.scalar_one_or_none()
        if definition:
            value_list.append({
                "id": v.id,
                "definition_id": v.definition_id,
                "chapter_id": v.chapter_id,
                "value": v.value,
                "definition": {
                    "name": definition.name,
                    "field_type": definition.field_type,
                    "options": json.loads(definition.options) if definition.options else None,
                }
            })

    return value_list


@router.put("/values/batch")
async def batch_update_attribute_values(
    req: BatchAttributeValueUpdate,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """批量更新属性值"""
    for item in req.values:
        # 检查是否已存在
        result = await db.execute(
            select(AttributeValue).where(
                and_(
                    AttributeValue.definition_id == item.definition_id,
                    AttributeValue.chapter_id == item.chapter_id
                )
            )
        )
        existing = result.scalar_one_or_none()

        if existing:
            if item.value is None or item.value == "":
                # 删除空值
                await db.delete(existing)
            else:
                existing.value = item.value
        else:
            if item.value is not None and item.value != "":
                # 创建新值
                new_value = AttributeValue(
                    definition_id=item.definition_id,
                    chapter_id=item.chapter_id,
                    value=item.value,
                )
                db.add(new_value)

    await db.commit()

    return {"ok": True}


@router.get("/values/filter")
async def filter_chapters_by_attributes(
    task_id: int,
    attribute_name: str = Query(..., description="属性名称"),
    attribute_value: str = Query(..., description="属性值"),
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """按属性筛选章节"""
    # 获取属性定义
    def_result = await db.execute(
        select(AttributeDefinition).where(
            and_(
                AttributeDefinition.task_id == task_id,
                AttributeDefinition.name == attribute_name
            )
        )
    )
    definition = def_result.scalar_one_or_none()
    if not definition:
        raise HTTPException(status_code=404, detail="Attribute definition not found")

    # 查找匹配的章节ID
    result = await db.execute(
        select(AttributeValue.chapter_id).where(
            and_(
                AttributeValue.definition_id == definition.id,
                AttributeValue.value == attribute_value
            )
        )
    )
    chapter_ids = [row[0] for row in result.all()]

    # 获取章节详情
    if not chapter_ids:
        return []

    result = await db.execute(
        select(Chapter).where(Chapter.id.in_(chapter_ids)).order_by(Chapter.order_index)
    )
    chapters = result.scalars().all()

    return [
        {
            "id": c.id,
            "title": c.title,
            "order_index": c.order_index,
            "status": c.status,
            "word_count": len(c.content) if c.content else 0,
        }
        for c in chapters
    ]
