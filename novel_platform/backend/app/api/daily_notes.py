from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.database import get_db
from ..core.deps import get_current_user
from ..models.models import DailyNote

router = APIRouter(prefix="/daily-notes", tags=["daily-notes"])


class DailyNoteCreate(BaseModel):
    content: str = ""
    mood: str = ""
    date: str = ""  # YYYY-MM-DD, defaults to today


class DailyNoteUpdate(BaseModel):
    content: str | None = None
    mood: str | None = None


@router.get("/")
async def list_notes(user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """获取用户的所有每日笔记"""
    result = await db.execute(
        select(DailyNote)
        .where(DailyNote.user_id == user.id)
        .order_by(DailyNote.date.desc())
    )
    notes = result.scalars().all()
    return [
        {
            "id": n.id,
            "date": n.date,
            "content": n.content,
            "mood": n.mood,
            "word_count": n.word_count,
            "created_at": n.created_at.isoformat() if n.created_at else None,
        }
        for n in notes
    ]


@router.get("/{date}")
async def get_note_by_date(date: str, user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """获取指定日期的笔记"""
    result = await db.execute(
        select(DailyNote).where(DailyNote.user_id == user.id, DailyNote.date == date)
    )
    note = result.scalar_one_or_none()
    if not note:
        return None
    return {
        "id": note.id,
        "date": note.date,
        "content": note.content,
        "mood": note.mood,
        "word_count": note.word_count,
    }


@router.post("/")
async def create_note(req: DailyNoteCreate, user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """创建每日笔记"""
    from datetime import date as date_type
    today = req.date or date_type.today().isoformat()

    # Check if note already exists for this date
    existing = await db.execute(
        select(DailyNote).where(DailyNote.user_id == user.id, DailyNote.date == today)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Note already exists for this date")

    note = DailyNote(
        user_id=user.id,
        date=today,
        content=req.content,
        mood=req.mood,
        word_count=len(req.content),
    )
    db.add(note)
    await db.commit()
    await db.refresh(note)

    return {
        "id": note.id,
        "date": note.date,
        "content": note.content,
        "mood": note.mood,
        "word_count": note.word_count,
    }


@router.patch("/{note_id}")
async def update_note(note_id: int, req: DailyNoteUpdate, user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """更新每日笔记"""
    result = await db.execute(
        select(DailyNote).where(DailyNote.id == note_id, DailyNote.user_id == user.id)
    )
    note = result.scalar_one_or_none()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")

    if req.content is not None:
        note.content = req.content
        note.word_count = len(req.content)
    if req.mood is not None:
        note.mood = req.mood

    await db.commit()
    return {"ok": True}
