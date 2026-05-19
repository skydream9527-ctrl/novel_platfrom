import client from "./client";

export interface AttributeDefinition {
  id: number;
  task_id: number;
  name: string;
  field_type: string;
  options: string[] | null;
  default_value: string | null;
  sort_order: number;
  created_at: string;
}

export interface AttributeValue {
  id: number;
  definition_id: number;
  chapter_id: number;
  value: string | null;
  definition: {
    name: string;
    field_type: string;
    options: string[] | null;
  };
}

export async function getAttributeDefinitions(
  taskId: number
): Promise<AttributeDefinition[]> {
  const response = await client.get(`/attributes/definitions/by-task/${taskId}`);
  return response.data;
}

export async function createAttributeDefinition(data: {
  task_id: number;
  name: string;
  field_type: string;
  options?: string[];
  default_value?: string;
  sort_order?: number;
}): Promise<AttributeDefinition> {
  const response = await client.post("/attributes/definitions", data);
  return response.data;
}

export async function updateAttributeDefinition(
  defId: number,
  data: {
    name?: string;
    field_type?: string;
    options?: string[];
    default_value?: string;
    sort_order?: number;
  }
): Promise<void> {
  await client.patch(`/attributes/definitions/${defId}`, data);
}

export async function deleteAttributeDefinition(defId: number): Promise<void> {
  await client.delete(`/attributes/definitions/${defId}`);
}

export async function getChapterAttributeValues(
  chapterId: number
): Promise<AttributeValue[]> {
  const response = await client.get(`/attributes/values/by-chapter/${chapterId}`);
  return response.data;
}

export async function batchUpdateAttributeValues(
  values: Array<{
    definition_id: number;
    chapter_id: number;
    value: string | null;
  }>
): Promise<void> {
  await client.put("/attributes/values/batch", { values });
}

export async function filterChaptersByAttribute(
  taskId: number,
  attributeName: string,
  attributeValue: string
): Promise<
  Array<{
    id: number;
    title: string;
    order_index: number;
    status: string;
    word_count: number;
  }>
> {
  const response = await client.get("/attributes/values/filter", {
    params: {
      task_id: taskId,
      attribute_name: attributeName,
      attribute_value: attributeValue,
    },
  });
  return response.data;
}
