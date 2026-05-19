from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.database import get_db
from ..core.deps import get_current_user
from ..models.models import (
    Chapter, Character, Note, Source, Tag, ContentTag, Link, Task
)

router = APIRouter(prefix="/graph", tags=["graph"])


async def build_graph(db: AsyncSession, task_id: int, filter_type: str | None = None):
    """构建完整的知识图谱数据"""
    nodes = []
    edges = []
    node_id_map = {}  # (type, id) -> node_index

    # 1. 添加章节节点
    if not filter_type or filter_type == "chapter":
        result = await db.execute(
            select(Chapter).where(Chapter.task_id == task_id).order_by(Chapter.order_index)
        )
        chapters = result.scalars().all()
        for c in chapters:
            node_id = f"chapter-{c.id}"
            node_id_map[("chapter", c.id)] = len(nodes)
            nodes.append({
                "id": node_id,
                "type": "chapter",
                "label": c.title,
                "data": {
                    "id": c.id,
                    "title": c.title,
                    "status": c.status,
                    "word_count": len(c.content) if c.content else 0,
                    "order_index": c.order_index,
                }
            })

    # 2. 添加角色节点
    if not filter_type or filter_type == "character":
        result = await db.execute(
            select(Character).where(Character.task_id == task_id)
        )
        characters = result.scalars().all()
        for c in characters:
            node_id = f"character-{c.id}"
            node_id_map[("character", c.id)] = len(nodes)
            nodes.append({
                "id": node_id,
                "type": "character",
                "label": c.name,
                "data": {
                    "id": c.id,
                    "name": c.name,
                    "role": c.role,
                    "personality": c.personality,
                }
            })

    # 3. 添加笔记节点
    if not filter_type or filter_type == "note":
        result = await db.execute(
            select(Note).where(Note.task_id == task_id)
        )
        notes = result.scalars().all()
        for n in notes:
            node_id = f"note-{n.id}"
            node_id_map[("note", n.id)] = len(nodes)
            nodes.append({
                "id": node_id,
                "type": "note",
                "label": n.title,
                "data": {
                    "id": n.id,
                    "title": n.title,
                    "category_id": n.category_id,
                }
            })

    # 4. 添加素材节点
    if not filter_type or filter_type == "source":
        result = await db.execute(
            select(Source).where(Source.task_id == task_id)
        )
        sources = result.scalars().all()
        for s in sources:
            node_id = f"source-{s.id}"
            node_id_map[("source", s.id)] = len(nodes)
            nodes.append({
                "id": node_id,
                "type": "source",
                "label": s.name,
                "data": {
                    "id": s.id,
                    "name": s.name,
                    "type": s.type,
                    "word_count": s.word_count,
                }
            })

    # 5. 添加标签节点
    if not filter_type or filter_type == "tag":
        result = await db.execute(
            select(Tag).where(Tag.task_id == task_id)
        )
        tags = result.scalars().all()
        for t in tags:
            node_id = f"tag-{t.id}"
            node_id_map[("tag", t.id)] = len(nodes)
            nodes.append({
                "id": node_id,
                "type": "tag",
                "label": t.name,
                "data": {
                    "id": t.id,
                    "name": t.name,
                    "color": t.color,
                }
            })

    # 6. 构建边 - 双向链接
    result = await db.execute(
        select(Link).where(Link.task_id == task_id)
    )
    links = result.scalars().all()
    for link in links:
        source_key = (link.source_type, link.source_id)
        target_key = (link.target_type, link.target_id)
        if source_key in node_id_map and target_key in node_id_map:
            edges.append({
                "id": f"link-{link.id}",
                "source": f"{link.source_type}-{link.source_id}",
                "target": f"{link.target_type}-{link.target_id}",
                "type": "reference",
                "label": link.anchor_text,
            })

    # 7. 构建边 - 标签关联
    result = await db.execute(
        select(ContentTag).where(ContentTag.content_type.in_(["chapter", "note", "source"]))
    )
    content_tags = result.scalars().all()
    for ct in content_tags:
        tag_key = ("tag", ct.tag_id)
        content_key = (ct.content_type, ct.content_id)
        if tag_key in node_id_map and content_key in node_id_map:
            edges.append({
                "id": f"ctag-{ct.id}",
                "source": f"tag-{ct.tag_id}",
                "target": f"{ct.content_type}-{ct.content_id}",
                "type": "tag",
            })

    # 8. 构建边 - 角色出场（通过内容中提到角色名）
    if not filter_type or filter_type in ["chapter", "character"]:
        result = await db.execute(
            select(Chapter).where(Chapter.task_id == task_id)
        )
        chapters = result.scalars().all()
        result = await db.execute(
            select(Character).where(Character.task_id == task_id)
        )
        characters = result.scalars().all()

        for chapter in chapters:
            if not chapter.content:
                continue
            for char in characters:
                if char.name in chapter.content:
                    source_key = ("chapter", chapter.id)
                    target_key = ("character", char.id)
                    if source_key in node_id_map and target_key in node_id_map:
                        edges.append({
                            "id": f"appear-{chapter.id}-{char.id}",
                            "source": f"chapter-{chapter.id}",
                            "target": f"character-{char.id}",
                            "type": "appearance",
                        })

    return {
        "nodes": nodes,
        "edges": edges,
        "stats": {
            "total_nodes": len(nodes),
            "total_edges": len(edges),
            "chapters": sum(1 for n in nodes if n["type"] == "chapter"),
            "characters": sum(1 for n in nodes if n["type"] == "character"),
            "notes": sum(1 for n in nodes if n["type"] == "note"),
            "sources": sum(1 for n in nodes if n["type"] == "source"),
            "tags": sum(1 for n in nodes if n["type"] == "tag"),
        }
    }


