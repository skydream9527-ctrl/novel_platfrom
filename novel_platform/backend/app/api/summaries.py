from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.database import get_db
from ..core.deps import get_current_user
from ..models.models import Chapter, Task
from ..services.llm import chat_once

router = APIRouter(prefix="/summaries", tags=["summaries"])


class SummaryRequest(BaseModel):
    chapter_id: int


SUMMARY_PROMPT = """请对以下章节内容进行简要分析，输出格式如下：

**一句话摘要：** （用一句话概括本章核心内容）

**关键人物：** （列出本章出现的人物，用逗号分隔，没有则写"无"）

**主要事件：** （列出 2-3 个关键事件，每行一个）

章节内容：
{content}"""


@router.post("/chapter")
async def generate_chapter_summary(
    req: SummaryRequest, user=Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Chapter).where(Chapter.id == req.chapter_id).join(Task).where(Task.owner_id == user.id)
    )
    chapter = result.scalar_one_or_none()
    if not chapter:
        raise HTTPException(status_code=404, detail="Chapter not found")

    if not chapter.content or not chapter.content.strip():
        return {"summary": "章节内容为空，无法生成摘要。"}

    prompt = SUMMARY_PROMPT.format(content=chapter.content[:6000])
    messages = [{"role": "user", "content": prompt}]
    summary = await chat_once(messages)
    return {"summary": summary}
