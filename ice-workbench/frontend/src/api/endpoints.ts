import http, { api } from "./client";
import type {
  AgentCard,
  AgentRefreshResult,
  ChatMessage,
  ConversationSummary,
  FileMeta,
  FileRefreshResult,
  GlobalToggles,
  JoinRequest,
  LoginResponse,
  NotificationItem,
  PageData,
  SkillCard,
  TaskDetail,
  TaskSummary,
  UserPublic,
} from "@/types/api";

export const authApi = {
  login: (email: string, password: string) =>
    api<LoginResponse>(http.post("/auth/login", { email, password })),
  refresh: (refresh_token: string) =>
    api<{ access_token: string; refresh_token: string }>(
      http.post("/auth/refresh", { refresh_token }),
    ),
  feishuStart: () => api<{ auth_url: string; state: string }>(http.post("/auth/feishu/oauth/start")),
  me: () => api<UserPublic>(http.get("/users/me")),
  methods: () =>
    api<{ aegis_enabled: boolean; password_enabled: boolean; feishu_oauth_enabled: boolean }>(
      http.get("/auth/methods"),
    ),
};

export const userApi = {
  search: (q: string) =>
    api<PageData<UserPublic>>(http.get("/users/search", { params: { q } })),
};

export const taskApi = {
  list: () => api<PageData<TaskSummary>>(http.get("/tasks")),
  listPublic: () => api<PageData<TaskSummary>>(http.get("/tasks/public")),
  create: (body: {
    name: string;
    paradigm: string;
    agent_id?: string | null;
    description?: string;
    initial_prompt?: string;
    skill_ids?: string[];
    visibility?: string;
  }) => api<TaskDetail>(http.post("/tasks", body)),
  detail: (id: string) => api<TaskDetail>(http.get(`/tasks/${id}`)),
  conversation: (id: string) =>
    api<{ conversation_id: string; messages: ChatMessage[] }>(
      http.get(`/tasks/${id}/conversation`),
    ),
  remove: (id: string) =>
    api<{ deleted: boolean; task_id: string }>(http.delete(`/tasks/${id}`)),
};

export const fileApi = {
  upload: (taskId: string, file: File, scope: string = "uploaded") => {
    const fd = new FormData();
    fd.append("task_id", taskId);
    fd.append("scope", scope);
    fd.append("file", file);
    return api<FileMeta>(http.post("/files/upload", fd));
  },
  listTask: (taskId: string) =>
    api<PageData<FileMeta>>(http.get(`/files/task/${taskId}`)),
  listPublic: () => api<PageData<FileMeta>>(http.get("/files/public")),
  read: (taskId: string, fileId: string) =>
    api<{ meta: FileMeta; content: string | null; binary?: boolean }>(
      http.get(`/files/task/${taskId}/${fileId}/content`),
    ),
  readPublic: (fileId: string) =>
    api<{ meta: FileMeta; content: string | null; binary?: boolean }>(
      http.get(`/files/public/${fileId}/content`),
    ),
  remove: (taskId: string, fileId: string) =>
    api<{ deleted: boolean }>(http.delete(`/files/task/${taskId}/${fileId}`)),
  import_: (
    taskId: string,
    source_type: "feishu_doc" | "kb_article",
    source_url: string,
    source_ref?: Record<string, unknown>,
  ) => {
    const fd = new FormData();
    fd.append("task_id", taskId);
    fd.append("source_type", source_type);
    fd.append("source_url", source_url);
    if (source_ref) fd.append("source_ref", JSON.stringify(source_ref));
    return api<FileMeta>(http.post("/files/import", fd));
  },
  refresh: (taskId: string, fileId: string) => {
    const fd = new FormData();
    fd.append("task_id", taskId);
    return api<FileRefreshResult>(http.post(`/files/${fileId}/refresh`, fd));
  },
};

// ---- agent snapshot refresh (C3) ----
export const agentSnapshotApi = {
  refresh: (taskId: string, expected_agent_source_version?: string | null) =>
    api<AgentRefreshResult>(
      http.post(`/tasks/${taskId}/agent/refresh`, { expected_agent_source_version }),
    ),
};

