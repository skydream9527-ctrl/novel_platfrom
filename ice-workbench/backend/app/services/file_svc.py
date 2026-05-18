"""File service. Files are filesystem-first; index in cache."""
from __future__ import annotations

import hashlib
import shutil
import uuid
from datetime import datetime, timezone
from pathlib import Path

from ..core.errors import APIError, ErrorCode
from ..core.storage import get_index_db, get_paths, read_json, write_json

MAX_SIZE_HARD_CAP_MB = 50
MAX_SIZE_DEFAULT_MB = 20

TEXT_EXTS = {".md", ".txt", ".csv", ".sql", ".py", ".json", ".tsv", ".log", ".yml", ".yaml"}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _detect_format(name: str) -> str:
    ext = Path(name).suffix.lower().lstrip(".")
    return ext or "bin"


def _detect_type(fmt: str) -> str:
    if fmt in {"md", "txt", "log"}:
        return "text"
    if fmt in {"csv", "tsv", "json"}:
        return "data"
    if fmt in {"sql"}:
        return "sql"
    if fmt in {"py", "ts", "js"}:
        return "code"
    if fmt in {"png", "jpg", "jpeg", "gif", "webp"}:
        return "image"
    if fmt in {"pdf"}:
        return "pdf"
    return "binary"


async def upload_task_file(
    *, task_id: str, owner_id: str, filename: str, data: bytes, scope: str = "uploaded"
) -> dict:
    if len(data) > MAX_SIZE_HARD_CAP_MB * 1024 * 1024:
        raise APIError(
            413,
            ErrorCode.FILE_TOO_LARGE,
            f"文件超过 {MAX_SIZE_HARD_CAP_MB}MB 上限，无法上传",
        )
    paths = get_paths()
    target_dir = (
        paths.task_files_input(task_id)
        if scope == "input"
        else paths.task_files_output(task_id)
        if scope == "output"
        else paths.task_files_uploaded(task_id)
    )
    target_dir.mkdir(parents=True, exist_ok=True)
    fid = uuid.uuid4().hex
    safe_name = filename.replace("/", "_").replace("\\", "_")
    target = target_dir / f"{fid}__{safe_name}"
    target.write_bytes(data)

    meta_dir = paths.task_files_meta(task_id)
    meta_dir.mkdir(parents=True, exist_ok=True)
    fmt = _detect_format(safe_name)
    meta = {
        "id": fid,
        "task_id": task_id,
        "owner_id": owner_id,
        "name": safe_name,
        "scope": scope,
        "path": str(target.relative_to(paths.root)),
        "file_type": _detect_type(fmt),
        "format": fmt,
        "size_bytes": len(data),
        "is_pinned": False,
        "sha1": hashlib.sha1(data).hexdigest(),
        "created_at": _now(),
    }
    write_json(meta_dir / f"{fid}.json", meta)
    db = get_index_db()
    await db.upsert("files_index", {k: v for k, v in meta.items() if k in {
        "id", "task_id", "owner_id", "scope", "name", "path", "file_type",
        "format", "size_bytes", "is_pinned", "created_at",
    }} | {"is_pinned": 0})
    return meta


async def list_task_files(task_id: str) -> list[dict]:
    paths = get_paths()
    items: list[dict] = []
    meta_dir = paths.task_files_meta(task_id)
    if meta_dir.exists():
        for p in sorted(meta_dir.glob("*.json")):
            m = read_json(p)
            if not m:
                continue
            # Ensure `scope` is present for input/output/uploaded items.
            if "scope" not in m:
                m["scope"] = "uploaded"
            items.append(m)

    imported_dir = paths.task_files_imported(task_id)
    if imported_dir.exists():
        imp_meta_dir = imported_dir / ".meta"
        if imp_meta_dir.exists():
            for mf in sorted(imp_meta_dir.glob("*.json")):
                m = read_json(mf)
                if not m:
                    continue
                body_path = imported_dir / f"{m['file_id']}.md"
                items.append({
                    "file_id": m["file_id"],
                    "filename": m.get("filename"),
                    "size": m.get(
                        "size",
                        body_path.stat().st_size if body_path.exists() else 0,
                    ),
                    "scope": "imported",
                    "source_type": m.get("source_type"),
                    "source_url": m.get("source_url"),
                    "imported_at": m.get("imported_at"),
                    "imported_by": m.get("imported_by"),
                    "last_refreshed_at": m.get("last_refreshed_at"),
                })

    items.sort(
        key=lambda x: x.get("created_at") or x.get("imported_at") or "",
        reverse=True,
    )
    return items


