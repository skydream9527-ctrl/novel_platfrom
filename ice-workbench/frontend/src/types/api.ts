export interface ApiEnvelope<T = unknown> {
  code: number;
  message: string;
  error_code?: string;
  data: T;
}

export interface PageData<T> {
  items: T[];
  total: number;
  page?: number;
  page_size?: number;
  unread?: number;
}

export interface UserPublic {
  id: string;
  email: string;
  name: string;
  auth_role: "user" | "admin" | "super_admin";
  avatar_url?: string | null;
  feishu_bound: boolean;
  team?: string | null;
  title?: string | null;
}

export interface TokenPair {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

export interface LoginResponse {
  user: UserPublic;
  tokens: TokenPair;
}

export interface AgentCard {
  id: string;
  name: string;
  paradigm: string;
  icon: string;
  color: string;
  description?: string;
  publish_status?: string;
}

export interface SkillCard {
  id: string;
  name: string;
  description: string;
  description_zh?: string | null;
  category: string;
  tool_entry: string;
  tool_schema?: Record<string, unknown>;
  builtin?: boolean;
  enabled?: boolean;
}

export interface TaskSummary {
  id: string;
  name: string;
  paradigm: string;
  agent_id?: string | null;
  owner_id: string;
  status: string;
  visibility: string;
  file_count: number;
  last_message_preview?: string | null;
  updated_at?: string | null;
  created_at?: string | null;
  role?: "owner" | "collaborator";
}

export interface TaskDetail extends TaskSummary {
  description?: string | null;
  initial_prompt?: string | null;
  skill_ids?: string[];
  collaborators?: Array<{ user_id: string; role: string; status: string }>;
  workspace?: { current_conversation_id?: string; model?: string };
  agent_update_available?: boolean;
  imported_file_count?: number;
  snapshot?: {
    mode: "live" | "frozen";
    agent_source_version: string | null;
    frozen_at: string | null;
    frozen_by: string | null;
    last_manual_update_at: string | null;
    last_manual_update_by: string | null;
  };
}

export interface FileMeta {
  id: string;
  name: string;
  path: string;
  scope: "input" | "output" | "uploaded" | "public" | "imported";
  task_id?: string | null;
  file_type?: string | null;
  format?: string | null;
  size_bytes: number;
  is_pinned: boolean;
  created_at?: string | null;
  // Imported-file fields (source_type = kb_article | feishu_doc)
  source_type?: "kb_article" | "feishu_doc" | null;
  source_url?: string | null;
  imported_at?: string | null;
  imported_by?: string | null;
  last_refreshed_at?: string | null;
  // Backend uses these alternate keys for imported files
  file_id?: string | null;
  filename?: string | null;
  size?: number | null;
}

export interface ConversationSummary {
  id: string;
  title: string;
  created_by: string;
  created_at: string;
  last_message_at: string;
  message_count: number;
}

export interface JoinRequest {
  id: string;
  user_id: string;
  message: string;
  status: "pending" | "approved" | "rejected";
  created_at: string;
  reviewed_at?: string | null;
  reviewed_by?: string | null;
  reject_reason?: string | null;
}

export interface AgentRefreshResult {
  changed: boolean;
  new_version?: string;
  diff_summary?: {
    cards_added: number;
    cards_removed: number;
    system_changed: boolean;
  };
}

export interface FileRefreshResult {
  changed: boolean;
  size: number;
  last_refreshed_at: string;
}

export interface NotificationItem {
  id: string;
  kind:
    | "experience"
    | "task-fail"
    | "collaboration"
    | "token-alert"
    | "system"
    | "public-task-pending";
  title: string;
  body: string;
  action_url?: string | null;
  is_read: boolean;
  created_at: string;
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant" | "system";
  content: string;
  tool_uses?: Array<{ id: string; name: string; input: Record<string, unknown> }>;
  agent_id?: string;
  user_id?: string;
  created_at: string;
}

export interface ToolCall {
  tool_call_id: string;
  tool_name: string;
  display_name?: string;
  arguments: Record<string, unknown>;
  status: "executing" | "done" | "error" | "timeout";
  result?: unknown;
  error?: { code: string; message: string };
}

export interface GlobalToggles {
  feishu_enabled: boolean;
  llm_enabled: boolean;
  kyuubi_enabled: boolean;
  enable_open_register: boolean;
  enable_public_task_review: boolean;
  enable_feishu_strict_whitelist: boolean;
  upload_max_size_mb: number;
  upload_max_size_hard_cap_mb: number;
}
