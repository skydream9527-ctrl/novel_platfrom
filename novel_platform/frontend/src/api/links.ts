import client from "./client";

export interface Link {
  id: number;
  task_id: number;
  source_type: string;
  source_id: number;
  target_type: string;
  target_id: number;
  anchor_text: string | null;
  created_at: string;
}

export interface Backlink {
  link_id: number;
  source_type: string;
  source_id: number;
  source_title: string;
  anchor_text: string | null;
  created_at: string;
}

export interface ParsedLink {
  type: string;
  name: string;
  full_match: string;
  start: number;
  end: number;
  resolved: boolean;
  target: {
    type: string;
    id: number;
  } | null;
}

export interface LinkParseResult {
  links: ParsedLink[];
  total: number;
  resolved: number;
}

export async function getLinksByTask(taskId: number): Promise<Link[]> {
  const response = await client.get(`/links/by-task/${taskId}`);
  return response.data;
}

export async function getBacklinks(
  targetType: string,
  targetId: number,
  taskId: number
): Promise<Backlink[]> {
  const response = await client.get(
    `/links/backlinks/${targetType}/${targetId}`,
    { params: { task_id: taskId } }
  );
  return response.data;
}

export async function parseLinks(
  content: string,
  taskId: number
): Promise<LinkParseResult> {
  const response = await client.post("/links/parse", {
    content,
    task_id: taskId,
  });
  return response.data;
}

export async function createLink(data: {
  task_id: number;
  source_type: string;
  source_id: number;
  target_type: string;
  target_id: number;
  anchor_text?: string;
}): Promise<Link> {
  const response = await client.post("/links", data);
  return response.data;
}

export async function deleteLink(linkId: number): Promise<void> {
  await client.delete(`/links/${linkId}`);
}

export async function batchCreateLinks(
  links: Array<{
    task_id: number;
    source_type: string;
    source_id: number;
    target_type: string;
    target_id: number;
    anchor_text?: string;
  }>
): Promise<{ created: number; links: Link[] }> {
  const response = await client.post("/links/batch", links);
  return response.data;
}
