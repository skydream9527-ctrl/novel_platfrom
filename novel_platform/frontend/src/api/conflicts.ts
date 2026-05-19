import client from "./client";

export interface Conflict {
  id: number;
  task_id: number;
  title: string;
  description: string;
  conflict_type: string;
  status: string;
  priority: string;
  introduced_chapter: {
    id: number;
    title: string;
  } | null;
  resolved_chapter: {
    id: number;
    title: string;
  } | null;
  characters: Array<{
    id: number;
    name: string;
  }>;
  created_at: string;
  updated_at: string;
}

export interface Foreshadowing {
  id: number;
  task_id: number;
  title: string;
  description: string;
  foreshadowing_type: string;
  status: string;
  planted_chapter: {
    id: number;
    title: string;
  } | null;
  revealed_chapter: {
    id: number;
    title: string;
  } | null;
  hints: Array<{
    chapter_id: number;
    description: string;
  }>;
  created_at: string;
  updated_at: string;
}

export interface Annotation {
  id: number;
  chapter_id: number;
  annotation_type: string;
  color: string | null;
  selection_start: number;
  selection_end: number;
  selected_text: string | null;
  note: string | null;
  suggestion: string | null;
  user: {
    id: number;
    name: string;
  } | null;
  created_at: string;
}

// 冲突相关接口
export async function getConflicts(
  taskId: number,
  status?: string,
  conflictType?: string
): Promise<Conflict[]> {
  const response = await client.get(`/conflicts/by-task/${taskId}`, {
    params: { status, conflict_type: conflictType },
  });
  return response.data;
}

export async function createConflict(data: {
  task_id: number;
  title: string;
  description?: string;
  conflict_type?: string;
  priority?: string;
  introduced_chapter_id?: number;
  related_characters?: number[];
}): Promise<Conflict> {
  const response = await client.post("/conflicts", data);
  return response.data;
}

export async function updateConflict(
  conflictId: number,
  data: {
    title?: string;
    description?: string;
    conflict_type?: string;
    status?: string;
    priority?: string;
    introduced_chapter_id?: number;
    resolved_chapter_id?: number;
    related_characters?: number[];
  }
): Promise<void> {
  await client.patch(`/conflicts/${conflictId}`, data);
}

export async function deleteConflict(conflictId: number): Promise<void> {
  await client.delete(`/conflicts/${conflictId}`);
}

export async function getUnresolvedConflicts(taskId: number): Promise<Conflict[]> {
  const response = await client.get("/conflicts/unresolved", {
    params: { task_id: taskId },
  });
  return response.data;
}

// 伏笔相关接口
export async function getForeshadowing(
  taskId: number,
  status?: string
): Promise<Foreshadowing[]> {
  const response = await client.get("/conflicts/foreshadowing/by-task/${taskId}", {
    params: { status },
  });
  return response.data;
}

export async function createForeshadowing(data: {
  task_id: number;
  title: string;
  description?: string;
  foreshadowing_type?: string;
  planted_chapter_id?: number;
  hints?: Array<{ chapter_id: number; description: string }>;
}): Promise<Foreshadowing> {
  const response = await client.post("/conflicts/foreshadowing", data);
  return response.data;
}

export async function updateForeshadowing(
  fsId: number,
  data: {
    title?: string;
    description?: string;
    foreshadowing_type?: string;
    status?: string;
    planted_chapter_id?: number;
    revealed_chapter_id?: number;
    hints?: Array<{ chapter_id: number; description: string }>;
  }
): Promise<void> {
  await client.patch(`/conflicts/foreshadowing/${fsId}`, data);
}

export async function deleteForeshadowing(fsId: number): Promise<void> {
  await client.delete(`/conflicts/foreshadowing/${fsId}`);
}

export async function getUnresolvedForeshadowing(taskId: number): Promise<Foreshadowing[]> {
  const response = await client.get("/conflicts/foreshadowing/unresolved", {
    params: { task_id: taskId },
  });
  return response.data;
}

// 审阅标注相关接口
export async function getAnnotations(chapterId: number): Promise<Annotation[]> {
  const response = await client.get(`/conflicts/annotations/by-chapter/${chapterId}`);
  return response.data;
}

export async function createAnnotation(data: {
  task_id: number;
  chapter_id: number;
  annotation_type: string;
  color?: string;
  selection_start: number;
  selection_end: number;
  selected_text?: string;
  note?: string;
  suggestion?: string;
}): Promise<Annotation> {
  const response = await client.post("/conflicts/annotations", data);
  return response.data;
}

export async function deleteAnnotation(annotationId: number): Promise<void> {
  await client.delete(`/conflicts/annotations/${annotationId}`);
}
