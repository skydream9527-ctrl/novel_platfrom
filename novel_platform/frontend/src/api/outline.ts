import client from "./client";

export interface OutlineNode {
  id: number;
  task_id: number;
  parent_id: number | null;
  chapter_id: number | null;
  title: string;
  summary: string;
  node_type: string;
  sort_order: number;
  is_collapsed: boolean;
  created_at: string;
  updated_at: string;
  children: OutlineNode[];
}

export async function getOutline(taskId: number): Promise<OutlineNode[]> {
  const response = await client.get(`/outline/by-task/${taskId}`);
  return response.data;
}

export async function createOutlineNode(data: {
  task_id: number;
  parent_id?: number;
  title: string;
  summary?: string;
  node_type?: string;
}): Promise<OutlineNode> {
  const response = await client.post("/outline/nodes", data);
  return response.data;
}

export async function updateOutlineNode(
  nodeId: number,
  data: {
    title?: string;
    summary?: string;
    node_type?: string;
    is_collapsed?: boolean;
  }
): Promise<void> {
  await client.patch(`/outline/nodes/${nodeId}`, data);
}

export async function deleteOutlineNode(nodeId: number): Promise<void> {
  await client.delete(`/outline/nodes/${nodeId}`);
}

export async function moveOutlineNode(
  nodeId: number,
  newParentId: number | null,
  newSortOrder: number
): Promise<void> {
  await client.patch(`/outline/nodes/${nodeId}/move`, {
    new_parent_id: newParentId,
    new_sort_order: newSortOrder,
  });
}

export async function linkChapter(
  nodeId: number,
  chapterId: number
): Promise<void> {
  await client.post(`/outline/nodes/${nodeId}/link-chapter`, {
    chapter_id: chapterId,
  });
}

export async function unlinkChapter(nodeId: number): Promise<void> {
  await client.delete(`/outline/nodes/${nodeId}/unlink-chapter`);
}

export async function createFromTemplate(
  taskId: number,
  nodes: Array<{
    title: string;
    node_type?: string;
    summary?: string;
    children?: any[];
  }>
): Promise<void> {
  await client.post("/outline/from-template", {
    task_id: taskId,
    nodes,
  });
}
