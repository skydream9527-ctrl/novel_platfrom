from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..core.database import get_db
from ..core.deps import get_current_user
from ..models.models import Category, Note, Task
from ..utils.file_sync import delete_doc_file, delete_note_file, get_task_dir, sync_doc_to_file, sync_note_to_file

router = APIRouter(prefix="/notes", tags=["notes"])


class NoteCreate(BaseModel):
    task_id: int
    title: str
    content: str = ""
    category_id: int | None = None


class NoteUpdate(BaseModel):
    title: str | None = None
    content: str | None = None
    category_id: int | None = None


def _note_dict(n: Note) -> dict:
    return {
        "id": n.id,
        "title": n.title,
        "content": n.content[:200] if n.content else "",
        "task_id": n.task_id,
        "category_id": n.category_id,
        "created_at": n.created_at.isoformat(),
        "updated_at": n.updated_at.isoformat() if n.updated_at else None,
    }


@router.get("/by-task/{task_id}")
async def list_notes(task_id: int, user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Note).where(Note.task_id == task_id).order_by(Note.updated_at.desc()))
    notes = result.scalars().all()
    return [_note_dict(n) for n in notes]


@router.get("/by-category/{category_id}")
async def list_notes_by_category(category_id: int, user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    # Verify category exists and user owns the task
    result = await db.execute(
        select(Category).where(Category.id == category_id).join(Task).where(Task.owner_id == user.id)
    )
    category = result.scalar_one_or_none()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")

    result = await db.execute(
        select(Note).where(Note.category_id == category_id).order_by(Note.updated_at.desc())
    )
    notes = result.scalars().all()
    return [_note_dict(n) for n in notes]


@router.get("/{note_id}")
async def get_note(note_id: int, user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Note).where(Note.id == note_id).join(Task).where(Task.owner_id == user.id)
    )
    note = result.scalar_one_or_none()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    return {
        "id": note.id,
        "title": note.title,
        "content": note.content,
        "task_id": note.task_id,
        "category_id": note.category_id,
        "created_at": note.created_at.isoformat(),
        "updated_at": note.updated_at.isoformat() if note.updated_at else None,
    }


@router.post("/")
async def create_note(req: NoteCreate, user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    note = Note(task_id=req.task_id, title=req.title, content=req.content, category_id=req.category_id)
    db.add(note)
    await db.commit()
    await db.refresh(note)

    task_dir = await get_task_dir(db, req.task_id)
    if task_dir:
        if req.category_id:
            # Get category name for folder path
            result = await db.execute(select(Category).where(Category.id == req.category_id))
            category = result.scalar_one_or_none()
            if category:
                sync_doc_to_file(task_dir, category.name, note)
        else:
            sync_note_to_file(task_dir, note)

    return {"id": note.id, "title": note.title, "category_id": note.category_id}


@router.patch("/{note_id}")
async def update_note(note_id: int, req: NoteUpdate, user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Note).where(Note.id == note_id).join(Task).where(Task.owner_id == user.id)
    )
    note = result.scalar_one_or_none()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")

    old_title = note.title
    old_category_id = note.category_id

    for field, value in req.model_dump(exclude_none=True).items():
        setattr(note, field, value)
    await db.commit()

    task_dir = await get_task_dir(db, note.task_id)
    if task_dir:
        # Determine category name for file path
        cat_name = None
        effective_cat_id = req.category_id if req.category_id is not None else old_category_id
        if effective_cat_id:
            cat_result = await db.execute(select(Category).where(Category.id == effective_cat_id))
            cat = cat_result.scalar_one_or_none()
            if cat:
                cat_name = cat.name

        # Delete old file
        if cat_name:
            delete_doc_file(task_dir, cat_name, old_title)
        elif old_category_id:
            old_cat_result = await db.execute(select(Category).where(Category.id == old_category_id))
            old_cat = old_cat_result.scalar_one_or_none()
            if old_cat:
                delete_doc_file(task_dir, old_cat.name, old_title)
        else:
            delete_note_file(task_dir, old_title)

        # Write new file
        await db.refresh(note)
        if cat_name:
            sync_doc_to_file(task_dir, cat_name, note)
        else:
            sync_note_to_file(task_dir, note)

    return {"ok": True}


@router.delete("/{note_id}")
async def delete_note(note_id: int, user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Note).where(Note.id == note_id).join(Task).where(Task.owner_id == user.id)
    )
    note = result.scalar_one_or_none()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")

    task_dir = await get_task_dir(db, note.task_id)
    title = note.title
    category_id = note.category_id

    await db.delete(note)
    await db.commit()

    if task_dir:
        if category_id:
            cat_result = await db.execute(select(Category).where(Category.id == category_id))
            cat = cat_result.scalar_one_or_none()
            if cat:
                delete_doc_file(task_dir, cat.name, title)
        else:
            delete_note_file(task_dir, title)

    return {"ok": True}
