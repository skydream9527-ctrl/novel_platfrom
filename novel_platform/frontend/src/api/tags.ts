import client from "./client";

export interface Tag {
  id: number;
  task_id: number;
  name: string;
  color: string | null;
  usage_count: number;
  created_at: string;
}

export interface ContentTag {
  content_type: string;
  content_id: number;
  title: string;
  word_count: number;
  created_at: string;
}

export async function getTagsByTask(taskId: number): Promise<Tag[]> {
  const response = await client.get(`/tags/by-task/${taskId}`);
  return response.data;
}

export async function createTag(data: {
  task_id: number;
  name: string;
  color?: string;
}): Promise<Tag> {
  const response = await client.post("/tags", data);
  return response.data;
}

export async function updateTag(
  tagId: number,
  data: { name?: string; color?: string }
): Promise<void> {
  await client.patch(`/tags/${tagId}`, data);
}

export async function deleteTag(tagId: number): Promise<void> {
  await client.delete(`/tags/${tagId}`);
}

export async function assignTag(data: {
  tag_id: number;
  content_type: string;
  content_id: number;
}): Promise<void> {
  await client.post("/tags/assign", data);
}

export async function unassignTag(data: {
  tag_id: number;
  content_type: string;
  content_id: number;
}): Promise<void> {
  await client.delete("/tags/unassign", { data });
}

export async function getTagContent(
  tagId: number,
  contentType?: string
): Promise<{
  tag: Tag;
  content: ContentTag[];
  total: number;
}> {
  const response = await client.get(`/tags/${tagId}/content`, {
    params: { content_type: contentType },
  });
  return response.data;
}

export async function getContentTags(
  contentType: string,
  contentId: number
): Promise<Tag[]> {
  const response = await client.get(`/tags/by-content/${contentType}/${contentId}`);
  return response.data;
}

export async function batchAssignTags(
  assignments: Array<{
    tag_id: number;
    content_type: string;
    content_id: number;
  }>
): Promise<{ assigned: number }> {
  const response = await client.post("/tags/batch-assign", assignments);
  return response.data;
}
