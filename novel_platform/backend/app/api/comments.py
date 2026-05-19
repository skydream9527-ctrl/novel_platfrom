from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.database import get_db
from ..core.deps import get_current_user
from ..models.models import Comment, Task, Chapter, User

router = APIRouter(prefix="/comments", tags=["comments"])


class CommentCreate(BaseModel):
    task_id: int
    chapter_id: int
    parent_id: int | None = None
    content: str
    comment_type: str = "general"  # general / suggestion / issue / praise / ai
    selection_start: int | None = None
    selection_end: int | None = None
    selected_text: str | None = None


class CommentUpdate(BaseModel):
    content: str | None = None
    comment_type: str | None = None
    status: str | None = None


@router.get("/by-chapter/{chapter_id}")
async def get_chapter_comments(
    chapter_id: int,
    status: str | None = Query(None, description="按状态筛选"),
    comment_type: str | None = Query(None, description="按类型筛选"),
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取章节的所有评论"""
    query = select(Comment).where(Comment.chapter_id == chapter_id)

    if status:
        query = query.where(Comment.status == status)
    if comment_type:
        query = query.where(Comment.comment_type == comment_type)

    query = query.order_by(Comment.created_at)

    result = await db.execute(query)
    comments = result.scalars().all()

    # 构建评论树
    comments_data = []
    for comment in comments:
        # 获取作者信息
        author_result = await db.execute(select(User).where(User.id == comment.author_id))
        author = author_result.scalar_one_or_none()

        # 获取回复
        replies_result = await db.execute(
            select(Comment)
            .where(Comment.parent_id == comment.id)
            .order_by(Comment.created_at)
        )
        replies = replies_result.scalars().all()

        replies_data = []
        for reply in replies:
            reply_author_result = await db.execute(select(User).where(User.id == reply.author_id))
            reply_author = reply_author_result.scalar_one_or_none()
            replies_data.append({
                "id": reply.id,
                "content": reply.content,
                "comment_type": reply.comment_type,
                "status": reply.status,
                "author": {
                    "id": reply_author.id,
                    "name": reply_author.name,
                } if reply_author else None,
                "created_at": reply.created_at.isoformat(),
                "updated_at": reply.updated_at.isoformat(),
            })

        comments_data.append({
            "id": comment.id,
            "chapter_id": comment.chapter_id,
            "content": comment.content,
            "comment_type": comment.comment_type,
            "status": comment.status,
            "selection_start": comment.selection_start,
            "selection_end": comment.selection_end,
            "selected_text": comment.selected_text,
            "author": {
                "id": author.id,
                "name": author.name,
            } if author else None,
            "replies": replies_data,
            "created_at": comment.created_at.isoformat(),
            "updated_at": comment.updated_at.isoformat(),
        })

    return comments_data


@router.post("/")
async def create_comment(req: CommentCreate, user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """创建评论"""
    # 验证任务所有权
    task_result = await db.execute(
        select(Task).where(Task.id == req.task_id, Task.owner_id == user.id)
    )
    if not task_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Task not found")

    # 验证章节存在
    chapter_result = await db.execute(select(Chapter).where(Chapter.id == req.chapter_id))
    if not chapter_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Chapter not found")

    comment = Comment(
        task_id=req.task_id,
        chapter_id=req.chapter_id,
        parent_id=req.parent_id,
        author_id=user.id,
        content=req.content,
        comment_type=req.comment_type,
        selection_start=req.selection_start,
        selection_end=req.selection_end,
        selected_text=req.selected_text,
    )
    db.add(comment)
    await db.commit()
    await db.refresh(comment)

    return {
        "id": comment.id,
        "content": comment.content,
        "comment_type": comment.comment_type,
    }


@router.patch("/{comment_id}")
async def update_comment(comment_id: int, req: CommentUpdate, user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """更新评论"""
    result = await db.execute(select(Comment).where(Comment.id == comment_id))
    comment = result.scalar_one_or_none()
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")

    if req.content is not None:
        comment.content = req.content
    if req.comment_type is not None:
        comment.comment_type = req.comment_type
    if req.status is not None:
        comment.status = req.status

    await db.commit()

    return {"ok": True}


@router.delete("/{comment_id}")
async def delete_comment(comment_id: int, user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """删除评论"""
    result = await db.execute(select(Comment).where(Comment.id == comment_id))
    comment = result.scalar_one_or_none()
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")

    await db.delete(comment)
    await db.commit()

    return {"ok": True}


@router.post("/{comment_id}/resolve")
async def resolve_comment(comment_id: int, user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """标记评论为已解决"""
    result = await db.execute(select(Comment).where(Comment.id == comment_id))
    comment = result.scalar_one_or_none()
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")

    comment.status = "resolved"
    await db.commit()

    return {"ok": True}


@router.get("/stats/by-chapter/{chapter_id}")
async def get_comment_stats(chapter_id: int, user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """获取章节评论统计"""
    # 总评论数
    total_result = await db.execute(
        select(func.count(Comment.id)).where(Comment.chapter_id == chapter_id)
    )
    total = total_result.scalar() or 0

    # 未解决数
    open_result = await db.execute(
        select(func.count(Comment.id)).where(
            and_(
                Comment.chapter_id == chapter_id,
                Comment.status == "open"
            )
        )
    )
    open_count = open_result.scalar() or 0

    # 按类型统计
    type_stats_result = await db.execute(
        select(
            Comment.comment_type,
            func.count(Comment.id).label("count")
        ).where(Comment.chapter_id == chapter_id)
        .group_by(Comment.comment_type)
    )
    type_stats = {row.comment_type: row.count for row in type_stats_result.all()}

    return {
        "total": total,
        "open": open_count,
        "resolved": total - open_count,
        "by_type": type_stats,
    }
