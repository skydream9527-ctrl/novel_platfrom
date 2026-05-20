from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.config import settings
from ..core.database import get_db
from ..core.deps import get_current_user
from ..models.models import Chapter, Note, Source, Task
from ..services.llm import chat_once
from ..utils.file_sync import truncate

router = APIRouter(prefix="/ai", tags=["ai"])


ACTIONS = {
    "continue": "请根据以下内容，自然地续写下去，保持风格一致，续写约300字：\n\n{text}",
    "rewrite": "请改写以下内容，保持原意但使用不同的表达方式：\n\n{text}",
    "expand": "请将以下内容扩写，增加更多细节和描写，使内容更加丰富：\n\n{text}",
    "shorten": "请将以下内容精简压缩，保留核心信息，去除冗余描写：\n\n{text}",
    "translate_en": "请将以下内容翻译为英文，保持文学性：\n\n{text}",
    "translate_ja": "请将以下内容翻译为日文，保持文学性：\n\n{text}",
    "polish": "请润色以下内容，提升文笔质量，使语言更优美流畅：\n\n{text}",
    "dialogue": "请根据以下内容，编写一段生动的对话场景：\n\n{text}",
}


class AIActionRequest(BaseModel):
    action: str
    text: str
    chapter_id: int | None = None
    task_id: int | None = None


@router.post("/actions")
async def ai_action(req: AIActionRequest, user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    if req.action not in ACTIONS:
        raise HTTPException(status_code=400, detail=f"Unknown action: {req.action}")

    prompt = ACTIONS[req.action].format(text=req.text)

    # Load context: sources + notes + chapter content
    context_parts = []
    if req.task_id:
        result = await db.execute(select(Source).where(Source.task_id == req.task_id))
        sources = result.scalars().all()
        for s in sources[:3]:
            context_parts.append(f"【素材：{s.name}】\n{truncate(s.content, 1500)}")

        result = await db.execute(select(Note).where(Note.task_id == req.task_id))
        notes = result.scalars().all()
        for n in notes[:3]:
            context_parts.append(f"【笔记：{n.title}】\n{truncate(n.content, 1000)}")

    if req.chapter_id:
        result = await db.execute(select(Chapter).where(Chapter.id == req.chapter_id))
        chapter = result.scalar_one_or_none()
        if chapter and chapter.content:
            context_parts.append(f"【当前章节：{chapter.title}】\n{truncate(chapter.content, 2000)}")

    system = "你是一个专业的文字创作助手。请直接输出结果，不要解释你的操作。保持原文风格。"
    if context_parts:
        system += "\n\n以下是参考上下文：\n" + "\n\n---\n\n".join(context_parts)

    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": prompt},
    ]

    result = await chat_once(messages)
    return {"result": result, "action": req.action}


GENERATE_PROMPTS = {
    "outline": "请根据以下素材和已写内容，生成一份完整的故事大纲，包含：故事背景、主要人物、起承转合四幕结构、核心冲突和结局方向。使用 Markdown 格式。",
    "character_map": "请根据以下素材和已写内容，梳理所有角色之间的关系，生成一份角色关系图谱说明，包含：角色名称、身份、与其他角色的关系、在故事中的作用。",
    "timeline": "请根据以下素材和已写内容，提取所有事件并按时间顺序排列，生成一份故事时间线，包含：时间点、事件描述、涉及角色。",
    "faq": "请根据以下素材和已写内容，生成 5-8 个读者可能会问的常见问题及其解答，涵盖世界观、人物动机、故事逻辑等方面。",
    "chapter_summary": "请为以下章节内容生成一份详细摘要，包含：一句话总结、关键人物、主要事件、与整体故事的关联。",
}


class GenerateRequest(BaseModel):
    task_id: int
    type: str


