import json
import re
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


def truncate(text: str, max_len: int) -> str:
    return text[:max_len] + "..." if len(text) > max_len else text


async def get_task_dir(db: AsyncSession, task_id: int) -> str | None:
    from ..models.models import Task
    result = await db.execute(select(Task.directory_path).where(Task.id == task_id))
    return result.scalar_one_or_none()


def _sanitize(name: str) -> str:
    return re.sub(r'[<>:"/\\|?*\x00-\x1f]', '_', name).strip().strip('.')


def ensure_task_dir(dir_path: str) -> None:
    Path(dir_path).mkdir(parents=True, exist_ok=True)
    Path(dir_path, "chapters").mkdir(exist_ok=True)
    Path(dir_path, "sources").mkdir(exist_ok=True)
    Path(dir_path, "notes").mkdir(exist_ok=True)


def ensure_category_dir(task_dir: str, category_name: str) -> None:
    """Create a category subdirectory."""
    Path(task_dir, category_name).mkdir(parents=True, exist_ok=True)


def sync_category_to_file(task_dir: str, category) -> None:
    """Write a README.md into the category folder."""
    cat_dir = Path(task_dir, category.name)
    cat_dir.mkdir(parents=True, exist_ok=True)
    readme = cat_dir / "README.md"
    readme.write_text(f"# {category.icon} {category.name}\n", encoding="utf-8")


def rename_category_dir(task_dir: str, old_name: str, new_name: str) -> None:
    """Rename a category directory."""
    old_dir = Path(task_dir, old_name)
    new_dir = Path(task_dir, new_name)
    if old_dir.is_dir() and not new_dir.exists():
        old_dir.rename(new_dir)


def delete_category_dir(task_dir: str, category_name: str) -> None:
    """Remove a category directory and all its contents."""
    import shutil
    cat_dir = Path(task_dir, category_name)
    if cat_dir.is_dir():
        shutil.rmtree(cat_dir)


def sync_doc_to_file(task_dir: str, category_name: str, note) -> None:
    """Write a document file into a category folder."""
    cat_dir = Path(task_dir, category_name)
    cat_dir.mkdir(parents=True, exist_ok=True)
    safe_name = _sanitize(note.title) or "untitled"
    filepath = cat_dir / f"{safe_name}.md"
    filepath.write_text(note.content or "", encoding="utf-8")


def delete_doc_file(task_dir: str, category_name: str, note_title: str) -> None:
    """Remove a document file from a category folder."""
    cat_dir = Path(task_dir, category_name)
    safe_name = _sanitize(note_title) or "untitled"
    filepath = cat_dir / f"{safe_name}.md"
    filepath.unlink(missing_ok=True)


def sync_chapter_to_file(task_dir: str, chapter) -> None:
    """Write or rename a chapter file. Uses chapter.id to track files."""
    chapters_dir = Path(task_dir, "chapters")
    chapters_dir.mkdir(exist_ok=True)

    safe_title = _sanitize(chapter.title) or "untitled"
    filename = f"{chapter.order_index:03d}_{safe_title}.md"
    filepath = chapters_dir / filename

    # Remove any old file for this chapter (different title/order)
    for f in chapters_dir.glob("*.md"):
        if f != filepath and f.stem.startswith(f"{chapter.order_index:03d}_"):
            f.unlink(missing_ok=True)

    filepath.write_text(chapter.content or "", encoding="utf-8")


def delete_chapter_file(task_dir: str, order_index: int, title: str) -> None:
    """Remove a chapter file from disk."""
    chapters_dir = Path(task_dir, "chapters")
    safe_title = _sanitize(title) or "untitled"
    filepath = chapters_dir / f"{order_index:03d}_{safe_title}.md"
    filepath.unlink(missing_ok=True)


def sync_source_to_file(task_dir: str, source) -> None:
    """Write a source file to disk."""
    sources_dir = Path(task_dir, "sources")
    sources_dir.mkdir(exist_ok=True)

    safe_name = _sanitize(source.name) or "untitled"
    filepath = sources_dir / f"{safe_name}.txt"
    filepath.write_text(source.content or "", encoding="utf-8")


def delete_source_file(task_dir: str, source_name: str) -> None:
    """Remove a source file from disk."""
    sources_dir = Path(task_dir, "sources")
    safe_name = _sanitize(source_name) or "untitled"
    filepath = sources_dir / f"{safe_name}.txt"
    filepath.unlink(missing_ok=True)


def sync_characters_to_file(task_dir: str, characters: list) -> None:
    """Write all characters to a single JSON file."""
    data = []
    for c in characters:
        data.append({
            "name": c.name,
            "role": c.role,
            "appearance": c.appearance,
            "personality": c.personality,
            "backstory": c.backstory,
            "relationships": c.relationships,
        })
    filepath = Path(task_dir, "characters.json")
    filepath.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def sync_task_meta(task_dir: str, task) -> None:
    """Write task metadata to task.json."""
    data = {
        "id": task.id,
        "title": task.title,
        "type": task.type,
        "description": task.description or "",
        "status": task.status,
    }
    filepath = Path(task_dir, "task.json")
    filepath.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def sync_note_to_file(task_dir: str, note) -> None:
    """Write a note file to disk."""
    notes_dir = Path(task_dir, "notes")
    notes_dir.mkdir(exist_ok=True)
    safe_name = _sanitize(note.title) or "untitled"
    filepath = notes_dir / f"{safe_name}.md"
    filepath.write_text(note.content or "", encoding="utf-8")


def delete_note_file(task_dir: str, note_title: str) -> None:
    """Remove a note file from disk."""
    notes_dir = Path(task_dir, "notes")
    safe_name = _sanitize(note_title) or "untitled"
    filepath = notes_dir / f"{safe_name}.md"
    filepath.unlink(missing_ok=True)
