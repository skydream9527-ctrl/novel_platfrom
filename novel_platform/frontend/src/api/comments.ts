import client from "./client";

export interface Comment {
  id: number;
  chapter_id: number;
  content: string;
  comment_type: string;
  status: string;
  selection_start: number | null;
  selection_end: number | null;
  selected_text: string | null;
  author: {
    id: number;
    name: string;
  } | null;
  replies: Comment[];
  created_at: string;
  updated_at: string;
}

export interface CommentStats {
  total: number;
  open: number;
  resolved: number;
  by_type: Record<string, number>;
}

export async function getChapterComments(
  chapterId: number,
  status?: string,
  commentType?: string
): Promise<Comment[]> {
  const response = await client.get(`/comments/by-chapter/${chapterId}`, {
    params: { status, comment_type: commentType },
  });
  return response.data;
}

export async function createComment(data: {
  task_id: number;
  chapter_id: number;
  parent_id?: number;
  content: string;
  comment_type?: string;
  selection_start?: number;
  selection_end?: number;
  selected_text?: string;
}): Promise<Comment> {
  const response = await client.post("/comments", data);
  return response.data;
}

export async function updateComment(
  commentId: number,
  data: {
    content?: string;
    comment_type?: string;
    status?: string;
  }
): Promise<void> {
  await client.patch(`/comments/${commentId}`, data);
}

export async function deleteComment(commentId: number): Promise<void> {
  await client.delete(`/comments/${commentId}`);
}

export async function resolveComment(commentId: number): Promise<void> {
  await client.post(`/comments/${commentId}/resolve`);
}

export async function getCommentStats(chapterId: number): Promise<CommentStats> {
  const response = await client.get(`/comments/stats/by-chapter/${chapterId}`);
  return response.data;
}