@router.post("/generate")
async def ai_generate(req: GenerateRequest, user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    if req.type not in GENERATE_PROMPTS:
        raise HTTPException(status_code=400, detail=f"Unknown generate type: {req.type}")

    # Load task
    result = await db.execute(select(Task).where(Task.id == req.task_id, Task.owner_id == user.id))
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    # Build context
    context_parts = []

    # Sources
    result = await db.execute(select(Source).where(Source.task_id == req.task_id))
    sources = result.scalars().all()
    for s in sources[:5]:
        context_parts.append(f"【素材：{s.name}】\n{truncate(s.content, 1500)}")

    # Characters
    from ..models.models import Character
    result = await db.execute(select(Character).where(Character.task_id == req.task_id))
    chars = result.scalars().all()
    for c in chars:
        char_info = f"角色：{c.name}，身份：{c.role}"
        if c.personality:
            char_info += f"，性格：{truncate(c.personality, 200)}"
        context_parts.append(f"【{char_info}】")

    # Chapters
    result = await db.execute(select(Chapter).where(Chapter.task_id == req.task_id).order_by(Chapter.order_index))
    chapters = result.scalars().all()
    for ch in chapters:
        if ch.content:
            context_parts.append(f"【章节：{ch.title}】\n{truncate(ch.content, 1500)}")

    # Notes
    result = await db.execute(select(Note).where(Note.task_id == req.task_id))
    notes = result.scalars().all()
    for n in notes[:3]:
        context_parts.append(f"【笔记：{n.title}】\n{truncate(n.content, 1000)}")

    prompt = GENERATE_PROMPTS[req.type]
    system = f"你是一个专业的文字创作助手。任务类型：{task.title}。请用中文回复，使用 Markdown 格式。"
    if context_parts:
        system += "\n\n以下是创作素材和已有内容：\n" + "\n\n---\n\n".join(context_parts)

    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": prompt},
    ]

    result = await chat_once(messages)
    return {"result": result, "type": req.type}


class RecommendRequest(BaseModel):
    task_id: int


@router.post("/recommend-sources")
async def recommend_sources(req: RecommendRequest, user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Task).where(Task.id == req.task_id, Task.owner_id == user.id))
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    # Load existing sources
    result = await db.execute(select(Source).where(Source.task_id == req.task_id))
    sources = result.scalars().all()
    existing = "\n".join(f"- {s.name}" for s in sources) if sources else "暂无素材"

    prompt = f"""基于以下创作任务和已有素材，推荐 3-5 个相关的补充素材主题。

任务标题：{task.title}
任务描述：{task.description or '无'}
已有素材：
{existing}

请为每个推荐主题提供：
1. 标题
2. 简要说明（为什么对创作有帮助）

请直接输出推荐列表，使用 Markdown 格式。"""

    messages = [
        {"role": "system", "content": "你是一个专业的文字创作助手，擅长分析创作需求并推荐参考资料。"},
        {"role": "user", "content": prompt},
    ]

    result = await chat_once(messages)
    return {"result": result}


@router.get("/models")
async def get_available_models(user=Depends(get_current_user)):
    """获取可用的模型列表"""
    return {
        "models": settings.available_models_list,
        "default": settings.llm_model,
    }


class SourceSummaryRequest(BaseModel):
    source_id: int


class SourceSummaryUpdate(BaseModel):
    summary: str
    keywords: str


@router.post("/source-summary")
async def generate_source_summary(
    req: SourceSummaryRequest,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """为素材自动生成摘要和关键词"""
    result = await db.execute(
        select(Source).join(Task).where(Source.id == req.source_id, Task.owner_id == user.id)
    )
    source = result.scalar_one_or_none()
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")

    content_preview = truncate(source.content, 4000)

    prompt = f"""请为以下素材生成一份简洁的摘要和关键词。

素材名称：{source.name}
素材内容：
{content_preview}

请按以下格式输出：
## 摘要
（200字以内的摘要，概括素材的核心内容）

## 关键词
（5-8个关键词，用逗号分隔）"""

    messages = [
        {"role": "system", "content": "你是一个专业的文本分析助手。请用中文回复，使用 Markdown 格式。"},
        {"role": "user", "content": prompt},
    ]

    result = await chat_once(messages)

    # Parse summary and keywords from result
    summary = ""
    keywords = ""
    lines = result.split("\n")
    current_section = None
    summary_lines = []

    for line in lines:
        if line.strip().startswith("## 摘要"):
            current_section = "summary"
            continue
        elif line.strip().startswith("## 关键词"):
            current_section = "keywords"
            continue

        if current_section == "summary":
            summary_lines.append(line.strip())
        elif current_section == "keywords":
            keywords = line.strip().lstrip("-").strip()

    summary = " ".join(summary_lines).strip()

    # Update source with summary and keywords
    source.summary = summary
    source.keywords = keywords
    await db.commit()

    return {"summary": summary, "keywords": keywords}


@router.patch("/source-summary/{source_id}")
async def update_source_summary(
    source_id: int,
    req: SourceSummaryUpdate,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """更新素材摘要和关键词"""
    result = await db.execute(
        select(Source).join(Task).where(Source.id == source_id, Task.owner_id == user.id)
    )
    source = result.scalar_one_or_none()
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")

    source.summary = req.summary
    source.keywords = req.keywords
    await db.commit()

    return {"ok": True}
