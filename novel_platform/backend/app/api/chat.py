import json
import re
import uuid

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from ..core.config import settings
from ..core.database import async_session
from ..models.models import Conversation, Message, Note, Source, SourceReference, Task
from ..services.llm import chat_once, chat_with_tools
from ..services.tools import TOOLS, TOOL_LABELS, execute_tool
from ..utils.file_sync import truncate

router = APIRouter(tags=["chat"])

SYSTEM_PROMPT_TEMPLATE = """你是一个专业的文字创作助手，帮助用户进行{type_name}创作。

## 你的能力
你可以直接操作用户的创作项目。当用户要求你创建、编辑或管理内容时，请使用工具直接完成操作，而不是只给出建议。

### 可用工具
- create_chapter: 创建新章节
- edit_chapter: 编辑已有章节的内容（需先获取 chapter_id）
- create_character: 创建角色设定
- update_character: 更新已有角色信息（需先获取 character_id）
- create_note: 创建笔记或文档
- create_source: 创建参考素材
- read_chapter: 读取某个章节的内容
- read_source: 读取某个素材的内容
- list_chapters: 列出所有章节（获取 ID 和标题）
- list_characters: 列出所有角色（获取 ID 和名称）

### 使用原则
1. 当用户要求创建或修改内容时，直接使用工具完成操作
2. 操作完成后，简要告知用户做了什么
3. 需要先了解现有内容时，先用 read/list 工具查看
4. 修改章节前，先用 read_chapter 读取当前内容，在此基础上修改
5. 引用素材时使用 [编号] 标记
6. 生成内容使用 Markdown 格式

创作类型：{type_name}
{sources_section}
{notes_section}
请用中文回复。"""

TYPE_NAMES = {"novel": "小说", "script": "剧本", "storyboard": "分镜脚本"}


@router.websocket("/ws/conversations/{conversation_id}")
async def ws_conversation(websocket: WebSocket, conversation_id: int):
    async with async_session() as db:
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

            model = data.get("model")

            async with async_session() as db:
                user_msg = Message(conversation_id=conversation_id, role="user", content=user_content)
                db.add(user_msg)
                await db.commit()

                result = await db.execute(
                    select(Message)
                    .where(Message.conversation_id == conversation_id)
                    .order_by(Message.created_at.desc())
                    .limit(20)
                )
                history = list(reversed(result.scalars().all()))

                result = await db.execute(select(Source).where(Source.task_id == task.id))
                sources = result.scalars().all()

                result = await db.execute(select(Note).where(Note.task_id == task.id))
                notes = result.scalars().all()

            # Build system prompt
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

            messages = [
                {"role": "system", "content": SYSTEM_PROMPT_TEMPLATE.format(
                    type_name=type_name,
                    sources_section=sources_section,
                    notes_section=notes_section,
                )}
            ]
            for msg in history:
                messages.append({"role": msg.role, "content": msg.content})

            await websocket.send_json({"type": "start"})

            # Tool use loop
            full_response = []
            max_rounds = settings.llm_max_tool_rounds

            for _round in range(max_rounds):
                tool_calls_this_round = []

                async for event in chat_with_tools(messages, TOOLS, model=model):
                    if event["type"] == "text":
                        full_response.append(event["content"])
                        await websocket.send_json({"type": "chunk", "content": event["content"]})

                    elif event["type"] == "tool_call":
                        tool_name = event["name"]
                        tool_args = event["arguments"]
                        call_id = event["id"] or str(uuid.uuid4())

                        label = TOOL_LABELS.get(tool_name, tool_name)
                        await websocket.send_json({
                            "type": "tool_call",
                            "call_id": call_id,
                            "tool": tool_name,
                            "label": label,
                            "args": tool_args,
                        })

                        async with async_session() as db:
                            result = await execute_tool(tool_name, tool_args, task_id, db)

                        await websocket.send_json({
                            "type": "tool_result",
                            "call_id": call_id,
                            "success": result.get("success", False),
                            "result": result,
                        })

                        tool_calls_this_round.append({
                            "call_id": call_id,
                            "tool_name": tool_name,
                            "args": tool_args,
                            "result": result,
                        })

                if not tool_calls_this_round:
                    break

                # Append tool call/result messages for next LLM round
                assistant_tool_calls = []
                for tc in tool_calls_this_round:
                    assistant_tool_calls.append({
                        "id": tc["call_id"],
                        "type": "function",
                        "function": {
                            "name": tc["tool_name"],
                            "arguments": json.dumps(tc["args"], ensure_ascii=False),
                        },
                    })
                messages.append({
                    "role": "assistant",
                    "content": None,
                    "tool_calls": assistant_tool_calls,
                })
                for tc in tool_calls_this_round:
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tc["call_id"],
                        "content": json.dumps(tc["result"], ensure_ascii=False),
                    })

            assistant_content = "".join(full_response)

            # Save assistant message and track citations
            async with async_session() as db:
                assistant_msg = Message(
                    conversation_id=conversation_id, role="assistant", content=assistant_content
                )
                db.add(assistant_msg)
                await db.flush()

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

            # Generate suggestions
            try:
                sug_prompt = f"根据以下对话，生成2-3个用户可能想追问的简短问题。只输出问题，每行一个，不要编号。\n\n用户：{user_content}\n助手：{assistant_content[:1000]}"
                sug_messages = [{"role": "user", "content": sug_prompt}]
                suggestions_text = await chat_once(sug_messages, model=model)
                suggestions = [s.strip() for s in suggestions_text.strip().split('\n') if s.strip() and len(s.strip()) > 2][:3]
                if suggestions:
                    await websocket.send_json({"type": "suggestions", "suggestions": suggestions})
            except Exception:
                pass

    except WebSocketDisconnect:
        pass
