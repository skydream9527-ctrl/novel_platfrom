import client from "./client";

export interface TimelineEvent {
  id: number;
  task_id: number;
  chapter_id: number | null;
  title: string;
  description: string;
  event_type: string;
  story_date: string;
  story_date_order: number;
  duration: string;
  location: string;
  is_milestone: boolean;
  created_at: string;
  updated_at: string;
  chapter: {
    id: number;
    title: string;
    order_index: number;
  } | null;
  characters: Array<{
    id: number;
    name: string;
  }>;
}

export interface TimelineConflict {
  type: string;
  event1: {
    id: number;
    title: string;
    location: string;
  };
  event2: {
    id: number;
    title: string;
    location: string;
  };
  characters: string[];
  description: string;
}

export async function getTimeline(taskId: number): Promise<TimelineEvent[]> {
  const response = await client.get(`/timeline/by-task/${taskId}`);
  return response.data;
}

export async function createTimelineEvent(data: {
  task_id: number;
  chapter_id?: number;
  title: string;
  description?: string;
  event_type?: string;
  story_date?: string;
  story_date_order?: number;
  duration?: string;
  location?: string;
  characters?: number[];
  is_milestone?: boolean;
}): Promise<TimelineEvent> {
  const response = await client.post("/timeline/events", data);
  return response.data;
}

export async function updateTimelineEvent(
  eventId: number,
  data: {
    chapter_id?: number;
    title?: string;
    description?: string;
    event_type?: string;
    story_date?: string;
    story_date_order?: number;
    duration?: string;
    location?: string;
    characters?: number[];
    is_milestone?: boolean;
  }
): Promise<void> {
  await client.patch(`/timeline/events/${eventId}`, data);
}

export async function deleteTimelineEvent(eventId: number): Promise<void> {
  await client.delete(`/timeline/events/${eventId}`);
}

export async function moveTimelineEvent(
  eventId: number,
  newStoryDateOrder: number
): Promise<void> {
  await client.patch(`/timeline/events/${eventId}/move`, {
    new_story_date_order: newStoryDateOrder,
  });
}

export async function generateFromChapters(taskId: number): Promise<{ created: number }> {
  const response = await client.post(`/timeline/from-chapters`, null, {
    params: { task_id: taskId },
  });
  return response.data;
}

export async function checkConflicts(
  taskId: number
): Promise<{ conflicts: TimelineConflict[]; total: number }> {
  const response = await client.get(`/timeline/conflicts`, {
    params: { task_id: taskId },
  });
  return response.data;
}