async def list_public_files() -> list[dict]:
    paths = get_paths()
    out: list[dict] = []
    if not paths.files.exists():
        return out
    for p in sorted(paths.files.iterdir()):
        if p.is_dir() or p.name.startswith("."):
            continue
        try:
            stat = p.stat()
        except OSError:
            continue
        fmt = _detect_format(p.name)
        out.append(
            {
                "id": hashlib.md5(str(p).encode()).hexdigest(),
                "name": p.name,
                "scope": "public",
                "task_id": None,
                "path": str(p.relative_to(paths.root)),
                "file_type": _detect_type(fmt),
                "format": fmt,
                "size_bytes": stat.st_size,
                "is_pinned": p.name.startswith("使用指南"),
                "created_at": datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat(),
            }
        )
    return out


async def read_file_text(task_id: str | None, file_id: str, *, owner_id: str | None = None) -> dict:
    paths = get_paths()
    if task_id:
        meta_path = paths.task_files_meta(task_id) / f"{file_id}.json"
        meta = read_json(meta_path)
        if not meta:
            raise APIError(404, ErrorCode.RESOURCE_NOT_FOUND, "文件不存在")
        rel = paths.root / meta["path"]
        if not rel.exists():
            raise APIError(404, ErrorCode.RESOURCE_NOT_FOUND, "文件已被删除")
        if Path(meta["name"]).suffix.lower() in TEXT_EXTS:
            return {"meta": meta, "content": rel.read_text(encoding="utf-8", errors="replace")}
        return {"meta": meta, "content": None, "binary": True}
    raise APIError(400, ErrorCode.VALIDATION_ERROR, "需要 task_id")


# ---- public files (admin only writes; users read) ----


def _public_meta_dir() -> Path:
    p = get_paths().files / ".meta"
    p.mkdir(parents=True, exist_ok=True)
    return p


def _public_meta_path(file_id: str) -> Path:
    return _public_meta_dir() / f"{file_id}.json"


async def upload_public_file(*, filename: str, data: bytes, is_pinned: bool = False) -> dict:
    if len(data) > MAX_SIZE_HARD_CAP_MB * 1024 * 1024:
        raise APIError(
            413, ErrorCode.FILE_TOO_LARGE, f"文件超过 {MAX_SIZE_HARD_CAP_MB}MB 上限"
        )
    paths = get_paths()
    safe_name = filename.replace("/", "_").replace("\\", "_")
    target = paths.files / safe_name
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        raise APIError(409, "FILE_EXISTS", f"已存在同名文件：{safe_name}")
    target.write_bytes(data)
    fid = hashlib.md5(str(target).encode()).hexdigest()
    fmt = _detect_format(safe_name)
    meta = {
        "id": fid,
        "name": safe_name,
        "scope": "public",
        "task_id": None,
        "path": str(target.relative_to(paths.root)),
        "file_type": _detect_type(fmt),
        "format": fmt,
        "size_bytes": len(data),
        "is_pinned": bool(is_pinned),
        "created_at": _now(),
        "updated_at": _now(),
    }
    write_json(_public_meta_path(fid), meta)
    return meta


