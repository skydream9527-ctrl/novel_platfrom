# API Map · 后端端点 ↔ 决策 ID

> 决策详细见 [`../design_decisions.md`](../design_decisions.md)，全部新接口实现见 [`../requirements/BACKEND.md`](../requirements/BACKEND.md)

## 端点统计

| 状态 | 数量 |
|---|---|
| 现有保留 | ~40 |
| 新增 | ~50 |
| 修改字段 / 行为 | ~25 |
| 删除 | 1（`/admin/costs/*`） |

## 公开端点（无需认证）

| 方法 | 路径 | 说明 | 决策 |
|---|---|---|---|
| GET | `/api/v1/health` | 健康检查 | 现有 |
| GET | `/api/v1/guide` | 使用指南 markdown | 现有 |
| GET | `/api/v1/announcements/active` | 公告 | 现有 + D131 受众过滤 |
| GET | `/api/v1/system-config/global-toggles` | 3 个 enable_* 开关 | **新增** D102/E2 |
| GET | `/api/v1/paradigm-presets` | 范式预设 | **新增** D76 |

## 认证（auth）

| 方法 | 路径 | 决策 |
|---|---|---|
| GET | `/auth/accounts` | D3 测试快捷登录限定 2 个 |
| POST | `/auth/login` | D85 super_admin 拒绝密码 |
| POST | `/auth/login-by-account` | D3 仅张明远 + 李思涵 |
| POST | `/auth/refresh` | 现有 |
| GET | `/auth/me` | 现有 |
| POST | `/auth/register` | D83 默认禁用 + 全局开关 |
| POST | `/auth/feishu/oauth/start` | **新增** D89 |
| POST | `/auth/feishu/oauth/callback` | **新增** D89 + 白名单 |
| POST | `/auth/feishu/bind` | **新增** D89 |

## 用户搜索（D51 新增公开非 admin 端点）

| 方法 | 路径 | 决策 |
|---|---|---|
| GET | `/users/search?q=` | **新增** D51（限频 30/min） |

## 通知

| 方法 | 路径 | 决策 |
|---|---|---|
| GET | `/notifications` | **新增** D29（替代 mock） |
| POST | `/notifications/read-all` | **新增** D29 |
| POST | `/notifications/{id}/read` | **新增** D29 |

## 任务（tasks）

| 方法 | 路径 | 决策 |
|---|---|---|
| GET | `/tasks` | 改 D23 加 last_message_preview |
| POST | `/tasks` | 改 D72 接收 query 参数预填 |
| GET | `/tasks/public` | **新增** D11 |
| GET | `/tasks/shared/list` | 改 D11 与 public 合并/独立 |
| GET | `/tasks/{tid}` | 现有 |
| PATCH | `/tasks/{tid}` | 改 D60 归档语义 |
| DELETE | `/tasks/{tid}` | 现有 + 二次确认 |
| POST | `/tasks/{tid}/share` | 改 D14 双轨制 |
| POST | `/tasks/{tid}/unshare` | 现有 |
| POST | `/tasks/{tid}/join` | **新增** D12-D13 加入协作 |
| GET | `/tasks/invites/{token}` | **新增** D50 邀请验证 |
| POST | `/tasks/invites/{token}/accept` | **新增** D50 接受邀请 |
| POST | `/tasks/{tid}/abort` | **新增** D42 中止 LLM 流式 |

## Workspace

所有 `/workspaces/{wsid}/*` 接口现有，少量字段调整：

| 方法 | 路径 | 改动 |
|---|---|---|
| POST | `/workspaces/{wsid}/files/upload` | D31 后端默认上限改 20MB |
| GET | `/workspaces/{wsid}/knowledge-bases` | D54 source_type 收敛 |
| POST | `/workspaces/{wsid}/knowledge-bases/{kbid}/sync` | D57 toast 反馈 |

## 对话与消息

| 方法 | 路径 | 决策 |
|---|---|---|
| GET | `/conversations/{cid}/messages` | 现有 + D45 向上加载 |
| POST | `/conversations/messages/{mid}/feedback` | 现有 + D47 hover |
| POST | `/conversations/messages/{mid}/extract-experience` | 现有 |
| GET | `/messages/{mid}/source` | **新增** D118 跳回原文 |

## Agent（公开 + 管理）

### 公开

| 方法 | 路径 | 决策 |
|---|---|---|
| GET | `/agents/public` | 现有 |
| GET | `/agents/{aid}` | **新增** D63 单详情 |
| GET | `/agents/{aid}/skills` | **新增** D63 |
| GET | `/agents/{aid}/experience-cards?status=approved` | **新增** D63/D66 |
| GET | `/agents/{aid}/sample-tasks?limit=3` | **新增** D69 |
| POST | `/agents/{aid}/share` | 现有 |
| POST | `/agents/{aid}/test-chat` | **新增** D68/D111 沙盒 |

