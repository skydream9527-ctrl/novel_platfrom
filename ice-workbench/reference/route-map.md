# Route Map · 前端路由 ↔ 决策 ID

> 23 个路由的完整索引，每条决策原文见 [`../design_decisions.md`](../design_decisions.md)

## 公开路由（无需登录）

| 路由 | 文件 | 关键决策 | 角色 | 设计稿 |
|---|---|---|---|---|
| `/login` | `pages/LoginPage.tsx` | D1–D6 | all | `design_v3/login_v3.html` |
| `/guide` | `pages/GuidePage.tsx` | D90–D95 | all | `design_v3/guide_v3.html` |
| `/introduce` | `pages/IntroducePage.tsx` | D96–D100 | all | `design_v3/introduce_v3.html` |
| `/register` | ❌ **删除** | D83–D84 | — | — |

## 主用户路由（AuthGuard）

| 路由 | 文件 | 关键决策 | 设计稿 |
|---|---|---|---|
| `/dashboard` | `pages/DashboardPage.tsx` | D7–D27 | `design_v3/dashboard_v3.html` |
| `/workspace/:taskId` | `pages/WorkspacePage.tsx` | D28–D62 | `design_v3/workspace_v3.html` 等 3 份 |
| `/agent/:agentId` | `pages/AgentDetailPage.tsx` | D63–D70 | `design_v3/agent_detail_v3.html` |
| `/create-task` | `pages/CreateTaskPage.tsx` | D71–D76 | `design_v3/create_task_v3.html` |
| `/scheduled-tasks` | `pages/ScheduledTasksPage.tsx` | D77–D82 | `design_v3/scheduled_task_v3.html` |

## 管理后台（AuthGuard + AdminGuard）

### 监控组

| 路由 | 文件 | 关键决策 | 角色 |
|---|---|---|---|
| `/admin` | `pages/admin/AdminDashboard.tsx` | D101–D110 | admin+ |
| `/admin/usage` | `pages/admin/AdminUsageStats.tsx` | D125–D128 | admin+ |
| `/admin/sql-audit` | `pages/admin/AdminSQLAudit.tsx` | D127–D128 | admin+ |
| ~~`/admin/costs`~~ | ❌ **删除** D125 | — | — |

### 内容审核组

| 路由 | 文件 | 关键决策 |
|---|---|---|
| `/admin/review-center` | **新增** | D123–D124 |
| `/admin/experience-cards` | `pages/admin/AdminExperienceCards.tsx` | D118 |
| `/admin/public-tasks` | `pages/admin/AdminPublicTasks.tsx` | D122 |
| `/admin/templates` | `pages/admin/AdminTemplates.tsx` | D121 |
| `/admin/files` | `pages/admin/AdminFiles.tsx` | D120 |

### 资源管理组

| 路由 | 文件 | 关键决策 |
|---|---|---|
| `/admin/agents` | `pages/admin/AdminAgents.tsx` | D111–D112 |
| `/admin/agents/:agentId/edit` | `pages/admin/AdminAgentEdit.tsx` | D113–D114 |
| `/admin/skills` | `pages/admin/AdminSkills.tsx` | D116–D117 |
| `/admin/paradigm-presets` | **新增** | D115 |
| `/admin/knowledge-bases` | `pages/admin/AdminKnowledgeBases.tsx` | D119 |

### 用户与配置组

| 路由 | 文件 | 关键决策 | 角色 |
|---|---|---|---|
| `/admin/users` | `pages/admin/AdminUsers.tsx` | D106–D110 | admin+（auth_role 编辑仅 super_admin） |
| `/admin/settings` | `pages/admin/AdminSettings.tsx` | D129–D131 | **super_admin 专属** |

## 设计稿文件清单（14 份）

```text
design_v3/
├── login_v3.html
├── dashboard_v3.html
├── workspace_v3.html
├── workspace_chat_v3.html
├── workspace_files_v3.html
├── agent_detail_v3.html
├── create_task_v3.html
├── scheduled_task_v3.html
├── admin_dashboard_v3.html
├── admin_agents_v3.html
├── states_demo_v3.html
├── notification_center_demo_v3.html
├── introduce_v3.html
└── guide_v3.html         (新增，v2 没有)
```

## 决策 → 路由反向索引

### 全局影响（多路由）

| 决策 | 影响范围 |
|---|---|
| D28 / D64 / D101 | TopNav 统一（影响所有顶栏） |
| D37 | react-markdown 统一（Workspace + Files + Guide） |
| D52 | useFileUpload hook（Workspace 多处） |
| D85–D89 | 三级角色（影响所有需要角色 gate 的页） |
| D102 | SuperAdminGuard（/admin/settings 整页） |
| D103 / D125 | AdminLayout sidebar 重构 |
| D128 | ECharts 全图表配色 |
| D134–D139 | 文件优先存储（影响所有需要持久化的页） |

### 单路由

详见上方各路由表格的"关键决策"列。

## 路由守卫

```text
/login, /register, /guide, /introduce  →  无守卫
/dashboard, /workspace/:taskId, /agent/:agentId,
/create-task, /scheduled-tasks         →  AuthGuard
/admin/*                                →  AuthGuard + AdminGuard (admin+)
/admin/settings                         →  AuthGuard + AdminGuard + SuperAdminGuard
```
