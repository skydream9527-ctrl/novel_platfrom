# SHARED — 全局约束 / 设计 token / 协议规范

> 前后端共同遵守的契约，决策原文见 [`../design_decisions.md`](../design_decisions.md)

## 目录

1. [全局约束（G1 / G2 / G3）](#1-全局约束)
2. [角色权限矩阵（D86）](#2-角色权限矩阵-d86)
3. [设计 Token（v3 暖色）](#3-设计-token-v3-暖色)
4. [布局尺寸 / 字体 / 动画](#4-布局尺寸--字体--动画)
5. [WebSocket 协议 v2](#5-websocket-协议-v2)
6. [错误码命名规范](#6-错误码命名规范)
7. [API 响应规范](#7-api-响应规范)
8. [v3 状态设计规范](#8-v3-状态设计规范)
9. [文件优先存储约束（G3）](#9-文件优先存储约束-g3)

---

## 1. 全局约束

### G1 · 用户工作页面禁止虚构数据

**适用范围**：所有 user-facing 页面（Dashboard / Workspace / Agent详情 / Create-Task / Scheduled-Tasks / Guide / Introduce）

**禁止项**：mock 数据、占位假数据、硬编码示例数据。所有展示的资源必须来自真实接口。

**例外**：管理后台的 EmptyState 演示页（`states_demo`）、设计稿（`design_v3/`）。

### G2 · 三级角色体系

详见第 2 节权限矩阵。super_admin 必须飞书 OAuth，admin 与 user 可飞书或密码。

### G3 · 文件优先存储

文件系统是 source of truth，SQLite 仅作 cache/索引。详见第 9 节。

---

## 2. 角色权限矩阵（D86）

| 能力 | super_admin | admin | user |
|---|:---:|:---:|:---:|
| 修改任意用户 auth_role | ✅ | ❌ | ❌ |
| 删除用户 | ✅ | ❌ | ❌ |
| 系统配置 / 全局开关 | ✅ | ❌ | ❌ |
| 单价配置 / 月度预算 | ✅ | ❌ | ❌ |
| 用户管理（增/查/改非角色字段/重置密码/禁用） | ✅ | ✅ | ❌ |
| Agent 配置 + Skills 绑定 | ✅ | ✅ | ❌ |
| 审核经验卡片 / 公共任务 / 模板 | ✅ | ✅ | ❌ |
| 公共文件 CRUD | ✅ | ✅ | ❌ |
| 知识库管理 + 同步 | ✅ | ✅ | ❌ |
| 公告 CRUD | ✅ | ✅ | ❌ |
| 查看审计日志 | ✅ | ✅ | ❌ |
| 调试 Prompt / 编辑 System Prompt | ✅ | ✅ | ❌ |
| 创建任务 / 对话 / 上传文件 | ✅ | ✅ | ✅ |
| 浏览公共区 | ✅ | ✅ | ✅ |

### 关键约束

- **super_admin 不能降级自己**（D87）
- **系统至少保留 1 个 super_admin**（D87）
- **super_admin 必须飞书登录**，密码登录返回 `SUPER_ADMIN_REQUIRES_FEISHU`（D85）

---

## 3. 设计 Token（v3 暖色）

### 暗色模式（默认）

```css
:root[data-theme="dark"] {
  /* Background Layers */
  --bg:            #1a1a1a;
  --surface:       #212121;
  --surface-2:     #2a2a2a;
  --surface-3:     #333333;
  --border:        #3d3d3d;
  --border-light:  #4d4d4d;

  /* Text */
  --text:          #ede9e3;
  --text-dim:      #a39e93;
  --text-muted:    #6b6560;

  /* Primary - Warm Amber */
  --primary:       #e8915a;
  --primary-hover: #f0a06e;
  --primary-pressed:#d07a48;
  --primary-dim:   rgba(232,145,90, 0.12);
  --primary-glow:  rgba(232,145,90, 0.25);

  /* Agent - Purple */
  --agent:         #9b8ec4;
  --agent-dim:     rgba(155,142,196, 0.12);
  --agent-border:  rgba(155,142,196, 0.25);

  /* Paradigm Colors - Morandi */
  --p-ab:          #7bafd4;        /* 雾蓝 — AB 实验 */
  --p-ab-dim:      rgba(123,175,212, 0.12);
  --p-biz:         #d4a34e;        /* 暖金 — 经营分析 */
  --p-biz-dim:     rgba(212,163,78, 0.12);
  --p-gray:        #9b8ec4;        /* 淡紫 — 版本灰度 */
  --p-gray-dim:    rgba(155,142,196, 0.12);
  --p-data:        #6baa8e;        /* 灰绿 — 数据分析 */
  --p-data-dim:    rgba(107,170,142, 0.12);
  --p-wave:        #c97b7b;        /* 暗红 — 波动分析 */
  --p-wave-dim:    rgba(201,123,123, 0.12);

  /* Semantic */
  --success:       #5bb98c;
  --success-dim:   rgba(91,185,140, 0.12);
  --warning:       #d4a34e;
  --warning-dim:   rgba(212,163,78, 0.12);
  --error:         #c97b7b;
  --error-dim:     rgba(201,123,123, 0.12);
  --info:          #7bafd4;
  --info-dim:      rgba(123,175,212, 0.12);

  --shadow:        rgba(0,0,0, 0.4);
}
```

### 亮色模式

```css
:root[data-theme="light"] {
  --bg:            #f8f6f3;
  --surface:       #ffffff;
  --surface-2:     #f2eeea;
  --surface-3:     #e8e4df;
  --border:        #ddd8d2;
  --border-light:  #ccc7c0;

  --text:          #1a1a1a;
  --text-dim:      #6b6560;
  --text-muted:    #9e9890;

  --primary:       #c27040;
  --primary-hover: #a85e35;
  --primary-pressed:#9a5530;
  --primary-dim:   rgba(194,112,64, 0.08);
  --primary-glow:  rgba(194,112,64, 0.15);

  --agent:         #7b6fa8;

  --p-ab:          #4a8ab5;
  --p-biz:         #a07d30;
  --p-gray:        #7b6fa8;
  --p-data:        #3d8c65;
  --p-wave:        #a85555;

  --success:       #3d8c65;
  --warning:       #a07d30;
  --error:         #a85555;
  --info:          #4a8ab5;

  --shadow:        rgba(0,0,0, 0.06);
}
```

### 圆角

```css
--radius:    12px;  /* 卡片、面板 */
--radius-sm: 8px;   /* 按钮、输入框 */
--radius-xs: 6px;   /* 标签、badge */
```

---

## 4. 布局尺寸 / 字体 / 动画

### 布局尺寸

| 组件 | 尺寸 |
|---|---|
| Global Bar | 高 52px |
| Context Bar / 面包屑 | 高 44px |
| Sidebar (workspace) | 宽 280px |
| Sidebar (admin) | 宽 220px，可折叠到 56px |
| Right Panel | 宽 320px |
| 通知 Dropdown | 380 × 480px |
| 搜索 Modal | 600 × 500px |

### 响应式断点

```css
@media (max-width: 1100px) { /* 隐藏 RightPanel */ }
@media (max-width: 900px)  { /* 登录页双栏 → 单栏 */ }
@media (max-width: 800px)  { /* 隐藏 Sidebar，移动端 */ }
```

### 字体

```css
--font-head: 'Sora', sans-serif;
--font-body: 'DM Sans', sans-serif;
--font-mono: 'JetBrains Mono', monospace;
```

### 动画

| 名 | 用途 | 参数 |
|---|---|---|
| fadeUp | 元素入场 | 0.5s ease, translateY(16px→0) |
| slideDown | Warning banner | 0.3s ease, translateY(-100%→0) |
| shimmer | 骨架屏 | 1.5s ease-in-out infinite |
| pulse | 在线点 | 1.5s ease-in-out infinite |
| blink | 流式光标 | 1s step-end infinite |
| bounce | 思考三点 | 1.4s infinite, translateY(0→-8px) |

### 背景三级（D138 设计稿规则保留）

| 层级 | 适用页面 | 网格 | Orb 光斑 |
|---|---|---|---|
| L3 展示型 | introduce / login / guide | opacity ≤0.10 | 2-3 个 opacity ≤0.10 |
| L2 导航型 | dashboard | 无 | 1 个顶部 opacity ≤0.04 |
| L1 工具型 | workspace / admin | 无 | 无 |

---

## 5. WebSocket 协议 v2

### 端点

```text
WS /api/v1/ws/conversations/{conversation_id}
认证: subprotocol ['bearer', '{access_token}']  (D46 P2 改造，目前仍 query)
```

### 客户端 → 服务端事件

```json
// 用户消息
{
  "type": "user_message",
  "content": "...",
  "model": "azure_openai/gpt-5.4",
  "referenced_file_ids": ["uuid"],
  "referenced_skill_ids": ["uuid"],
  "kb_citations": [{"title":"...","source":"...","snippet":"...","score":0.85}]
}

// 中止生成（D42）
{ "type": "abort" }
```

### 服务端 → 客户端事件

```json
// 回执
{ "type": "user_message_ack", "message_id": "uuid" }

// 思考状态
{ "type": "agent_typing", "status": "start | stop" }

// 流式内容（多次）
{ "type": "agent_message", "message_id": "uuid", "content": "chunk" }

// 工具调用（D38–D39）
{ "type": "tool_call_start", "tool_call_id": "uuid", "tool_name": "...", "arguments": {...} }
{ "type": "tool_call_done",  "tool_call_id": "uuid", "result": {...}, "success": true }

// 完成
{ "type": "agent_message_done", "files_created": [{...}] }

// 文件创建（中途）
{ "type": "file_created", "file": {...} }

// 引用来源（D49）
{ "type": "citations", "message_id": "uuid", "items": [{"title":"...","source":"...","snippet":"...","score":0.9}] }

// 推荐追问
{ "type": "suggested_followups", "message_id": "uuid", "questions": ["..."] }
```

### 连接行为约束

- 重连指数退避：1s, 2s, 4s, 8s, 16s, 30s 上限（D45）
- 重连成功 → toast "连接已恢复"
- 断开期发消息 → inline 错误条 + 队列暂存最后 5 条（D45）
- Tool calling 循环最多 5 轮（D38）
- 单 tool 超时 30s 标记 `timeout`（D39）
- 对话历史 context 20 条

---

## 6. 错误码命名规范

格式：`UPPER_SNAKE_CASE`，按业务域前缀组织

| 错误码 | 触发场景 |
|---|---|
| `INVALID_CREDENTIALS` | 密码错误 |
| `ACCOUNT_DISABLED` | 账号被禁用 |
| `SUPER_ADMIN_REQUIRES_FEISHU` | super_admin 用密码登录 |
| `FEISHU_ACCOUNT_NOT_WHITELISTED` | 飞书账号未授权 |
| `LOGIN_RATE_LIMITED` | 登录频率超限（429） |
| `OPEN_REGISTER_DISABLED` | 注册被关闭（D83） |
| `TOKEN_EXPIRED` | access_token 过期 |
| `TOKEN_REFRESH_FAILED` | refresh_token 无效 |
| `PERMISSION_DENIED` | 无权限（普通 admin 改 super_admin 字段等） |
| `RESOURCE_NOT_FOUND` | 通用 404 |
| `FILE_TOO_LARGE` | 文件超 upload_max_size_hard_cap_mb |
| `TOOL_TIMEOUT_30s` | Tool call 30s 未返回 |
| `LLM_BUDGET_EXCEEDED` | 月度预算超限（D126） |
| `KB_SYNC_FAILED` | 知识库同步失败 |
| `GUIDE_LOAD_FAILED` | 使用指南加载失败 |
| `LAST_SUPER_ADMIN_PROTECTED` | 最后一个 super_admin 不能降级/删除 |

### 客户端展示约定

- ErrorState 内显示错误码 monospace 小字（用户复制报障用）
- toast 显示中文文案，错误码作为辅助识别

---

## 7. API 响应规范

```json
// 成功
{
  "code": 0,
  "message": "success",
  "data": { ... } | [ ... ] | { "items": [...], "total": N, "page": 1, "page_size": 15 }
}

// 错误
{
  "code": 40001,
  "message": "Invalid credentials",
  "error_code": "INVALID_CREDENTIALS",
  "data": null
}
```

- HTTP 状态码：`200` 成功 / `400/401/403/404/409/429/500` 按 REST 约定
- 业务错误码：HTTP 4xx 时 `error_code` 必填
- 分页响应统一含 `total / page / page_size`

---

## 8. v3 状态设计规范

### EmptyState（引导型空状态）

结构：`场景插画（CSS 构建）+ 标题 + 引导文案 + CTA 按钮`

| 场景 | 页面 | CTA |
|---|---|---|
| 无历史任务 | Dashboard | "选择上方一个范式开始" |
| 无文件 | Workspace Files | "拖拽文件或点击上传" |
| 无定时任务 | /scheduled-tasks | (整 Section 隐藏) |
| 知识库未配置 | Workspace 知识库 | "联系 @gongyunhe 配置" |

### Skeleton（骨架屏）

- 不用 spinner，用骨架屏 + shimmer 动画
- 骨架色：`var(--surface-2)` 底 + `var(--surface-3)` shimmer
- 卡片 / 列表 / 段落各自独立形状

### WarningBanner（顶部 slideDown 滑入，D26）

| 级别 | 颜色 | 可关闭 | 触发事项 |
|---|---|---|---|
| error | --error | ❌ | WS 断开 / Token 即将耗尽 |
| warning | --warning | ✅ 24h dismiss | Token 不足 / 同步失败 / 经验待审 |
| info | --info | ✅ 24h dismiss | 系统维护 / 公告 / 公共任务待审 |

### ErrorState（阻塞型）

替换内容区域，提供恢复路径：

```text
[图标] 文案
错误码（monospace --text-muted）
[CTA1] [CTA2]
```

### Tool Calling 状态（D39）

| 状态 | 边框色 | Badge | 操作 |
|---|---|---|---|
| executing | --warning | ⏳ 执行中 | — |
| done | --success | ✅ 已完成 | — |
| error | --error | ❌ 失败 | [🔁 重试] [📋 复制错误] [🚩 反馈] |
| timeout | --info | ⏱ 超时 | [🔁 重试] [📋 复制错误] [🚩 反馈] |

---

## 9. 文件优先存储约束（G3）

### 顶层目录约定

```text
agents/    # 内置 Agent（5 个）
skills/    # 本地 Skill（25 个）
files/     # 公共文件（4 个）
users/     # 用户数据（每用户一子目录）
tasks/     # 任务数据（每任务一子目录）
```

### 数据双向一致性

- 任务创建：写 `tasks/{tid}/meta.json` + 写 `users/{owner}/tasks/index.json` + 更新 SQLite cache，事务保证
- 协作者加入：写 `tasks/{tid}/collaborators.json` + 写 `users/{collab}/tasks/index.json` + 更新 cache
- 任意一边失败需回滚（D139）

### Source of truth 优先级

```text
1. 文件系统（.json/.jsonl）        ← source of truth
2. SQLite cache (.cache/index.db)   ← 查询索引，可重建
3. Frontend store (Zustand)         ← UI 状态
```

启动时若 SQLite 缺失：扫描文件系统全量重建。

### 索引结构（SQLite cache）

仅存查询所需的字段映射，不存原始内容：

- `tasks_index(id, owner_id, paradigm, status, updated_at, file_count)`
- `users_index(id, email, auth_role, status, last_login_at)`
- `messages_index(id, conversation_id, task_id, role, created_at)`
- `files_index(id, task_id, file_type, format, is_pinned, created_at)`
- `experience_cards_index(id, task_id, agent_id, status, created_at)`
- `tool_calls_index(id, conversation_id, task_id, tool_name, status, created_at)`

任何索引行漂移可由 `scripts/rebuild_index.py` 局部重建。

---

## 引用决策

本文档所有约束来自 `design_decisions.md` 中的：
- G1 / G2 / G3（全局约束）
- D7–D11（Tab 与 Section 顺序）
- D26（告警条规则）
- D37（react-markdown 统一）
- D38–D39（Tool Calling 状态）
- D45–D46（WebSocket 健壮性）
- D85–D89（角色体系）
- D101–D110（admin 权限 gate）
- D134–D139（文件优先存储）

具体决策细节请直接查阅 [`../design_decisions.md`](../design_decisions.md)。
