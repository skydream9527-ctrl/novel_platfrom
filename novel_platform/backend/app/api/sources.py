from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.database import get_db
from ..core.deps import get_current_user
from ..models.models import Source, SourceReference, Task
from ..utils.file_sync import delete_source_file, get_task_dir, sync_source_to_file

router = APIRouter(prefix="/sources", tags=["sources"])


class SourceCreate(BaseModel):
    task_id: int
    name: str
    type: str = "text"  # text / url / chapter
    content: str = ""


class SourceUpdate(BaseModel):
    name: str | None = None
    content: str | None = None


@router.get("/by-task/{task_id}")
async def list_sources(task_id: int, user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    task = await db.execute(select(Task).where(Task.id == task_id, Task.owner_id == user.id))
    if not task.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Task not found")

    # Subquery for usage count
    usage_sq = (
        select(SourceReference.source_id, func.count(SourceReference.id).label("cnt"))
        .group_by(SourceReference.source_id)
        .subquery()
    )

    result = await db.execute(
        select(Source, func.coalesce(usage_sq.c.cnt, 0).label("usage_count"))
        .outerjoin(usage_sq, Source.id == usage_sq.c.source_id)
        .where(Source.task_id == task_id)
        .order_by(Source.created_at.desc())
    )
    rows = result.all()
    return [
        {
            "id": s.id,
            "name": s.name,
            "type": s.type,
            "word_count": s.word_count,
            "usage_count": usage_count,
            "created_at": s.created_at.isoformat() if s.created_at else None,
        }
        for s, usage_count in rows
    ]


@router.get("/{source_id}")
async def get_source(source_id: int, user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Source).where(Source.id == source_id).join(Task).where(Task.owner_id == user.id)
    )
    source = result.scalar_one_or_none()
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    return {
        "id": source.id,
        "task_id": source.task_id,
        "name": source.name,
        "type": source.type,
        "content": source.content,
        "word_count": source.word_count,
        "created_at": source.created_at.isoformat() if source.created_at else None,
    }


@router.post("/")
async def create_source(req: SourceCreate, user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Task).where(Task.id == req.task_id, Task.owner_id == user.id))
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    word_count = len(req.content) if req.content else 0
    source = Source(task_id=req.task_id, name=req.name, type=req.type, content=req.content, word_count=word_count)
    db.add(source)
    await db.commit()
    await db.refresh(source)

    if task.directory_path:
        sync_source_to_file(task.directory_path, source)

    return {"id": source.id, "name": source.name, "type": source.type, "word_count": source.word_count}


@router.patch("/{source_id}")
async def update_source(
    source_id: int, req: SourceUpdate, user=Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Source).where(Source.id == source_id).join(Task).where(Task.owner_id == user.id)
    )
    source = result.scalar_one_or_none()
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    if req.name is not None:
        source.name = req.name
    if req.content is not None:
        source.content = req.content
        source.word_count = len(req.content)
    await db.commit()

    dir_path = await get_task_dir(db, source.task_id)
    if dir_path:
        sync_source_to_file(dir_path, source)

    return {"ok": True}


@router.delete("/{source_id}")
async def delete_source(source_id: int, user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Source).where(Source.id == source_id).join(Task).where(Task.owner_id == user.id)
    )
    source = result.scalar_one_or_none()
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")

    old_name = source.name
    task_id = source.task_id

    await db.delete(source)
    await db.commit()

    dir_path = await get_task_dir(db, task_id)
    if dir_path:
        delete_source_file(dir_path, old_name)

    return {"ok": True}


@router.post("/upload")
async def upload_source(
    task_id: int = Form(...),
    name: str = Form(""),
    file: UploadFile = File(...),
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Task).where(Task.id == task_id, Task.owner_id == user.id))
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    filename = file.filename or "untitled"
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else "txt"
    source_name = name or filename.rsplit(".", 1)[0] if "." in filename else filename

    raw = await file.read()

    if ext in ("txt", "md"):
        content = raw.decode("utf-8", errors="replace")
    elif ext == "pdf":
        try:
            import pdfplumber
            import io
            with pdfplumber.open(io.BytesIO(raw)) as pdf:
                content = "\n\n".join(page.extract_text() or "" for page in pdf.pages)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"PDF 解析失败: {e}")
    elif ext == "docx":
        try:
            import docx
            import io
            doc = docx.Document(io.BytesIO(raw))
            content = "\n\n".join(p.text for p in doc.paragraphs)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"DOCX 解析失败: {e}")
    else:
        content = raw.decode("utf-8", errors="replace")

    source = Source(task_id=task_id, name=source_name, type="file", content=content, word_count=len(content))
    db.add(source)
    await db.commit()
    await db.refresh(source)

    if task.directory_path:
        sync_source_to_file(task.directory_path, source)

    return {"id": source.id, "name": source.name, "type": source.type, "word_count": source.word_count}


class FetchUrlRequest(BaseModel):
    task_id: int
    url: str
    name: str = ""


@router.post("/fetch-url")
async def fetch_url_source(req: FetchUrlRequest, user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Task).where(Task.id == req.task_id, Task.owner_id == user.id))
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    try:
        import httpx
        import trafilatura
        async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
            resp = await client.get(req.url)
            resp.raise_for_status()
            html = resp.text
        content = trafilatura.extract(html) or ""
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"网页抓取失败: {e}")

    if not content.strip():
        raise HTTPException(status_code=400, detail="无法提取网页内容")

    source_name = req.name or req.url[:100]
    source = Source(task_id=req.task_id, name=source_name, type="url", content=content, word_count=len(content))
    db.add(source)
    await db.commit()
    await db.refresh(source)

    if task.directory_path:
        sync_source_to_file(task.directory_path, source)

    return {"id": source.id, "name": source.name, "type": source.type, "word_count": source.word_count}