// ---- conversations (multi-conv) ----
export const conversationApi = {
  list: (taskId: string) =>
    api<PageData<ConversationSummary>>(http.get(`/tasks/${taskId}/conversations`)),
  create: (taskId: string, title?: string) =>
    api<ConversationSummary>(http.post(`/tasks/${taskId}/conversations`, { title })),
  rename: (taskId: string, convId: string, title: string) =>
    api<ConversationSummary>(http.patch(`/tasks/${taskId}/conversations/${convId}`, { title })),
  remove: (taskId: string, convId: string) =>
    api<{ deleted: boolean }>(http.delete(`/tasks/${taskId}/conversations/${convId}`)),
  get: (taskId: string, convId: string) =>
    api<{ conversation_id: string; messages: ChatMessage[] }>(
      http.get(`/tasks/${taskId}/conversations/${convId}`),
    ),
};

// ---- join requests (W3 collaboration) ----
export const joinRequestApi = {
  submit: (taskId: string, message: string) =>
    api<JoinRequest>(http.post(`/tasks/${taskId}/join-request`, { message })),
  list: (taskId: string, status?: "pending" | "approved" | "rejected") =>
    api<PageData<JoinRequest>>(
      http.get(`/tasks/${taskId}/join-requests`, { params: status ? { status } : {} }),
    ),
  review: (
    taskId: string,
    reqId: string,
    status: "approved" | "rejected",
    reject_reason?: string,
  ) =>
    api<JoinRequest>(
      http.post(`/tasks/${taskId}/join-requests/${reqId}/review`, { status, reject_reason }),
    ),
  removeCollaborator: (taskId: string, userId: string) =>
    api<{ removed: boolean }>(http.delete(`/tasks/${taskId}/collaborators/${userId}`)),
};

export const agentApi = {
  list: () => api<PageData<AgentCard>>(http.get("/agents")),
  get: (id: string) => api<AgentCard>(http.get(`/agents/${id}`)),
};

export const skillApi = {
  list: () => api<PageData<SkillCard>>(http.get("/skills")),
};

export const notifyApi = {
  list: () => api<PageData<NotificationItem>>(http.get("/notifications")),
  readAll: () => api<{ unread: number }>(http.post("/notifications/read-all")),
  read: (id: string) => api<{ id: string; is_read: boolean }>(http.post(`/notifications/${id}/read`)),
};

export const sysApi = {
  toggles: () => api<GlobalToggles>(http.get("/system-config/global-toggles")),
};

export const searchApi = {
  search: (q: string, type?: string) =>
    api<{ tasks: unknown[]; agents: unknown[]; skills: unknown[]; files: unknown[] }>(
      http.get("/search", { params: { q, type } }),
    ),
};

export interface TemplateRecord {
  id: string;
  owner_id: string;
  name: string;
  description?: string | null;
  paradigm: string;
  agent_id?: string | null;
  skill_ids: string[];
  file_seeds: string[];
  initial_prompt?: string | null;
  has_schedule: boolean;
  schedule_config?: unknown;
  visibility: "private" | "public";
  status: "draft" | "approved" | "rejected";
  reject_reason?: string | null;
  created_at: string;
  updated_at: string;
}

export const templateApi = {
  list: (visibility?: string) =>
    api<PageData<TemplateRecord>>(http.get("/templates", { params: { visibility } })),
  create: (body: Partial<TemplateRecord>) => api<TemplateRecord>(http.post("/templates", body)),
  get: (id: string) => api<TemplateRecord>(http.get(`/templates/${id}`)),
  update: (id: string, body: Partial<TemplateRecord>) =>
    api<TemplateRecord>(http.patch(`/templates/${id}`, body)),
  remove: (id: string) => api<{ deleted: boolean }>(http.delete(`/templates/${id}`)),
};

