import re
import shutil
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..core.database import get_db
from ..core.deps import get_current_user
from ..models.models import Category, Chapter, Conversation, Task, Template
from ..utils.file_sync import ensure_category_dir, ensure_task_dir, sync_category_to_file, sync_chapter_to_file, sync_task_meta

router = APIRouter(prefix="/tasks", tags=["tasks"])

DEFAULT_CATEGORIES = [
    ("故事背景", "🌍"),
    ("主要人物", "👤"),
    ("故事线", "📖"),
]


class TaskCreate(BaseModel):
    title: str
    description: str = ""
    type: str = "novel"  # novel / script / storyboard
    directory_path: str
    template_id: int | None = None


class TaskUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    status: str | None = None


@router.get("/")
async def list_tasks(user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Task)
        .where(Task.owner_id == user.id)
        .options(selectinload(Task.chapters))
        .order_by(Task.updated_at.desc())
    )
    tasks = result.scalars().all()
    return [
        {
            "id": t.id,
            "title": t.title,
            "description": t.description,
            "type": t.type,
            "status": t.status,
            "chapter_count": len(t.chapters),
            "directory_path": t.directory_path,
            "created_at": t.created_at.isoformat(),
            "updated_at": t.updated_at.isoformat() if t.updated_at else None,
        }
        for t in tasks
    ]


class DirectoryRequest(BaseModel):
    path: str


@router.post("/verify-directory")
async def verify_directory(req: DirectoryRequest, user=Depends(get_current_user)):
    """验证目录路径是否存在且为空"""
    dir_path = req.path.strip()
    if not dir_path:
        return {"valid": False, "error": "路径不能为空"}
    p = Path(dir_path)
    if not p.exists():
        return {"valid": False, "error": "目录不存在，请先创建文件夹"}
    if not p.is_dir():
        return {"valid": False, "error": "路径不是一个文件夹"}
    if any(p.iterdir()):
        return {"valid": False, "error": "文件夹必须为空"}
    return {"valid": True, "name": p.name}


class BrowseRequest(BaseModel):
    path: str = ""


@router.post("/browse-directory")
async def browse_directory(req: BrowseRequest, user=Depends(get_current_user)):
    """列出指定目录下的子文件夹"""
    import os

    # Default to home directory
    if not req.path.strip():
        base_path = Path.home()
    else:
        base_path = Path(req.path.strip())

    if not base_path.exists() or not base_path.is_dir():
        return {"error": "目录不存在", "current": str(base_path), "folders": []}

    folders = []
    try:
        for item in sorted(base_path.iterdir()):
            if item.is_dir() and not item.name.startswith("."):
                folders.append({
                    "name": item.name,
                    "path": str(item),
                })
    except PermissionError:
        return {"error": "无权限访问", "current": str(base_path), "folders": []}

    return {
        "current": str(base_path),
        "parent": str(base_path.parent) if base_path.parent != base_path else None,
        "folders": folders[:50],  # Limit to 50 folders
    }


@router.post("/open-directory")
async def open_directory(user=Depends(get_current_user)):
    """打开系统文件夹选择对话框，返回选中的路径"""
    import subprocess
    import platform

    try:
        system = platform.system()
        if system == "Darwin":
            # On macOS, we need to allow stdin for the dialog
            result = subprocess.run(
                ["osascript", "-e", 'POSIX path of (choose folder with prompt "选择项目文件夹（必须为空）")'],
                capture_output=True, text=True, timeout=60,
                stdin=subprocess.DEVNULL,
            )
        elif system == "Windows":
            result = subprocess.run(
                ["powershell", "-Command",
                 "Add-Type -AssemblyName System.Windows.Forms; "
                 "$f = New-Object System.Windows.Forms.FolderBrowserDialog; "
                 "$f.Description = '选择项目文件夹（必须为空）'; "
                 "$f.ShowNewFolderButton = $true; "
                 "if ($f.ShowDialog() -eq 'OK') { $f.SelectedPath }"],
                capture_output=True, text=True, timeout=60,
                stdin=subprocess.DEVNULL,
            )
        else:
            result = subprocess.run(
                ["zenity", "--file-selection", "--directory", "--title=选择项目文件夹（必须为空）"],
                capture_output=True, text=True, timeout=60,
                stdin=subprocess.DEVNULL,
            )

        if result.returncode != 0:
            return {"selected": False, "error": "未选择文件夹"}

        selected_path = result.stdout.strip()
        if not selected_path:
            return {"selected": False, "error": "未选择文件夹"}

        # Verify it's empty
        p = Path(selected_path)
        if not p.is_dir():
            return {"selected": False, "error": "选择的不是一个文件夹"}
        if any(p.iterdir()):
            return {"selected": False, "error": "文件夹必须为空，请选择一个空文件夹"}

        return {"selected": True, "path": selected_path, "name": p.name}

    except subprocess.TimeoutExpired:
        return {"selected": False, "error": "选择超时"}
    except FileNotFoundError:
        return {"selected": False, "error": "系统不支持文件夹选择对话框，请手动输入路径"}
    except Exception as e:
        return {"selected": False, "error": str(e)}


