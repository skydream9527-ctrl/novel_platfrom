import json
import re

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..core.database import async_session
from ..models.models import Conversation, Message, Note, Source, SourceReference, Task
from ..services.llm import chat_once, chat_stream
from ..utils.file_sync import truncate

router = APIRouter(tags=["chat"])


SYSTEM_PROMPT_TEMPLATE = """你是一个专业的文字创作助手，帮助用户进行{type_name}创作。

你的能力：
- 根据用户需求生成高质量的文字内容
- 支持小说、剧本、分镜脚本等多种创作形式
- 可以续写、改写、扩写、缩写已有内容
- 可以设计人物、构建世界观、编写对话

创作类型：{type_name}
{sources_section}
{notes_section}
请用中文回复。生成的内容请使用 Markdown 格式。
当引用素材内容时，请使用编号标记如 [1]、[2]，编号对应上方素材列表的顺序。"""

TYPE_NAMES = {"novel": "小说", "script": "剧本", "storyboard": "分镜脚本"}


@router.websocket("/ws/conversations/{conversation_id}")
async def ws_conversation(websocket: WebSocket, conversation_id: int):
    async with async_session() as db:
        # Verify conversation exists
        result = await db.execute(
            select(Conversation)
            .where(Conversation.id == conversation_id)
            .options(selectinload(Conversation.task))
        )
        conv = result.scalar_one_or_none()
        if not conv:
            await websocket.close(code=4003, reason="Not found")
            return

        task = conv.task
        task_id = task.id

    await websocket.accept()

    try:
        while True:
            data = await websocket.receive_json()
            user_content = data.get("content", "").strip()
            if not user_content:
                continue

            async with async_session() as db:
                # Save user message
                user_msg = Message(conversation_id=conversation_id, role="user", content=user_content)
                db.add(user_msg)
                await db.commit()

                # Load recent message history
                result = await db.execute(
                    select(Message)
                    .where(Message.conversation_id == conversation_id)
                    .order_by(Message.created_at.desc())
                    .limit(20)
                )
                history = list(reversed(result.scalars().all()))

                # Load sources for this task
                result = await db.execute(
                    select(Source).where(Source.task_id == task.id)
                )
                sources = result.scalars().all()

                # Load notes for this task
                result = await db.execute(
                    select(Note).where(Note.task_id == task.id)
                )
                notes = result.scalars().all()

            # Build messages for LLM
            type_name = TYPE_NAMES.get(task.type, "文字")
            sources_section = ""
            if sources:
                source_parts = []
                for i, s in enumerate(sources, 1):
                    source_parts.append(f"[{i}] 【{s.name}】\n{truncate(s.content, 3000)}")
                sources_section = "\n\n以下是用户提供的参考素材，请基于这些素材回答问题（引用时使用 [编号] 标记）：\n\n" + "\n\n---\n\n".join(source_parts)

            notes_section = ""
            if notes:
                note_parts = []
                for n in notes:
                    note_parts.append(f"【笔记：{n.title}】\n{truncate(n.content, 2000)}")
                notes_section = "\n\n以下是用户的创作笔记，可作为参考：\n\n" + "\n\n---\n\n".join(note_parts)

            messages = [{"role": "system", "content": SYSTEM_PROMPT_TEMPLATE.format(type_name=type_name, sources_section=sources_section, notes_section=notes_section)}]
            for msg in history:
                messages.append({"role": msg.role, "content": msg.content})

            # Stream response
            await websocket.send_json({"type": "start"})

            full_response = []
            async for chunk in chat_stream(messages):
                full_response.append(chunk)
                await websocket.send_json({"type": "chunk", "content": chunk})

            assistant_content = "".join(full_response)

            # Save assistant message and track citations
            async with async_session() as db:
                assistant_msg = Message(
                    conversation_id=conversation_id, role="assistant", content=assistant_content
                )
                db.add(assistant_msg)
                await db.flush()

                # Track source citations (F11)
                if sources:
                    citations = re.findall(r'\[(\d+)\]', assistant_content)
                    seen = set()
                    for c in citations:
                        idx = int(c) - 1
                        if 0 <= idx < len(sources) and idx not in seen:
                            seen.add(idx)
                            ref = SourceReference(source_id=sources[idx].id, message_id=assistant_msg.id)
                            db.add(ref)

                await db.commit()

            await websocket.send_json({"type": "done", "content": assistant_content})

            # Generate follow-up suggestions (F6)
            try:
                sug_prompt = f"根据以下对话，生成2-3个用户可能想追问的简短问题。只输出问题，每行一个，不要编号。\n\n用户：{user_content}\n助手：{assistant_content[:1000]}"
                sug_messages = [{"role": "user", "content": sug_prompt}]
                suggestions_text = await chat_once(sug_messages, model=None)
                suggestions = [s.strip() for s in suggestions_text.strip().split('\n') if s.strip() and len(s.strip()) > 2][:3]
                if suggestions:
                    await websocket.send_json({"type": "suggestions", "suggestions": suggestions})
            except Exception:
                pass

    except WebSocketDisconnect:
        pass
