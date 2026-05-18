from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.database import get_db
from ..core.deps import get_current_user
from ..models.models import Conversation, Message, Task

router = APIRouter(prefix="/conversations", tags=["conversations"])


@router.get("/{conversation_id}/messages")
async def get_messages(
    conversation_id: int,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Conversation)
        .where(Conversation.id == conversation_id)
    )
    conv = result.scalar_one_or_none()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")

    # Verify ownership
    task_result = await db.execute(select(Task).where(Task.id == conv.task_id, Task.owner_id == user.id))
    if not task_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Not found")

    result = await db.execute(
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at)
    )
    messages = result.scalars().all()
    return [
        {
            "id": m.id,
            "role": m.role,
            "content": m.content,
            "created_at": m.created_at.isoformat(),
        }
        for m in messages
    ]