@router.post("/")
async def create_task(req: TaskCreate, user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    dir_path = req.directory_path.strip()
    if not dir_path:
        raise HTTPException(status_code=400, detail="目录路径不能为空")

    # Validate directory exists and is empty
    p = Path(dir_path)
    if not p.exists():
        raise HTTPException(status_code=400, detail="目录不存在，请先创建文件夹")
    if not p.is_dir():
        raise HTTPException(status_code=400, detail="路径不是一个文件夹")
    if any(p.iterdir()):
        raise HTTPException(status_code=400, detail="文件夹必须为空")

    task = Task(
        owner_id=user.id,
        title=req.title,
        description=req.description,
        type=req.type,
        directory_path=dir_path,
    )
    db.add(task)
    await db.flush()

    # Apply template if provided
    if req.template_id:
        tpl_result = await db.execute(select(Template).where(Template.id == req.template_id))
        template = tpl_result.scalar_one_or_none()
        if template:
            if not task.description:
                task.description = template.content[:500]
            headings = re.findall(r'^##\s+(.+)$', template.content, re.MULTILINE)
            if headings:
                for i, heading in enumerate(headings):
                    db.add(Chapter(task_id=task.id, title=heading.strip(), content="", order_index=i))
            else:
                db.add(Chapter(task_id=task.id, title="第一章", content="", order_index=0))
        else:
            db.add(Chapter(task_id=task.id, title="第一章", content="", order_index=0))
    else:
        chapter = Chapter(task_id=task.id, title="第一章", content="", order_index=0)
        db.add(chapter)

    # Create default categories
    for i, (cat_name, cat_icon) in enumerate(DEFAULT_CATEGORIES):
        db.add(Category(task_id=task.id, name=cat_name, icon=cat_icon, sort_order=i))

    # Auto-create conversation
    conv = Conversation(task_id=task.id)
    db.add(conv)

    await db.commit()

    # Sync to filesystem
    await db.refresh(task, ["chapters", "categories"])
    ensure_task_dir(dir_path)
    sync_task_meta(dir_path, task)
    for ch in task.chapters:
        sync_chapter_to_file(dir_path, ch)
    for cat in task.categories:
        ensure_category_dir(dir_path, cat.name)
        sync_category_to_file(dir_path, cat)

    return {"id": task.id, "title": task.title, "type": task.type, "status": task.status, "directory_path": task.directory_path}


@router.get("/{task_id}")
async def get_task(task_id: int, user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Task)
        .where(Task.id == task_id, Task.owner_id == user.id)
        .options(selectinload(Task.chapters), selectinload(Task.conversations))
    )
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return {
        "id": task.id,
        "title": task.title,
        "description": task.description,
        "type": task.type,
        "status": task.status,
        "directory_path": task.directory_path,
        "chapters": [
            {"id": c.id, "title": c.title, "order_index": c.order_index, "version": c.version}
            for c in task.chapters
        ],
        "conversation_id": task.conversations[0].id if task.conversations else None,
        "created_at": task.created_at.isoformat(),
        "updated_at": task.updated_at.isoformat() if task.updated_at else None,
    }


@router.patch("/{task_id}")
async def update_task(
    task_id: int, req: TaskUpdate, user=Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Task).where(Task.id == task_id, Task.owner_id == user.id))
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    if req.title is not None:
        task.title = req.title
    if req.description is not None:
        task.description = req.description
    if req.status is not None:
        task.status = req.status
    await db.commit()
    return {"ok": True}


@router.delete("/{task_id}")
async def delete_task(task_id: int, user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Task).where(Task.id == task_id, Task.owner_id == user.id))
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    dir_path = task.directory_path
    await db.delete(task)
    await db.commit()

    # Clean up filesystem
    if dir_path:
        p = Path(dir_path)
        if p.is_dir():
            shutil.rmtree(dir_path, ignore_errors=True)

    return {"ok": True}
