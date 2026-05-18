import json

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.models import Category, Chapter, Character, Note, Source
from ..utils.file_sync import (
    get_task_dir,
    sync_chapter_to_file,
    sync_characters_to_file,
    sync_doc_to_file,
    sync_note_to_file,
    sync_source_to_file,
    truncate,
)

# OpenAI function calling tool definitions
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "create_chapter",
            "description": "创建一个新章节。当用户要求写新章节、新建章节、开始新的一章时使用。",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "章节标题，如 '第一章 风起'"},
                    "content": {"type": "string", "description": "章节正文内容（可选，默认为空）"},
                },
                "required": ["title"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "edit_chapter",
            "description": "编辑已有章节的内容。当用户要求改写、续写、修改某章节时使用。需要先知道 chapter_id，可用 list_chapters 或 read_chapter 获取。",
            "parameters": {
                "type": "object",
                "properties": {
                    "chapter_id": {"type": "integer", "description": "章节 ID"},
                    "content": {"type": "string", "description": "新的章节内容（完整替换）"},
                },
                "required": ["chapter_id", "content"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_character",
            "description": "创建一个新角色设定。当用户要求设计人物、创建角色时使用。",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "角色名称"},
                    "role": {"type": "string", "description": "角色定位，如 '主角'、'反派'、'配角'"},
                    "personality": {"type": "string", "description": "性格特点"},
                    "backstory": {"type": "string", "description": "背景故事"},
                    "relationships": {"type": "string", "description": "与其他角色的关系"},
                },
                "required": ["name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "update_character",
            "description": "更新已有角色的信息。需要先知道 character_id，可用 list_characters 获取。",
            "parameters": {
                "type": "object",
                "properties": {
                    "character_id": {"type": "integer", "description": "角色 ID"},
                    "name": {"type": "string", "description": "角色名称"},
                    "role": {"type": "string", "description": "角色定位"},
                    "personality": {"type": "string", "description": "性格特点"},
                    "backstory": {"type": "string", "description": "背景故事"},
                    "relationships": {"type": "string", "description": "人物关系"},
                },
                "required": ["character_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_note",
            "description": "创建笔记或文档。当用户要求记录想法、写笔记、创建文档时使用。",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "笔记标题"},
                    "content": {"type": "string", "description": "笔记内容"},
                    "category_id": {"type": "integer", "description": "分类 ID（可选，不传则为未分类）"},
                },
                "required": ["title", "content"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_source",
            "description": "创建参考素材。当用户提供或要求添加参考资料时使用。",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "素材名称"},
                    "content": {"type": "string", "description": "素材内容"},
                },
                "required": ["name", "content"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_chapter",
            "description": "读取某个章节的完整内容。当需要查看章节内容以进行编辑或分析时使用。",
            "parameters": {
                "type": "object",
                "properties": {
                    "chapter_id": {"type": "integer", "description": "章节 ID"},
                },
                "required": ["chapter_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_source",
            "description": "读取某个素材的完整内容。当需要查看素材详情时使用。",
            "parameters": {
                "type": "object",
                "properties": {
                    "source_id": {"type": "integer", "description": "素材 ID"},
                },
                "required": ["source_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_chapters",
            "description": "列出当前任务的所有章节（标题和 ID）。用于了解项目结构后再进行具体操作。",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_characters",
            "description": "列出当前任务的所有角色（名称、ID 和定位）。用于了解已有角色后再进行具体操作。",
            "parameters": {"type": "object", "properties": {}},
        },
    },
]

# Tool name → human-readable Chinese description for frontend display
TOOL_LABELS = {
    "create_chapter": "创建章节",
    "edit_chapter": "编辑章节",
    "create_character": "创建角色",
    "update_character": "更新角色",
    "create_note": "创建笔记",
    "create_source": "创建素材",
    "read_chapter": "读取章节",
    "read_source": "读取素材",
    "list_chapters": "列出章节",
    "list_characters": "列出角色",
}


async def execute_tool(tool_name: str, args: dict, task_id: int, db: AsyncSession) -> dict:
    """Execute a tool and return the result dict."""
    try:
        if tool_name == "create_chapter":
            return await _create_chapter(args, task_id, db)
        elif tool_name == "edit_chapter":
            return await _edit_chapter(args, task_id, db)
        elif tool_name == "create_character":
            return await _create_character(args, task_id, db)
        elif tool_name == "update_character":
            return await _update_character(args, task_id, db)
        elif tool_name == "create_note":
            return await _create_note(args, task_id, db)
        elif tool_name == "create_source":
            return await _create_source(args, task_id, db)
        elif tool_name == "read_chapter":
            return await _read_chapter(args, task_id, db)
        elif tool_name == "read_source":
            return await _read_source(args, task_id, db)
        elif tool_name == "list_chapters":
            return await _list_chapters(task_id, db)
        elif tool_name == "list_characters":
            return await _list_characters(task_id, db)
        else:
            return {"success": False, "error": f"未知工具: {tool_name}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


async def _create_chapter(args: dict, task_id: int, db: AsyncSession) -> dict:
    result = await db.execute(
        select(Chapter.order_index).where(Chapter.task_id == task_id).order_by(Chapter.order_index.desc()).limit(1)
    )
    max_order = result.scalar_one_or_none() or 0
    chapter = Chapter(
        task_id=task_id,
        title=args.get("title", "新章节"),
        content=args.get("content", ""),
        order_index=max_order + 1,
    )
    db.add(chapter)
    await db.commit()
    await db.refresh(chapter)

    task_dir = await get_task_dir(db, task_id)
    if task_dir:
        sync_chapter_to_file(task_dir, chapter)

    return {"success": True, "chapter_id": chapter.id, "title": chapter.title}


async def _edit_chapter(args: dict, task_id: int, db: AsyncSession) -> dict:
    chapter_id = args.get("chapter_id")
    result = await db.execute(
        select(Chapter).where(Chapter.id == chapter_id, Chapter.task_id == task_id)
    )
    chapter = result.scalar_one_or_none()
    if not chapter:
        return {"success": False, "error": "章节不存在"}

    from ..models.models import ChapterVersion
    if chapter.content:
        db.add(ChapterVersion(
            chapter_id=chapter.id,
            version=chapter.version,
            title=chapter.title,
            content=chapter.content,
        ))
        chapter.version += 1

    chapter.content = args.get("content", chapter.content)
    if "title" in args:
        chapter.title = args["title"]
    await db.commit()

    task_dir = await get_task_dir(db, task_id)
    if task_dir:
        await db.refresh(chapter)
        sync_chapter_to_file(task_dir, chapter)

    return {"success": True, "chapter_id": chapter.id, "title": chapter.title}


async def _create_character(args: dict, task_id: int, db: AsyncSession) -> dict:
    char = Character(
        task_id=task_id,
        name=args.get("name", ""),
        role=args.get("role", ""),
        personality=args.get("personality", ""),
        backstory=args.get("backstory", ""),
        relationships=args.get("relationships", ""),
    )
    db.add(char)
    await db.commit()
    await db.refresh(char)

    task_dir = await get_task_dir(db, task_id)
    if task_dir:
        result = await db.execute(select(Character).where(Character.task_id == task_id))
        all_chars = result.scalars().all()
        sync_characters_to_file(task_dir, all_chars)

    return {"success": True, "character_id": char.id, "name": char.name}


async def _update_character(args: dict, task_id: int, db: AsyncSession) -> dict:
    char_id = args.get("character_id")
    result = await db.execute(
        select(Character).where(Character.id == char_id, Character.task_id == task_id)
    )
    char = result.scalar_one_or_none()
    if not char:
        return {"success": False, "error": "角色不存在"}

    for field in ("name", "role", "personality", "backstory", "relationships"):
        if field in args:
            setattr(char, field, args[field])
    await db.commit()

    task_dir = await get_task_dir(db, task_id)
    if task_dir:
        result = await db.execute(select(Character).where(Character.task_id == task_id))
        all_chars = result.scalars().all()
        sync_characters_to_file(task_dir, all_chars)

    return {"success": True, "character_id": char.id, "name": char.name}


async def _create_note(args: dict, task_id: int, db: AsyncSession) -> dict:
    note = Note(
        task_id=task_id,
        title=args.get("title", ""),
        content=args.get("content", ""),
        category_id=args.get("category_id"),
    )
    db.add(note)
    await db.commit()
    await db.refresh(note)

    task_dir = await get_task_dir(db, task_id)
    if task_dir:
        if note.category_id:
            cat_result = await db.execute(select(Category).where(Category.id == note.category_id))
            cat = cat_result.scalar_one_or_none()
            if cat:
                sync_doc_to_file(task_dir, cat.name, note)
        else:
            sync_note_to_file(task_dir, note)

    return {"success": True, "note_id": note.id, "title": note.title}


async def _create_source(args: dict, task_id: int, db: AsyncSession) -> dict:
    content = args.get("content", "")
    source = Source(
        task_id=task_id,
        name=args.get("name", ""),
        type="text",
        content=content,
        word_count=len(content),
    )
    db.add(source)
    await db.commit()
    await db.refresh(source)

    task_dir = await get_task_dir(db, task_id)
    if task_dir:
        sync_source_to_file(task_dir, source)

    return {"success": True, "source_id": source.id, "name": source.name}


async def _read_chapter(args: dict, task_id: int, db: AsyncSession) -> dict:
    chapter_id = args.get("chapter_id")
    result = await db.execute(
        select(Chapter).where(Chapter.id == chapter_id, Chapter.task_id == task_id)
    )
    chapter = result.scalar_one_or_none()
    if not chapter:
        return {"success": False, "error": "章节不存在"}
    return {
        "success": True,
        "chapter_id": chapter.id,
        "title": chapter.title,
        "content": chapter.content or "",
    }


async def _read_source(args: dict, task_id: int, db: AsyncSession) -> dict:
    source_id = args.get("source_id")
    result = await db.execute(
        select(Source).where(Source.id == source_id, Source.task_id == task_id)
    )
    source = result.scalar_one_or_none()
    if not source:
        return {"success": False, "error": "素材不存在"}
    return {
        "success": True,
        "source_id": source.id,
        "name": source.name,
        "content": source.content or "",
    }


async def _list_chapters(task_id: int, db: AsyncSession) -> dict:
    result = await db.execute(
        select(Chapter).where(Chapter.task_id == task_id).order_by(Chapter.order_index)
    )
    chapters = result.scalars().all()
    return {
        "success": True,
        "chapters": [
            {"id": c.id, "title": c.title, "order_index": c.order_index, "has_content": bool(c.content)}
            for c in chapters
        ],
    }


async def _list_characters(task_id: int, db: AsyncSession) -> dict:
    result = await db.execute(
        select(Character).where(Character.task_id == task_id)
    )
    chars = result.scalars().all()
    return {
        "success": True,
        "characters": [
            {"id": c.id, "name": c.name, "role": c.role}
            for c in chars
        ],
    }