@router.get("/by-task/{task_id}")
async def get_graph(
    task_id: int,
    type: str | None = Query(None, description="按类型筛选节点"),
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取完整的知识图谱数据"""
    # 验证任务所有权
    task_result = await db.execute(
        select(Task).where(Task.id == task_id, Task.owner_id == user.id)
    )
    if not task_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Task not found")

    graph_data = await build_graph(db, task_id, type)
    return graph_data


@router.get("/neighbors/{node_type}/{node_id}")
async def get_neighbors(
    node_type: str,
    node_id: int,
    depth: int = Query(1, ge=1, le=3, description="深度"),
    task_id: int = Query(..., description="任务ID"),
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取邻居节点"""
    # 验证任务所有权
    task_result = await db.execute(
        select(Task).where(Task.id == task_id, Task.owner_id == user.id)
    )
    if not task_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Task not found")

    # 获取完整图数据
    graph_data = await build_graph(db, task_id)

    # 找到目标节点
    target_node_id = f"{node_type}-{node_id}"
    target_node = None
    for node in graph_data["nodes"]:
        if node["id"] == target_node_id:
            target_node = node
            break

    if not target_node:
        raise HTTPException(status_code=404, detail="Node not found")

    # BFS 查找邻居
    visited = set()
    visited.add(target_node_id)
    current_level = [target_node_id]
    all_neighbors = []

    for _ in range(depth):
        next_level = []
        for current_id in current_level:
            # 找到所有与当前节点相连的边
            for edge in graph_data["edges"]:
                neighbor_id = None
                if edge["source"] == current_id and edge["target"] not in visited:
                    neighbor_id = edge["target"]
                elif edge["target"] == current_id and edge["source"] not in visited:
                    neighbor_id = edge["source"]

                if neighbor_id:
                    visited.add(neighbor_id)
                    next_level.append(neighbor_id)
                    # 找到节点数据
                    for node in graph_data["nodes"]:
                        if node["id"] == neighbor_id:
                            all_neighbors.append(node)
                            break
        current_level = next_level

    return {
        "center": target_node,
        "neighbors": all_neighbors,
        "edges": [
            e for e in graph_data["edges"]
            if e["source"] in visited or e["target"] in visited
        ]
    }


@router.get("/path/{from_type}/{from_id}/{to_type}/{to_id}")
async def find_path(
    from_type: str,
    from_id: int,
    to_type: str,
    to_id: int,
    task_id: int = Query(..., description="任务ID"),
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """查找两个节点之间的路径"""
    # 验证任务所有权
    task_result = await db.execute(
        select(Task).where(Task.id == task_id, Task.owner_id == user.id)
    )
    if not task_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Task not found")

    # 获取完整图数据
    graph_data = await build_graph(db, task_id)

    start_id = f"{from_type}-{from_id}"
    end_id = f"{to_type}-{to_id}"

    # BFS 查找最短路径
    from collections import deque

    queue = deque([(start_id, [start_id])])
    visited = {start_id}

    while queue:
        current, path = queue.popleft()

        if current == end_id:
            # 构建路径详情
            path_nodes = []
            for node_id in path:
                for node in graph_data["nodes"]:
                    if node["id"] == node_id:
                        path_nodes.append(node)
                        break

            path_edges = []
            for i in range(len(path) - 1):
                for edge in graph_data["edges"]:
                    if (edge["source"] == path[i] and edge["target"] == path[i + 1]) or \
                       (edge["target"] == path[i] and edge["source"] == path[i + 1]):
                        path_edges.append(edge)
                        break

            return {
                "found": True,
                "path": path_nodes,
                "edges": path_edges,
                "length": len(path) - 1
            }

        # 查找邻居
        for edge in graph_data["edges"]:
            neighbor = None
            if edge["source"] == current:
                neighbor = edge["target"]
            elif edge["target"] == current:
                neighbor = edge["source"]

            if neighbor and neighbor not in visited:
                visited.add(neighbor)
                queue.append((neighbor, path + [neighbor]))

    return {"found": False, "path": [], "edges": [], "length": 0}