export interface ScheduledTask {
  id: string;
  task_id: string;
  task_name?: string;
  name: string;
  cron: string;
  prompt: string;
  channels: string[];
  enabled: boolean;
  next_fire_at: string | null;
  last_fire_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface ScheduledRun {
  id: string;
  scheduled_id: string;
  task_id: string;
  trigger: "manual" | "cron";
  status: "running" | "success" | "failed" | "skipped";
  started_at: string;
  ended_at: string | null;
  prompt: string;
  output: string | null;
  error: { code: string; message: string } | null;
  tokens?: { input: number; output: number };
}

export const scheduledApi = {
  listMine: () => api<PageData<ScheduledTask>>(http.get("/scheduled-tasks")),
  listByTask: (taskId: string) =>
    api<PageData<ScheduledTask>>(http.get(`/scheduled-tasks/by-task/${taskId}`)),
  create: (taskId: string, body: Partial<ScheduledTask>) =>
    api<ScheduledTask>(http.post(`/scheduled-tasks/by-task/${taskId}`, body)),
  update: (taskId: string, sid: string, body: Partial<ScheduledTask>) =>
    api<ScheduledTask>(http.patch(`/scheduled-tasks/by-task/${taskId}/${sid}`, body)),
  remove: (taskId: string, sid: string) =>
    api<{ deleted: boolean }>(http.delete(`/scheduled-tasks/by-task/${taskId}/${sid}`)),
  runNow: (taskId: string, sid: string) =>
    api<ScheduledRun>(http.post(`/scheduled-tasks/by-task/${taskId}/${sid}/run-now`)),
  listRuns: (taskId: string, sid: string) =>
    api<{ items: ScheduledRun[] }>(http.get(`/scheduled-tasks/by-task/${taskId}/${sid}/runs`)),
};

export const guideApi = {
  get: () => api<{ content: string; path: string | null }>(http.get("/guide")),
};

export interface AdminUser {
  id: string;
  email: string;
  name: string;
  auth_role: "user" | "admin" | "super_admin";
  status: "active" | "disabled";
  feishu_bound: boolean;
  team?: string | null;
  title?: string | null;
  last_login_at?: string | null;
  created_at?: string | null;
}

export interface AdminAgent extends AgentCard {
  system_prompt?: string;
}

export interface AgentPromptSnapshot {
  id: string;
  agent_id: string;
  system_prompt: string;
  saved_by: string;
  saved_by_name?: string;
  saved_at: string;
  change_note?: string | null;
}

export const adminApi = {
  stats: (days = 30) =>
    api<{ users: number; tasks: number; messages: number; days: number }>(
      http.get("/admin/overview/stats", { params: { days } }),
    ),
  alerts: () =>
    api<{ experience_cards: number; public_tasks: number; templates: number; scheduled_failed: number }>(
      http.get("/admin/overview/alerts"),
    ),
  recentUsers: () =>
    api<{ items: AdminUser[] }>(http.get("/admin/overview/recent-users")),
  agentRanking: (days = 30) =>
    api<{ items: Array<{ agent_id: string; name: string; icon: string; messages: number; satisfaction: number }> }>(
      http.get("/admin/overview/agent-ranking", { params: { days } }),
    ),
  listUsers: (q?: string, role?: string, status?: string) =>
    api<PageData<AdminUser>>(http.get("/admin/users", { params: { q, role, status } })),
  createUser: (body: Partial<AdminUser> & { password?: string }) =>
    api<AdminUser>(http.post("/admin/users", body)),
  updateUser: (uid: string, body: Partial<AdminUser> & { password?: string }) =>
    api<AdminUser>(http.patch(`/admin/users/${uid}`, body)),
  deleteUser: (uid: string) =>
    api<{ deleted: boolean }>(http.delete(`/admin/users/${uid}`)),
  auditLogs: (limit = 100) =>
    api<{ items: Array<{ id: string; admin_id: string; action: string; target_type: string; target_id: string; created_at: string; diff: unknown }> }>(
      http.get("/admin/audit-logs", { params: { limit } }),
    ),
  listAgents: () => api<PageData<AdminAgent>>(http.get("/admin/agents")),
  getAgent: (aid: string) => api<AdminAgent>(http.get(`/admin/agents/${aid}`)),
  updateAgent: (aid: string, body: Partial<AdminAgent> & { change_note?: string }) =>
    api<AdminAgent>(http.patch(`/admin/agents/${aid}`, body)),
  promptHistory: (aid: string) =>
    api<{ items: AgentPromptSnapshot[] }>(http.get(`/admin/agents/${aid}/prompt-history`)),
  promptRollback: (aid: string, history_id: string) =>
    api<AdminAgent>(http.post(`/admin/agents/${aid}/prompt-rollback`, { history_id })),
  testChat: (aid: string, body: { content: string; system_prompt?: string }) =>
    api<{ response: string }>(http.post(`/admin/agents/${aid}/test-chat`, body)),
};

// ---- /admin/settings ----

export interface LLMModel {
  id: string;
  label: string;
  input_unit_price: number;
  output_unit_price: number;
  enabled: boolean;
}
export interface LLMConfig {
  budget_monthly_usd: number;
  budget_alert_threshold: number;
  models: LLMModel[];
}
export interface SystemParams {
  upload_max_size_mb: number;
  upload_max_size_hard_cap_mb: number;
  context_size: number;
  tool_call_max_rounds: number;
  tool_call_timeout_s: number;
}
export interface Toggles {
  enable_open_register: boolean;
  enable_public_task_review: boolean;
  enable_feishu_strict_whitelist: boolean;
  enable_feishu_auto_register: boolean;
}
export interface Announcement {
  id: string;
  title: string;
  body: string;
  level: "info" | "warning" | "error";
  audience_scope: string;
  status: "draft" | "published";
  published_at: string | null;
  created_at: string;
  updated_at: string;
}

export const settingsApi = {
  read: () =>
    api<{
      toggles: Toggles;
      system_params: SystemParams;
      llm: LLMConfig;
      announcements: Announcement[];
    }>(http.get("/admin/settings")),
  updateToggles: (patch: Partial<Toggles>) =>
    api<Toggles>(http.patch("/admin/settings/toggles", patch)),
  updateSystemParams: (patch: Partial<SystemParams>) =>
    api<SystemParams>(http.patch("/admin/settings/system-params", patch)),
  resetSystemParams: () => api<SystemParams>(http.post("/admin/settings/system-params/reset")),
  updateBudget: (budget_monthly_usd: number, budget_alert_threshold: number) =>
    api<LLMConfig>(
      http.patch("/admin/settings/llm/budget", { budget_monthly_usd, budget_alert_threshold }),
    ),
  updateModel: (model_id: string, patch: Partial<LLMModel>) =>
    api<LLMModel>(http.patch(`/admin/settings/llm/models/${model_id}`, patch)),
  listAnnouncements: () =>
    api<{ items: Announcement[] }>(http.get("/admin/settings/announcements")),
  createAnnouncement: (body: Partial<Announcement>) =>
    api<Announcement>(http.post("/admin/settings/announcements", body)),
  updateAnnouncement: (id: string, body: Partial<Announcement>) =>
    api<Announcement>(http.patch(`/admin/settings/announcements/${id}`, body)),
  deleteAnnouncement: (id: string) =>
    api<{ deleted: boolean }>(http.delete(`/admin/settings/announcements/${id}`)),
};

// ---- /admin/usage ----

export interface UsageSummary {
  month: string;
  input_tokens: number;
  output_tokens: number;
  cost_usd: number;
  calls: number;
  budget_usd: number;
  budget_threshold: number;
  budget_used_ratio: number;
  budget_state: "ok" | "warning" | "exceeded";
}
export interface DailyUsage {
  day: string;
  input_tokens: number;
  output_tokens: number;
  cost_usd: number;
  calls: number;
}
export interface DimUsage {
  key: string;
  input_tokens: number;
  output_tokens: number;
  cost_usd: number;
  calls: number;
}

export const usageApi = {
  summary: () => api<UsageSummary>(http.get("/admin/usage/summary")),
  daily: (days = 30) =>
    api<{ items: DailyUsage[] }>(http.get("/admin/usage/daily", { params: { days } })),
  byDim: (dimension: "model" | "user_id" | "agent_id" | "task_id", days = 30, limit = 20) =>
    api<{ items: DimUsage[] }>(
      http.get("/admin/usage/by-dimension", { params: { dimension, days, limit } }),
    ),
  exportCsvUrl: (days = 30) => `/api/v1/admin/usage/export.csv?days=${days}`,
};

// ---- /admin/sql-audit ----

export interface SqlAuditRow {
  id: string;
  user_id: string | null;
  agent_id: string | null;
  task_id: string | null;
  conversation_id: string | null;
  sql: string;
  decision: "allow" | "warn" | "block";
  block_reason: string | null;
  error_message: string | null;
  rows_returned: number | null;
  duration_ms: number | null;
  created_at: string;
}
export interface SqlAuditStats {
  by_decision: Record<string, number>;
  daily: Array<{ day: string; decision: string; c: number }>;
}

export const sqlAuditApi = {
  list: (params: {
    decision?: string;
    user_id?: string;
    agent_id?: string;
    task_id?: string;
    q?: string;
    days?: number;
    limit?: number;
  }) => api<PageData<SqlAuditRow>>(http.get("/admin/sql-audit", { params })),
  stats: (days = 30) =>
    api<SqlAuditStats>(http.get("/admin/sql-audit/stats", { params: { days } })),
  exportCsvUrl: (days = 30) => `/api/v1/admin/sql-audit/export.csv?days=${days}`,
};

// ---- experience cards ----

export interface ExperienceCard {
  id: string;
  task_id: string;
  agent_id: string | null;
  author_id: string;
  title: string;
  rule: string;
  reason: string;
  source_message_id: string | null;
  status: "draft" | "approved" | "rejected";
  reject_reason: string | null;
  approved_by: string | null;
  approved_at: string | null;
  created_at: string;
  updated_at: string;
}

export const experienceApi = {
  createForTask: (
    taskId: string,
    body: { title: string; rule: string; reason?: string; source_message_id?: string },
  ) => api<ExperienceCard>(http.post(`/experience-cards/tasks/${taskId}`, body)),
  listForTask: (taskId: string, status?: string) =>
    api<{ items: ExperienceCard[] }>(
      http.get(`/experience-cards/tasks/${taskId}`, { params: { status } }),
    ),
  listForAgent: (agentId: string) =>
    api<{ items: ExperienceCard[] }>(http.get(`/experience-cards/agents/${agentId}`)),
};

// ---- task share/unshare ----

export const shareApi = {
  share: (taskId: string) =>
    api<{ visibility: string; publish_status: string }>(http.post(`/tasks/${taskId}/share`)),
  unshare: (taskId: string) =>
    api<{ visibility: string; publish_status: string }>(http.post(`/tasks/${taskId}/unshare`)),
};

// ---- admin: review center ----

export interface ReviewSummary {
  experience_cards_pending: number;
  public_tasks_pending: number;
  templates_pending: number;
}

export const reviewApi = {
  summary: () => api<ReviewSummary>(http.get("/admin/review-center/summary")),
  listCards: (params: { status?: string; agent_id?: string }) =>
    api<PageData<ExperienceCard>>(http.get("/admin/experience-cards", { params })),
  reviewCard: (cardId: string, status: "approved" | "rejected", reject_reason?: string) =>
    api<ExperienceCard>(http.post(`/admin/experience-cards/${cardId}/review`, { status, reject_reason })),
  batchReviewCards: (card_ids: string[], status: "approved" | "rejected", reject_reason?: string) =>
    api<{ items: ExperienceCard[] }>(
      http.post("/admin/experience-cards/batch-review", { card_ids, status, reject_reason }),
    ),
  listPublicTasks: (status?: string) =>
    api<PageData<TaskSummary>>(http.get("/admin/public-tasks", { params: { status } })),
  reviewPublicTask: (taskId: string, decision: "approve" | "reject" | "delist", reason?: string) =>
    api<TaskSummary>(http.post(`/admin/public-tasks/${taskId}/review`, { decision, reason })),
};

// ---- admin: public files ----

export interface PublicFileMeta {
  id: string;
  name: string;
  scope: "public";
  task_id: null;
  path: string;
  file_type: string | null;
  format: string | null;
  size_bytes: number;
  is_pinned: boolean;
  created_at: string;
  updated_at?: string;
}

export const adminFileApi = {
  list: () => api<PageData<PublicFileMeta>>(http.get("/admin/files")),
  upload: (file: File, isPinned = false) => {
    const fd = new FormData();
    fd.append("file", file);
    fd.append("is_pinned", String(isPinned));
    return api<PublicFileMeta>(http.post("/admin/files/upload", fd));
  },
  read: (id: string) =>
    api<{ meta: PublicFileMeta; content: string | null; binary?: boolean }>(
      http.get(`/admin/files/${id}/content`),
    ),
  update: (id: string, body: { content?: string; is_pinned?: boolean }) =>
    api<PublicFileMeta>(http.patch(`/admin/files/${id}`, body)),
  remove: (id: string) => api<{ deleted: boolean }>(http.delete(`/admin/files/${id}`)),
};

// ---- admin: skills ----

export interface SkillRecord {
  id: string;
  name: string;
  description: string;
  category: string;
  tool_entry: string;
  tool_schema: Record<string, unknown>;
  builtin: boolean;
  enabled: boolean;
}

export const adminSkillApi = {
  list: () => api<PageData<SkillRecord>>(http.get("/admin/skills")),
  get: (id: string) => api<SkillRecord>(http.get(`/admin/skills/${id}`)),
  create: (body: Partial<SkillRecord>) => api<SkillRecord>(http.post("/admin/skills", body)),
  update: (id: string, body: Partial<SkillRecord>) =>
    api<SkillRecord>(http.patch(`/admin/skills/${id}`, body)),
  remove: (id: string) => api<{ deleted: boolean }>(http.delete(`/admin/skills/${id}`)),
  validate: (tool_schema: Record<string, unknown>) =>
    api<{ valid: boolean; reason: string | null }>(
      http.post("/admin/skills/validate-schema", { tool_schema }),
    ),
  testRun: (id: string, args: Record<string, unknown>) =>
    api<{ success: boolean; result?: unknown; error?: string }>(
      http.post(`/admin/skills/${id}/test-run`, { arguments: args }),
    ),
};

// ---- admin: knowledge bases ----

export interface KBRecord {
  id: string;
  name: string;
  description: string | null;
  source_type: "feishu_wiki" | "mify_rag";
  config: Record<string, unknown>;
  sync_frequency: "manual" | "hourly" | "daily" | "weekly";
  visibility: string;
  status: string;
  last_sync_at: string | null;
  last_sync_summary: { status: string; added: number; updated: number; failed: number } | null;
  doc_count: number;
  enabled: boolean;
  created_at: string;
  updated_at: string;
}

export interface KBSyncLog {
  id: string;
  kb_id: string;
  trigger: string;
  started_at: string;
  ended_at: string | null;
  status: "running" | "success" | "failed";
  added: number;
  updated: number;
  failed: number;
  error: { code: string; message: string } | null;
}

export const adminKBApi = {
  list: () => api<PageData<KBRecord>>(http.get("/admin/knowledge-bases")),
  get: (id: string) => api<KBRecord>(http.get(`/admin/knowledge-bases/${id}`)),
  create: (body: Partial<KBRecord>) => api<KBRecord>(http.post("/admin/knowledge-bases", body)),
  update: (id: string, body: Partial<KBRecord>) =>
    api<KBRecord>(http.patch(`/admin/knowledge-bases/${id}`, body)),
  remove: (id: string) => api<{ deleted: boolean }>(http.delete(`/admin/knowledge-bases/${id}`)),
  sync: (id: string) => api<KBSyncLog>(http.post(`/admin/knowledge-bases/${id}/sync`)),
  syncLogs: (id: string) =>
    api<{ items: KBSyncLog[] }>(http.get(`/admin/knowledge-bases/${id}/sync-logs`)),
  testConnection: (id: string) =>
    api<{ ok: boolean; message?: string; error_code?: string }>(
      http.post(`/admin/knowledge-bases/${id}/test-connection`),
    ),
};

// ---- admin: templates ----

export const adminTemplateApi = {
  list: (status?: string, visibility?: string) =>
    api<PageData<TemplateRecord>>(http.get("/admin/templates", { params: { status, visibility } })),
  review: (id: string, status: "approved" | "rejected", reject_reason?: string) =>
    api<TemplateRecord>(http.post(`/admin/templates/${id}/review`, { status, reject_reason })),
  remove: (id: string) => api<{ deleted: boolean }>(http.delete(`/admin/templates/${id}`)),
};

// ---- model gateway (public list) ----

export interface ModelOption {
  id: string;
  label: string;
}
export const modelApi = {
  list: () =>
    api<{ items: ModelOption[]; default: string }>(http.get("/system-config/models")),
};