### 管理

| 方法 | 路径 | 决策 |
|---|---|---|
| GET | `/admin/agents` | 现有 + D111 publish_status 收敛 |
| POST | `/admin/agents` | 现有 |
| GET | `/admin/agents/{aid}` | **新增** D113 |
| PATCH | `/admin/agents/{aid}` | 现有 |
| DELETE | `/admin/agents/{aid}` | 现有 |
| POST | `/admin/agents/{aid}/review` | 现有 |
| GET | `/admin/agents/{aid}/skills` | 现有 |
| PUT | `/admin/agents/{aid}/skills` | 现有 |
| GET | `/admin/agents/{aid}/prompt-history` | **新增** D114 |
| POST | `/admin/agents/{aid}/prompt-rollback` | **新增** D114 |
| GET | `/admin/agents/{aid}/memories` | **新增** D113 |
| GET | `/admin/agents/{aid}/evolution` | **新增** D113 |
| GET | `/admin/agents/ranking?period=` | **新增** D103（替代 mock） |

## Skills（管理）

| 方法 | 路径 | 决策 |
|---|---|---|
| GET | `/admin/skills` | 现有 |
| PATCH | `/admin/skills/{sid}` | 现有 |
| DELETE | `/admin/skills/{sid}` | 现有 |
| POST | `/admin/skills/validate-entry` | **新增** D116 |
| POST | `/admin/skills/{sid}/test-run` | **新增** D117 |

## Paradigm Presets（D115 拆出）

| 方法 | 路径 | 决策 |
|---|---|---|
| GET | `/admin/paradigm-presets` | 现有（移到独立路由） |
| PUT | `/admin/paradigm-presets/{paradigm}` | 现有 |

## 经验卡片（admin/experience-cards）

| 方法 | 路径 | 决策 |
|---|---|---|
| GET | `/admin/experience-cards?agent_id=&status[]=` | 改 D118 多筛选 |
| PATCH | `/admin/experience-cards/{cid}` | 现有 |
| POST | `/admin/experience-cards/{cid}/review` | 现有 + reject_reason |
| POST | `/admin/experience-cards/batch-review` | **新增** D118 批量 |
| DELETE | `/admin/experience-cards/{cid}` | 现有 |

## 公共任务（admin/public-tasks）

| 方法 | 路径 | 决策 |
|---|---|---|
| GET | `/admin/public-tasks?status=` | **新增** D122（替代 mock） |
| POST | `/admin/public-tasks/{tid}/review` | **新增** D122 |
| POST | `/admin/public-tasks/{tid}/delist` | **新增** D122 |

## 模板（templates / admin/templates）

| 方法 | 路径 | 决策 |
|---|---|---|
| GET | `/templates?visibility=&status=` | 改 D121 字段扩展 |
| GET | `/admin/templates` | 改 D121 |
| POST | `/admin/templates` | 改 D121 字段扩展 |
| PATCH | `/admin/templates/{tid}` | 改 D121 |
| POST | `/admin/templates/{tid}/review` | **新增** D121 |
| POST | `/admin/templates/from-task/{tid}` | **新增** D121 |
| DELETE | `/admin/templates/{tid}` | 现有 |

## 审核中心（D123 新增）

| 方法 | 路径 | 决策 |
|---|---|---|
| GET | `/admin/review-center/summary` | **新增** D123 |

## 知识库（admin/knowledge-bases）

| 方法 | 路径 | 决策 |
|---|---|---|
| GET | `/admin/knowledge-bases` | 现有 |
| POST | `/admin/knowledge-bases` | 现有 |
| GET | `/admin/knowledge-bases/{kbid}` | 现有 |
| PATCH | `/admin/knowledge-bases/{kbid}` | **新增** D119 编辑 |
| DELETE | `/admin/knowledge-bases/{kbid}` | 现有 |
| POST | `/admin/knowledge-bases/{kbid}/sync` | 现有 + D57 toast |
| POST | `/admin/knowledge-bases/{kbid}/test-connection` | **新增** D119 |
| GET | `/admin/knowledge-bases/{kbid}/sync-logs` | **新增** D119 |

## 文件（admin/files）

| 方法 | 路径 | 决策 |
|---|---|---|
| GET | `/admin/files` | 现有 + D120 来源筛选 |
| POST | `/admin/files/upload` | **新增** D120 |
| PATCH | `/admin/files/{fid}` | 现有 |
| PATCH | `/admin/files/{fid}/content` | **新增** D120 文本编辑 |
| PATCH | `/admin/files/{fid}/pin` | **新增** D120 置顶 |
| DELETE | `/admin/files/{fid}` | 现有 + 公共文件防删（D53/D120） |