async def update_public_file(file_id: str, *, content: str | None = None, is_pinned: bool | None = None) -> dict:
    paths = get_paths()
    meta_path = _public_meta_path(file_id)
    meta = read_json(meta_path)
    if not meta:
        # legacy public file with no meta — synthesize from disk by scanning
        for m in await list_public_files():
            if m["id"] == file_id:
                meta = {**m, "updated_at": _now()}
                break
    if not meta:
        raise APIError(404, ErrorCode.RESOURCE_NOT_FOUND, "文件不存在")
    target = paths.root / meta["path"]
    if content is not None:
        if Path(meta["name"]).suffix.lower() not in TEXT_EXTS:
            raise APIError(400, ErrorCode.VALIDATION_ERROR, "仅文本类文件可编辑")
        target.write_text(content, encoding="utf-8")
        meta["size_bytes"] = len(content.encode("utf-8"))
    if is_pinned is not None:
        meta["is_pinned"] = bool(is_pinned)
    meta["updated_at"] = _now()
    write_json(meta_path, meta)
    return meta


async def delete_public_file(file_id: str) -> None:
    paths = get_paths()
    meta_path = _public_meta_path(file_id)
    meta = read_json(meta_path)
    if not meta:
        for m in await list_public_files():
            if m["id"] == file_id:
                meta = m
                break
    if not meta:
        raise APIError(404, ErrorCode.RESOURCE_NOT_FOUND, "文件不存在")
    if meta.get("is_pinned"):
        raise APIError(400, "FILE_PINNED", "已置顶文件不能删除（先取消置顶）")
    target = paths.root / meta["path"]
    try:
        target.unlink()
    except OSError:
        pass
    try:
        meta_path.unlink()
    except OSError:
        pass


async def read_public_file(file_id: str) -> dict:
    paths = get_paths()
    meta = read_json(_public_meta_path(file_id))
    if not meta:
        for m in await list_public_files():
            if m["id"] == file_id:
                meta = m
                break
    if not meta:
        raise APIError(404, ErrorCode.RESOURCE_NOT_FOUND, "文件不存在")
    target = paths.root / meta["path"]
    if not target.exists():
        raise APIError(404, ErrorCode.RESOURCE_NOT_FOUND, "文件已被删除")
    if Path(meta["name"]).suffix.lower() in TEXT_EXTS:
        return {"meta": meta, "content": target.read_text(encoding="utf-8", errors="replace")}
    return {"meta": meta, "content": None, "binary": True}


async def delete_task_file(task_id: str, file_id: str) -> None:
    paths = get_paths()
    meta_path = paths.task_files_meta(task_id) / f"{file_id}.json"
    meta = read_json(meta_path)
    if not meta:
        raise APIError(404, ErrorCode.RESOURCE_NOT_FOUND, "文件不存在")
    target = paths.root / meta["path"]
    try:
        target.unlink()
    except OSError:
        pass
    try:
        meta_path.unlink()
    except OSError:
        pass
    db = get_index_db()
    await db.execute("DELETE FROM files_index WHERE id = ?", [file_id])


