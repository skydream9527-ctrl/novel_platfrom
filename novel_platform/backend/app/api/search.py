from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.database import get_db
from ..core.deps import get_current_user
from ..models.models import Chapter, Character, Note, Source, Task

router = APIRouter(tags=["search"])


def _snippet(text: str, query: str, context_len: int = 80) -> str:
    """Extract a snippet around the first match."""
    if not text:
        return ""
    idx = text.lower().find(query.lower())
    if idx == -1:
        return text[:context_len * 2]
    start = max(0, idx - context_len)
    end = min(len(text), idx + len(query) + context_len)
    snippet = text[start:end]
    if start > 0:
        snippet = "..." + snippet
    if end < len(text):
        snippet = snippet + "..."
    return snippet


@router.get("/search")
async def search(
    q: str = Query(..., min_length=1),
    task_id: int = Query(...),
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Verify task ownership
    result = await db.execute(select(Task).where(Task.id == task_id, Task.owner_id == user.id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Task not found")

    pattern = f"%{q}%"
    results = []

    # Search chapters
    result = await db.execute(
        select(Chapter).where(
            Chapter.task_id == task_id,
            or_(Chapter.title.like(pattern), Chapter.content.like(pattern))
        ).limit(20)
    )
    for ch in result.scalars().all():
        match_field = "title" if q.lower() in ch.title.lower() else "content"
        results.append({
            "type": "chapter",
            "id": ch.id,
            "title": ch.title,
            "snippet": _snippet(ch.title if match_field == "title" else ch.content, q),
            "field": match_field,
        })

    # Search sources
    result = await db.execute(
        select(Source).where(
            Source.task_id == task_id,
            or_(Source.name.like(pattern), Source.content.like(pattern))
        ).limit(20)
    )
    for s in result.scalars().all():
        match_field = "name" if q.lower() in s.name.lower() else "content"
        results.append({
            "type": "source",
            "id": s.id,
            "title": s.name,
            "snippet": _snippet(s.name if match_field == "name" else s.content, q),
            "field": match_field,
        })

    # Search notes
    result = await db.execute(
        select(Note).where(
            Note.task_id == task_id,
            or_(Note.title.like(pattern), Note.content.like(pattern))
        ).limit(20)
    )
    for n in result.scalars().all():
        match_field = "title" if q.lower() in n.title.lower() else "content"
        results.append({
            "type": "note",
            "id": n.id,
            "title": n.title,
            "snippet": _snippet(n.title if match_field == "title" else n.content, q),
            "field": match_field,
        })

    # Search characters
    result = await db.execute(
        select(Character).where(
            Character.task_id == task_id,
            or_(
                Character.name.like(pattern),
                Character.personality.like(pattern),
                Character.backstory.like(pattern),
                Character.relationships.like(pattern),
            )
        ).limit(20)
    )
    for c in result.scalars().all():
        match_field = "name" if q.lower() in c.name.lower() else "details"
        results.append({
            "type": "character",
            "id": c.id,
            "title": c.name,
            "snippet": _snippet(c.name if match_field == "name" else (c.personality or c.backstory or ""), q),
            "field": match_field,
        })

    return results
