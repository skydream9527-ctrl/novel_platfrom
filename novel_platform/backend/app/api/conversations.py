from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.database import get_db
from ..core.deps import get_current_user
from ..models.models import Conversation, Message, Task

router = APIRouter(prefix="/conversations", tags=["conversations"])


class ConversationCreate(BaseModel):
    task_id: int
    title: str = "新对话"


class ConversationUpdate(BaseModel):
    title: str | None = None


@router.get("/by-task/{task_id}")
async def list_conversations(
    task_id: int,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """列出任务的所有对话"""
    task = await db.execute(select(Task).where(Task.id == task_id, Task.owner_id == user.id))
    if not task.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Task not found")

    result = await db.execute(
        select(Conversation)
        .where(Conversation.task_id == task_id)
        .order_by(Conversation.created_at.desc())
    )
    conversations = result.scalars().all()
    return [
        {
            "id": c.id,
            "title": c.title,
            "created_at": c.created_at.isoformat(),
        }
        for c in conversations
    ]


@router.post("/")
async def create_conversation(
    req: ConversationCreate,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """创建新对话"""
    task = await db.execute(select(Task).where(Task.id == req.task_id, Task.owner_id == user.id))
    if not task.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Task not found")

    conv = Conversation(task_id=req.task_id, title=req.title)
    db.add(conv)
    await db.commit()
    await db.refresh(conv)

    return {"id": conv.id, "title": conv.title, "created_at": conv.created_at.isoformat()}


@router.patch("/{conversation_id}")
async def update_conversation(
    conversation_id: int,
    req: ConversationUpdate,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """更新对话标题"""
    result = await db.execute(select(Conversation).where(Conversation.id == conversation_id))
    conv = result.scalar_one_or_none()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")

    # Verify ownership
    task = await db.execute(select(Task).where(Task.id == conv.task_id, Task.owner_id == user.id))
    if not task.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Not found")

    if req.title is not None:
        conv.title = req.title
    await db.commit()

    return {"ok": True}


@router.delete("/{conversation_id}")
async def delete_conversation(
    conversation_id: int,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """删除对话"""
    result = await db.execute(select(Conversation).where(Conversation.id == conversation_id))
    conv = result.scalar_one_or_none()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")

    # Verify ownership
    task = await db.execute(select(Task).where(Task.id == conv.task_id, Task.owner_id == user.id))
    if not task.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Not found")

    await db.delete(conv)
    await db.commit()

    return {"ok": True}


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