## 用户管理（admin/users）

| 方法 | 路径 | 决策 |
|---|---|---|
| GET | `/admin/users` | 现有 + D106 三级角色 |
| POST | `/admin/users` | 现有 + D108 password 可空 |
| POST | `/admin/users/whitelist` | **新增** D108 |
| PATCH | `/admin/users/{uid}` | 改 D87 auth_role 仅 super_admin |
| POST | `/admin/users/{uid}/reset-password` | 现有 |
| POST | `/admin/users/{uid}/feishu-invite` | **新增** D107 |
| DELETE | `/admin/users/{uid}` | 现有 + super_admin 保护 |
| POST | `/admin/users/batch-disable` | **新增** D109 |
| POST | `/admin/users/batch-enable` | **新增** D109 |

## 模型管理（admin/models / llm-models）

| 方法 | 路径 | 决策 |
|---|---|---|
| GET | `/admin/models` | 现有 + D130 单价字段 |
| POST | `/admin/models` | 现有 + D130 |
| PATCH | `/admin/models/{mid}` | 现有 |
| PATCH | `/admin/llm-models/{mid}/pricing` | **新增** D126 单价配置 |
| DELETE | `/admin/models/{mid}` | 现有 + ConfirmModal |

## 系统配置（admin/config）

| 方法 | 路径 | 决策 |
|---|---|---|
| GET | `/admin/config` | 现有 + 新键 |
| PUT | `/admin/config` | 现有 |
| GET | `/admin/system-config/llm-budget` | **新增** D126 |
| PATCH | `/admin/system-config/llm-budget` | **新增** D126 |

新键见 [BACKEND.md §2 SystemConfig 新增 keys](../requirements/BACKEND.md#systemconfig-新增-keys)

## 公告（admin/announcements）

| 方法 | 路径 | 决策 |
|---|---|---|
| GET | `/admin/announcements` | 现有 + D131 audience/status |
| POST | `/admin/announcements` | 现有 + D131 |
| PATCH | `/admin/announcements/{aid}` | 现有 |
| DELETE | `/admin/announcements/{aid}` | 现有 |

## 用量与成本（admin/usage）

| 方法 | 路径 | 决策 |
|---|---|---|
| GET | `/admin/usage/summary?days=` | 现有 |
| GET | `/admin/usage/daily?days=` | 现有 |
| GET | `/admin/usage/by-model?days=` | 现有 |
| GET | `/admin/usage/by-user?days=` | 现有 |
| GET | `/admin/usage/by-agent?days=` | **新增** D126 |
| GET | `/admin/usage/by-task?days=` | **新增** D126 |
| GET | `/admin/usage/export.csv?period=&type=` | **新增** D126 |

旧 `/admin/costs/*` 全部删除（D125 合并到 usage）。

## SQL 审计

| 方法 | 路径 | 决策 |
|---|---|---|
| GET | `/admin/sql-audit?...` | 改 D127 多筛选 + 全文搜索 |
| GET | `/admin/sql-audit/export.csv?...` | **新增** D127 |

## 审计日志

| 方法 | 路径 | 决策 |
|---|---|---|
| GET | `/admin/audit-logs` | 现有 |

## 定时任务

| 方法 | 路径 | 决策 |
|---|---|---|
| GET | `/tasks/{tid}/scheduled-tasks` | 现有 |
| POST | `/tasks/{tid}/scheduled-tasks` | 现有 + D74 同步配置 |
| PATCH | `/tasks/{tid}/scheduled-tasks/{sid}` | 现有 |
| DELETE | `/tasks/{tid}/scheduled-tasks/{sid}` | 现有 + ConfirmModal |
| POST | `/scheduled-tasks/{sid}/run-now` | **新增** D80 |
| GET | `/scheduled-tasks/{sid}/runs?limit=` | **新增** D81 |

## WebSocket

```text
WS /api/v1/ws/conversations/{cid}
```

协议规范见 [SHARED.md §5](../requirements/SHARED.md#5-websocket-协议-v2)。

## 本地资源（local-agents / local-skills）

```text
GET /local-agents
GET /local-agents/{dir_name}
GET /local-skills
GET /local-skills/{dir_name}
```

无变更（已对接真实文件目录）。

## 删除的端点

| 路径 | 决策 |
|---|---|
| `/admin/costs/*` 整组 | D125 合并到 `/admin/usage` |

## 错误码索引

完整错误码表见 [SHARED.md §6](../requirements/SHARED.md#6-错误码命名规范)。
