import client from "./client";

export interface WritingGoal {
  id: number;
  task_id: number;
  goal_type: string;
  target_words: number;
  start_date: string | null;
  end_date: string | null;
  created_at: string;
}

export interface WritingStats {
  today_words: number;
  week_words: number;
  total_words: number;
  writing_days: number;
  avg_speed: number;
}

export interface DailyStat {
  date: string;
  words: number;
}

export async function getWritingGoals(taskId: number): Promise<WritingGoal[]> {
  const response = await client.get(`/writing/goals/by-task/${taskId}`);
  return response.data;
}

export async function createWritingGoal(data: {
  task_id: number;
  goal_type: string;
  target_words: number;
  start_date?: string;
  end_date?: string;
}): Promise<WritingGoal> {
  const response = await client.post("/writing/goals", data);
  return response.data;
}

export async function updateWritingGoal(
  goalId: number,
  data: {
    target_words?: number;
    start_date?: string;
    end_date?: string;
  }
): Promise<void> {
  await client.patch(`/writing/goals/${goalId}`, data);
}

export async function deleteWritingGoal(goalId: number): Promise<void> {
  await client.delete(`/writing/goals/${goalId}`);
}

export async function createWritingLog(data: {
  task_id: number;
  chapter_id?: number;
  words_written: number;
  duration_seconds?: number;
}): Promise<void> {
  await client.post("/writing/logs", data);
}

export async function getWritingStats(taskId: number): Promise<WritingStats> {
  const response = await client.get(`/writing/stats/by-task/${taskId}`);
  return response.data;
}

export async function getDailyStats(
  taskId: number,
  days: number = 30
): Promise<DailyStat[]> {
  const response = await client.get(`/writing/stats/by-task/${taskId}/daily`, {
    params: { days },
  });
  return response.data;
}

export async function getWritingStreak(taskId: number): Promise<{ streak: number }> {
  const response = await client.get(`/writing/stats/streak`, {
    params: { task_id: taskId },
  });
  return response.data;
}
