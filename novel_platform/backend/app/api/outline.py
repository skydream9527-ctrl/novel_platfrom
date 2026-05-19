import json
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.database import get_db
from ..core.deps import get_current_user
from ..models.models import OutlineNode, Task, Chapter

router = APIRouter(prefix="/outline", tags=["outline"])


class OutlineNodeCreate(BaseModel):
    task_id: int
    parent_id: int | None = None
    title: str
    summary: str = ""
    node_type: str = "node"  # root / act / chapter / scene / node


class OutlineNodeUpdate(BaseModel):
    title: str | None = None
    summary: str | None = None
    node_type: str | None = None
    is_collapsed: bool | None = None


class OutlineNodeMove(BaseModel):
    new_parent_id: int | None = None
    new_sort_order: int = 0


class LinkChapterRequest(BaseModel):
    chapter_id: int


def build_tree(nodes: list, parent_id: int | None = None) -> list:
    """递归构建树形结构"""
    tree = []
    for node in nodes:
        if node.parent_id == parent_id:
            children = build_tree(nodes, node.id)
            tree.append({
                "id": node.id,
                "task_id": node.task_id,
                "parent_id": node.parent_id,
                "chapter_id": node.chapter_id,
                "title": node.title,
                "summary": node.summary,
                "node_type": node.node_type,
                "sort_order": node.sort_order,
                "is_collapsed": node.is_collapsed,
                "created_at": node.created_at.isoformat(),
                "updated_at": node.updated_at.isoformat(),
                "children": children,
            })
    # 按 sort_order 排序
    tree.sort(key=lambda x: x["sort_order"])
    return tree


@router.get("/by-task/{task_id}")
async def get_outline(task_id: int, user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """获取完整大纲树"""
    # 验证任务所有权
    task_result = await db.execute(
        select(Task).where(Task.id == task_id, Task.owner_id == user.id)
    )
    if not task_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Task not found")

    result = await db.execute(
        select(OutlineNode).where(OutlineNode.task_id == task_id)
    )
    nodes = result.scalars().all()

    tree = build_tree(nodes)
    return tree


@router.post("/nodes")
async def create_node(req: OutlineNodeCreate, user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """创建大纲节点"""
    # 验证任务所有权
    task_result = await db.execute(
        select(Task).where(Task.id == req.task_id, Task.owner_id == user.id)
    )
    if not task_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Task not found")

    # 如果有父节点，验证父节点存在
    if req.parent_id:
        parent_result = await db.execute(
            select(OutlineNode).where(OutlineNode.id == req.parent_id)
        )
        if not parent_result.scalar_one_or_none():
            raise HTTPException(status_code=404, detail="Parent node not found")

    # 获取同级节点的最大排序值
    result = await db.execute(
        select(OutlineNode.sort_order).where(
            and_(
                OutlineNode.task_id == req.task_id,
                OutlineNode.parent_id == req.parent_id
            )
        ).order_by(OutlineNode.sort_order.desc())
    )
    max_order = result.scalar()
    next_order = (max_order + 1) if max_order is not None else 0

    node = OutlineNode(
        task_id=req.task_id,
        parent_id=req.parent_id,
        title=req.title,
        summary=req.summary,
        node_type=req.node_type,
        sort_order=next_order,
    )
    db.add(node)
    await db.commit()
    await db.refresh(node)

    return {
        "id": node.id,
        "title": node.title,
        "node_type": node.node_type,
        "sort_order": node.sort_order,
    }


@router.patch("/nodes/{node_id}")
async def update_node(node_id: int, req: OutlineNodeUpdate, user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """更新大纲节点"""
    result = await db.execute(select(OutlineNode).where(OutlineNode.id == node_id))
    node = result.scalar_one_or_none()
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")

    if req.title is not None:
        node.title = req.title
    if req.summary is not None:
        node.summary = req.summary
    if req.node_type is not None:
        node.node_type = req.node_type
    if req.is_collapsed is not None:
        node.is_collapsed = req.is_collapsed

    await db.commit()

    return {"ok": True}


@router.delete("/nodes/{node_id}")
async def delete_node(node_id: int, user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """删除大纲节点"""
    result = await db.execute(select(OutlineNode).where(OutlineNode.id == node_id))
    node = result.scalar_one_or_none()
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")

    # 递归删除子节点
    async def delete_children(parent_id: int):
        children_result = await db.execute(
            select(OutlineNode).where(OutlineNode.parent_id == parent_id)
        )
        children = children_result.scalars().all()
        for child in children:
            await delete_children(child.id)
            await db.delete(child)

    await delete_children(node_id)
    await db.delete(node)
    await db.commit()

    return {"ok": True}


@router.patch("/nodes/{node_id}/move")
async def move_node(node_id: int, req: OutlineNodeMove, user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """移动大纲节点"""
    result = await db.execute(select(OutlineNode).where(OutlineNode.id == node_id))
    node = result.scalar_one_or_none()
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")

    # 验证新父节点存在（如果不是根节点）
    if req.new_parent_id:
        parent_result = await db.execute(
            select(OutlineNode).where(OutlineNode.id == req.new_parent_id)
        )
        if not parent_result.scalar_one_or_none():
            raise HTTPException(status_code=404, detail="New parent node not found")

    node.parent_id = req.new_parent_id
    node.sort_order = req.new_sort_order

    await db.commit()

    return {"ok": True}


@router.post("/nodes/{node_id}/link-chapter")
async def link_chapter(node_id: int, req: LinkChapterRequest, user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """关联章节到大纲节点"""
    result = await db.execute(select(OutlineNode).where(OutlineNode.id == node_id))
    node = result.scalar_one_or_none()
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")

    # 验证章节存在
    chapter_result = await db.execute(select(Chapter).where(Chapter.id == req.chapter_id))
    chapter = chapter_result.scalar_one_or_none()
    if not chapter:
        raise HTTPException(status_code=404, detail="Chapter not found")

    node.chapter_id = req.chapter_id
    await db.commit()

    return {"ok": True}


@router.delete("/nodes/{node_id}/unlink-chapter")
async def unlink_chapter(node_id: int, user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """取消关联章节"""
    result = await db.execute(select(OutlineNode).where(OutlineNode.id == node_id))
    node = result.scalar_one_or_none()
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")

    node.chapter_id = None
    await db.commit()

    return {"ok": True}


class BulkCreateRequest(BaseModel):
    task_id: int
    nodes: list[dict]  # [{"title": "...", "node_type": "...", "children": [...]}]


@router.post("/from-template")
async def create_from_template(req: BulkCreateRequest, user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """从模板批量创建大纲节点"""
    # 验证任务所有权
    task_result = await db.execute(
        select(Task).where(Task.id == req.task_id, Task.owner_id == user.id)
    )
    if not task_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Task not found")

    async def create_node_recursive(node_data: dict, parent_id: int | None = None, sort_order: int = 0):
        node = OutlineNode(
            task_id=req.task_id,
            parent_id=parent_id,
            title=node_data.get("title", "未命名"),
            summary=node_data.get("summary", ""),
            node_type=node_data.get("node_type", "node"),
            sort_order=sort_order,
        )
        db.add(node)
        await db.flush()

        # 递归创建子节点
        for i, child_data in enumerate(node_data.get("children", [])):
            await create_node_recursive(child_data, node.id, i)

        return node

    for i, node_data in enumerate(req.nodes):
        await create_node_recursive(node_data, None, i)

    await db.commit()

    return {"ok": True}
