from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.database import get_db
from ..core.deps import get_current_user
from ..models.models import Character, Task
from ..utils.file_sync import sync_characters_to_file

router = APIRouter(prefix="/characters", tags=["characters"])


async def _sync_chars(db: AsyncSession, task_id: int) -> None:
    """Reload all characters for a task and sync to filesystem if directory_path is set."""
    task_result = await db.execute(select(Task).where(Task.id == task_id))
    task = task_result.scalar_one_or_none()
    if not task or not task.directory_path:
        return
    chars_result = await db.execute(select(Character).where(Character.task_id == task_id))
    chars = chars_result.scalars().all()
    sync_characters_to_file(task.directory_path, chars)


class CharacterCreate(BaseModel):
    task_id: int
    name: str
    role: str = ""
    appearance: str = ""
    personality: str = ""
    backstory: str = ""
    relationships: str = ""


class CharacterUpdate(BaseModel):
    name: str | None = None
    role: str | None = None
    appearance: str | None = None
    personality: str | None = None
    backstory: str | None = None
    relationships: str | None = None


@router.get("/by-task/{task_id}")
async def list_characters(task_id: int, user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Character).where(Character.task_id == task_id).order_by(Character.created_at))
    chars = result.scalars().all()
    return [
        {
            "id": c.id, "name": c.name, "role": c.role,
            "appearance": c.appearance, "personality": c.personality,
            "backstory": c.backstory, "relationships": c.relationships,
            "created_at": c.created_at.isoformat(),
        }
        for c in chars
    ]


@router.post("/")
async def create_character(req: CharacterCreate, user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    char = Character(
        task_id=req.task_id, name=req.name, role=req.role,
        appearance=req.appearance, personality=req.personality,
        backstory=req.backstory, relationships=req.relationships,
    )
    db.add(char)
    await db.commit()
    await db.refresh(char)

    await _sync_chars(db, req.task_id)

    return {"id": char.id, "name": char.name}


@router.patch("/{char_id}")
async def update_character(char_id: int, req: CharacterUpdate, user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Character).where(Character.id == char_id))
    char = result.scalar_one_or_none()
    if not char:
        raise HTTPException(status_code=404, detail="Character not found")
    task_id = char.task_id
    for field, value in req.model_dump(exclude_none=True).items():
        setattr(char, field, value)
    await db.commit()

    await _sync_chars(db, task_id)

    return {"ok": True}


@router.delete("/{char_id}")
async def delete_character(char_id: int, user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Character).where(Character.id == char_id))
    char = result.scalar_one_or_none()
    if not char:
        raise HTTPException(status_code=404, detail="Character not found")
    task_id = char.task_id
    await db.delete(char)
    await db.commit()

    await _sync_chars(db, task_id)

    return {"ok": True}