async def import_external(
    *,
    task_id: str,
    user_id: str,
    source_type: str,
    source_url: str,
    source_ref: dict | None,
) -> dict:
    """Spec 4.7. Import external content into tasks/{tid}/files/imported/."""
    paths = get_paths()

    # Dedup: scan existing imported meta
    imp_meta_dir = paths.task_files_imported(task_id) / ".meta"
    imp_meta_dir.mkdir(parents=True, exist_ok=True)
    for mf in imp_meta_dir.glob("*.json"):
        m = read_json(mf)
        if m and m.get("source_url") == source_url:
            raise APIError(
                409, ErrorCode.IMPORT_DUPLICATE,
                f"该链接已导入，file_id={m.get('file_id')}",
                detail={"file_id": m.get("file_id")},
            )

    # Fetch
    if source_type == "feishu_doc":
        from . import feishu_import_svc
        ref = source_ref or feishu_import_svc.parse_feishu_url(source_url)
        title, body = await feishu_import_svc.fetch_document(**ref)
    elif source_type == "kb_article":
        from . import kb_svc
        if not source_ref or "kb_id" not in source_ref or "article_id" not in source_ref:
            raise APIError(400, ErrorCode.VALIDATION_ERROR, "source_ref 缺 kb_id/article_id")
        article = await kb_svc.get_article(source_ref["kb_id"], source_ref["article_id"])
        title, body = article.get("title") or "KB 文章", article.get("body") or ""
        ref = source_ref
    else:
        raise APIError(400, ErrorCode.IMPORT_SOURCE_NOT_SUPPORTED, f"不支持的 source_type: {source_type}")

    # Size cap
    data = body.encode("utf-8")
    if len(data) > MAX_SIZE_HARD_CAP_MB * 1024 * 1024:
        raise APIError(413, ErrorCode.FILE_TOO_LARGE, "文件超出大小限制")

    # Write file + meta
    file_id = str(uuid.uuid4().hex)
    safe_title = (title or "imported").replace("/", "_")[:100]
    filename = f"{safe_title}.md"
    fpath = paths.task_files_imported(task_id) / f"{file_id}.md"
    fpath.parent.mkdir(parents=True, exist_ok=True)
    fpath.write_bytes(data)
    meta = {
        "file_id": file_id,
        "filename": filename,
        "source_type": source_type,
        "source_url": source_url,
        "source_ref": ref,
        "imported_at": _now(),
        "imported_by": user_id,
        "last_refreshed_at": None,
        "last_refreshed_by": None,
        "fetch_error": None,
        "size": len(data),
    }
    write_json(paths.task_files_imported_meta(task_id, file_id), meta)

    # Update task meta counter
    task_meta_path = paths.task_meta(task_id)
    tmeta = read_json(task_meta_path) or {}
    tmeta["imported_file_count"] = int(tmeta.get("imported_file_count", 0)) + 1
    tmeta["updated_at"] = _now()
    write_json(task_meta_path, tmeta)

    return {**meta, "scope": "imported"}


async def refresh_imported(
    *, task_id: str, file_id: str, user_id: str, is_owner: bool, is_admin: bool,
) -> dict:
    paths = get_paths()
    meta_path = paths.task_files_imported_meta(task_id, file_id)
    meta = read_json(meta_path)
    if not meta:
        raise APIError(404, ErrorCode.RESOURCE_NOT_FOUND, "导入文件不存在")
    if not (is_owner or is_admin or meta.get("imported_by") == user_id):
        raise APIError(403, ErrorCode.FILE_REFRESH_FORBIDDEN, "无权刷新该文件")

    source_type = meta["source_type"]
    source_ref = meta.get("source_ref") or {}
    try:
        if source_type == "feishu_doc":
            from . import feishu_import_svc
            _, body = await feishu_import_svc.fetch_document(**source_ref)
        elif source_type == "kb_article":
            from . import kb_svc
            art = await kb_svc.get_article(source_ref["kb_id"], source_ref["article_id"])
            body = art.get("body") or ""
        else:
            raise APIError(400, ErrorCode.IMPORT_SOURCE_NOT_SUPPORTED, source_type)
    except APIError:
        raise
    except Exception as e:  # network / unknown
        meta["fetch_error"] = str(e)[:500]
        write_json(meta_path, meta)
        raise APIError(502, ErrorCode.IMPORT_FETCH_FAILED, f"刷新失败: {e}")

    fpath = paths.task_files_imported(task_id) / f"{file_id}.md"
    new_bytes = body.encode("utf-8")
    changed = (not fpath.exists()) or fpath.read_bytes() != new_bytes
    if changed:
        fpath.write_bytes(new_bytes)
    meta["last_refreshed_at"] = _now()
    meta["last_refreshed_by"] = user_id
    meta["fetch_error"] = None
    meta["size"] = len(new_bytes)
    write_json(meta_path, meta)

    if changed:
        try:
            from . import admin_svc
            await admin_svc.audit(
                admin_id=user_id,
                action="refresh_imported_file",
                target_type="task",
                target_id=task_id,
                diff={"file_id": file_id, "size": len(new_bytes)},
            )
        except Exception:
            pass  # audit must never block business path

    return {"changed": changed, "size": len(new_bytes), "last_refreshed_at": meta["last_refreshed_at"]}
