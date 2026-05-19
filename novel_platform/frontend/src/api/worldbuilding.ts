import client from "./client";

export interface WorldbuildingCategory {
  id: number;
  task_id: number;
  name: string;
  icon: string;
  description: string;
  sort_order: number;
  entries_count: number;
  created_at: string;
}

export interface WorldbuildingEntry {
  id: number;
  task_id: number;
  category_id: number;
  title: string;
  content: string;
  attributes: Record<string, any>;
  related_entries: number[];
  related_characters: number[];
  category: {
    id: number;
    name: string;
    icon: string;
  } | null;
  created_at: string;
  updated_at: string;
}

export async function getCategories(taskId: number): Promise<WorldbuildingCategory[]> {
  const response = await client.get(`/worldbuilding/categories/by-task/${taskId}`);
  return response.data;
}

export async function createCategory(data: {
  task_id: number;
  name: string;
  icon?: string;
  description?: string;
  sort_order?: number;
}): Promise<WorldbuildingCategory> {
  const response = await client.post("/worldbuilding/categories", data);
  return response.data;
}

export async function updateCategory(
  catId: number,
  data: {
    name?: string;
    icon?: string;
    description?: string;
    sort_order?: number;
  }
): Promise<void> {
  await client.patch(`/worldbuilding/categories/${catId}`, data);
}

export async function deleteCategory(catId: number): Promise<void> {
  await client.delete(`/worldbuilding/categories/${catId}`);
}

export async function createPresetCategories(taskId: number): Promise<{ created: number }> {
  const response = await client.post("/worldbuilding/categories/presets", null, {
    params: { task_id: taskId },
  });
  return response.data;
}

export async function getEntries(
  taskId: number,
  categoryId?: number
): Promise<WorldbuildingEntry[]> {
  const response = await client.get(`/worldbuilding/entries/by-task/${taskId}`, {
    params: { category_id: categoryId },
  });
  return response.data;
}

export async function createEntry(data: {
  task_id: number;
  category_id: number;
  title: string;
  content?: string;
  attributes?: Record<string, any>;
  related_entries?: number[];
  related_characters?: number[];
}): Promise<WorldbuildingEntry> {
  const response = await client.post("/worldbuilding/entries", data);
  return response.data;
}

export async function updateEntry(
  entryId: number,
  data: {
    title?: string;
    content?: string;
    attributes?: Record<string, any>;
    related_entries?: number[];
    related_characters?: number[];
  }
): Promise<void> {
  await client.patch(`/worldbuilding/entries/${entryId}`, data);
}

export async function deleteEntry(entryId: number): Promise<void> {
  await client.delete(`/worldbuilding/entries/${entryId}`);
}

export async function searchEntries(
  taskId: number,
  query: string
): Promise<WorldbuildingEntry[]> {
  const response = await client.get("/worldbuilding/search", {
    params: { task_id: taskId, q: query },
  });
  return response.data;
}
