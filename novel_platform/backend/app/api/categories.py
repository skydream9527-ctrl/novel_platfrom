from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.database import get_db
from ..core.deps import get_current_user
from ..models.models import Category, Task
from ..utils.file_sync import (
    delete_category_dir,
    ensure_category_dir,
    get_task_dir,
    rename_category_dir,
    sync_category_to_file,
)

router = APIRouter(prefix="/categories", tags=["categories"])


class CategoryCreate(BaseModel):
    task_id: int
    name: str
    icon: str = "📁"


class CategoryUpdate(BaseModel):
    name: str | None = None
    icon: str | None = None


@router.get("/by-task/{task_id}")
async def list_categories(task_id: int, user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Category)
        .where(Category.task_id == task_id)
        .order_by(Category.sort_order, Category.id)
    )
    categories = result.scalars().all()
    return [
        {
            "id": c.id,
            "name": c.name,
            "icon": c.icon,
            "sort_order": c.sort_order,
            "created_at": c.created_at.isoformat(),
        }
        for c in categories
    ]


@router.post("/")
async def create_category(req: CategoryCreate, user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    # Verify task ownership
    result = await db.execute(select(Task).where(Task.id == req.task_id, Task.owner_id == user.id))
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    # Get max sort_order
    result = await db.execute(
        select(Category.sort_order).where(Category.task_id == req.task_id).order_by(Category.sort_order.desc()).limit(1)
    )
    max_order = result.scalar_one_or_none() or 0

    category = Category(task_id=req.task_id, name=req.name, icon=req.icon, sort_order=max_order + 1)
    db.add(category)
    await db.commit()
    await db.refresh(category)

    # Sync to filesystem
    task_dir = await get_task_dir(db, req.task_id)
    if task_dir:
        ensure_category_dir(task_dir, category.name)
        sync_category_to_file(task_dir, category)

    return {"id": category.id, "name": category.name, "icon": category.icon}


@router.patch("/{category_id}")
async def update_category(
    category_id: int, req: CategoryUpdate, user=Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Category).where(Category.id == category_id))
    category = result.scalar_one_or_none()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")

    # Verify task ownership
    result = await db.execute(select(Task).where(Task.id == category.task_id, Task.owner_id == user.id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Task not found")

    old_name = category.name
    if req.name is not None:
        category.name = req.name
    if req.icon is not None:
        category.icon = req.icon
    await db.commit()

    task_dir = await get_task_dir(db, category.task_id)
    if task_dir:
        if req.name and req.name != old_name:
            rename_category_dir(task_dir, old_name, category.name)
        sync_category_to_file(task_dir, category)

    return {"ok": True}


@router.delete("/{category_id}")
async def delete_category(category_id: int, user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Category).where(Category.id == category_id))
    category = result.scalar_one_or_none()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")

    # Verify task ownership
    result = await db.execute(select(Task).where(Task.id == category.task_id, Task.owner_id == user.id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Task not found")

    task_dir = await get_task_dir(db, category.task_id)
    cat_name = category.name

    await db.delete(category)
    await db.commit()

    if task_dir:
        delete_category_dir(task_dir, cat_name)

    return {"ok": True}
