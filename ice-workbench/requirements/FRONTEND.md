# FRONTEND — 前端开发需求

> 决策原文见 [`../design_decisions.md`](../design_decisions.md)，全局约束见 [`SHARED.md`](SHARED.md)

## 目录

1. [跨页基础设施](#1-跨页基础设施)
2. [全产品要清理的内容](#2-全产品要清理的内容)
3. [页面级需求](#3-页面级需求)
4. [实施优先级总览](#4-实施优先级总览)

---

## 1. 跨页基础设施

### 1.1 TopNav 双层 Shell（D28 / D64 / D101 / D133）

**单组件适配 4 种 mode**：

| mode | 用途 | 结构 |
|---|---|---|
| `dashboard` | Dashboard 首页 | Logo + 搜索 ⌘K + 通知 + 主题 + 用户胶囊 |
| `workspace` | Workspace + Agent 详情 + Create-task + Scheduled + Guide | ← 返回 + 面包屑 / Agent 抽屉 + 操作按钮 |
| `admin` | 管理后台 | Logo + 面包屑 + 主题 + 通知 + 用户胶囊 |
| `introduce` | 产品介绍 | Logo + 锚点导航 + 主题 + [立即体验] |

**Agent 抽屉**（workspace mode 内）：

- 收起态显示：← 返回 / 任务名 · Agent名 · 范式 · 在线点
- 点击展开：Skills 列表 + 经验数 + 满意度
- 复用 Workspace D29 落地

**删除自写顶栏**：

- `WorkspacePage.tsx:180-215`（D28）
- `AdminLayout.tsx:38-59`（D101）
- `IntroducePage.tsx:172-192`（D98）
- `ScheduledTasksPage` / `CreateTaskPage` / `AgentDetailPage` / `GuidePage` 等也都改用 TopNav

### 1.2 NotificationCenter 真实化（D29）

- **删除** `MOCK_NOTIFICATIONS`
- 改读 `GET /notifications`（轮询 30s 或 SSE 推送）
- 通知类型：`experience` / `task-fail` / `collaboration` / `token-alert` / `system` / `public-task-pending`
- 全部已读 → `POST /notifications/read-all`
- 单条已读 → `POST /notifications/{id}/read`
- 跳转：每类型有 `action_url` 字段引导

### 1.3 useFileUpload Hook（D52）

新建 `frontend/src/hooks/useFileUpload.ts`：

- 统一处理：上限校验（`upload_max_size_mb` / `_hard_cap_mb`）/ 进度 / 错误重试 / 引用联动 / 取消
- 调用方：Sidebar / ChatInput / 拖拽到消息流（D52）
- 文件超限不静默丢弃，toast "文件 {name} 超过 {limit}MB 上限，无法上传"
- 上传中：inline 进度条（每文件一行 + percent + 取消）
- 进度通过 NotificationCenter 累积显示（"3 个文件上传中... 67%"）

### 1.4 useWebSocket Hook（D45 / D46）

升级现有 hook：

- 重连指数退避：1s, 2s, 4s, 8s, 16s, 30s 上限
- 重连成功 → toast "连接已恢复"
- 连续 N 次失败 → 触发顶部告警条 error 级
- 断开期发消息 → 队列暂存最后 5 条 + inline 错误条
- 协议版本号字段 `protocol_version`（前后端协商）
- token 改 subprotocol 传输（P2 工单）

### 1.5 useTheme Hook（D 全局主题）

- localStorage key 统一为 `ice-theme-v3`（删 introduce 的独立 key）
- 应用 `<html data-theme="dark|light">`
- 与 IntroducePage / Workspace / Admin 全局共享

### 1.6 全局 Modal / Toast 库

新建 `frontend/src/components/feedback/`：

- `<ConfirmModal>` 替换所有 `confirm()` 原生调用（删除/归档/敏感操作）
- `<ErrorModal>` v3 ErrorState 模式（图标 + 错误码 + CTA）
- `<Toast>` 统一 toast 体系（success / warning / error / info）

被影响位置：[ScheduledTasksPage], [WorkspaceSettings], [AdminExperienceCards], [AdminKnowledgeBases] 等使用 `confirm()` 处。

### 1.7 SuperAdminGuard（D88 / D102）

新建 `frontend/src/components/SuperAdminGuard.tsx`：

- 整页 gate：`/admin/settings` 完整路由
- 字段级 gate：`/admin/users` 的 `auth_role` 编辑控件
- 非 super_admin 整页访问 → 跳 `/admin` + toast `"该页面仅超级管理员可访问"`

### 1.8 ⌘K 全局搜索（D 全局）

- 复用现有 `<SearchModal>`，按 D 锁定 600×500
- 搜索范围：任务 / Agent / Skill / 文件 / 知识库
- 类别 filter chips
- 键盘导航 ↑↓ / Enter / Esc
- 全部接 `GET /search?q=&type=`（已有）

### 1.9 markdown 渲染统一（D37）

新建 `frontend/src/components/MarkdownRenderer.tsx`：

- `react-markdown` + `remark-gfm`
- `react-syntax-highlighter`（代码块 + 复制按钮）
- `DOMPurify.sanitize` 清洗
- 外链 `target="_blank" rel="noopener"`
- 内链 `#锚点` 平滑滚动

替换位置：

- [`ChatMessages.tsx`](#) 删除 `escapeAndFormat` + `dangerouslySetInnerHTML`
- [`FilePreview.tsx`](#) 复用
- [`GuidePage.tsx`](#) 复用

---

## 2. 全产品要清理的内容

### 2.1 Mock 数据（违反 G1）

| 位置 | 处置 |
|---|---|
| `DashboardPage.tsx` `MOCK_KB_DATA` | 删除，改读 `GET /workspaces/{wsid}/knowledge-bases` |
| `DashboardPage.tsx` `MOCK_PUBLIC_TASKS` | 删除，改读 `GET /tasks/public` 或 `/commons?type=task` |
| `DashboardPage.tsx` `MOCK_SCHEDULED_TASKS` | 删除，改读 `/scheduled-tasks` 真实数据 |
| `DashboardPage.tsx` `MOCK_MY_TEMPLATES / MOCK_PUBLIC_TEMPLATES` | 删除，改读 `/templates` |
| `AdminDashboard.tsx` `MOCK_AGENT_RANKS` | 删除，改读 `GET /admin/agents/ranking?period=` |
| `AdminPublicTasks.tsx` `MOCK_TASKS` | 删除，对接真实接口 |
| `AdminAgents.tsx` "测试对话" `[模拟响应]` | 删除，改用 `POST /agents/{aid}/test-chat` |
| `AgentDetailPage.tsx` `MOCK_AGENT/SKILLS/MEMORIES/EXPERIENCES/TIMELINE` | 删除，对接 6 个新接口 |
| `TopNav.tsx` `MOCK_NOTIFICATIONS` | 删除，改读 `GET /notifications` |
| `LoginPage.tsx` `alert("飞书 OAuth 即将上线")` | 删除，真实 OAuth 接入 |

### 2.2 重复 / 冲突路由

- `/register` → 删除（D83）
- `/admin/costs` → 删除（D125 合并到 `/admin/usage`）
- `WorkspaceSettings` 的 scheduled tab → 删除（D59 统一到 `/scheduled-tasks`）
- DashboardPage 顶部 `[概览 / 定时任务]` Tab → 删除（D7）

### 2.3 配色升级

全产品 cyan 旧色（`#00d4ff` / `var(--cyan)` / `var(--cyan-dim)`）替换为：

- 主操作 → `--primary` `#e8915a`
- 链接 hover → `--primary-hover` `#f0a06e`
- Logo 渐变 → `--primary` → `--agent`
- 用户气泡 → `linear-gradient(135deg, #c27040, #e8915a)`
- 范式色全替换为 v3 莫兰迪低饱和系（见 SHARED.md §3）

ECharts 全部图表配色按 D128 统一。

### 2.4 配置常量更新

- 文件上传 `2 * 1024 * 1024` → 删除前端硬编码，改读后端 `upload_max_size_mb` 配置
- LocalStorage theme key 统一为 `ice-theme-v3`（旧 `ice-theme` 迁移）

---

## 3. 页面级需求

### 3.1 `/login` 登录页 · D1–D6

| 决策 | 改动 |
|---|---|
| D1 | 飞书 OAuth 主推 — 主按钮 + 真实接入（替代 alert） |
| D2 | 账号 + 密码登录保留为辅 |
| D3 | 测试快捷登录收窄到 **张明远 + 李思涵** 2 个，折叠 + "仅测试可见" 标识 |
| D4 | 左栏极简：Logo + 一句话 `AI 数据工作流工作台` + 三步循环动画（用户气泡→ToolCall→报告） |
| D5 | `/login` 是新用户首次落地页 |
| D6 | 文案 + 错误状态 + 配色 + 主题切换 + 联系 @gongyunhe |

新增组件：

- 三步循环动画 CSS（不用视频/Lottie）
- 飞书 OAuth 跳转中蒙层
- v3 ErrorState 错误展示

### 3.2 `/dashboard` Dashboard · D7–D27

**整页大重构**。Section 顺序（D9）：

```text
1. 顶部告警条（仅有事时显示）
2. 一行欢迎语
3. ⚡ 快速开始 — 5 范式卡 + [📋 模板] [+ 开放任务]（D15-D18）
4. 📋 我的任务 — 卡片 Grid + 三点菜单 + 搜索/范式/排序 + 底部归档区（D19-D24）
5. 🌐 团队资产 — 公共任务 / 知识库 / 资产摘要胶囊（D10）
6. 📊 我的工作概况 — 折叠抽屉，3 指标 + sparkline（D25）
7. ⏱ 定时任务摘要 — 1 行只读，无任务则隐藏（D27）
```

任务卡设计（D19）：

```text
范式色顶线
任务名               [⋯ 三点菜单]
[范式 tag] · 🤖 经营洞察 Agent
💬 "上周新版本留存比上月..." (D23)
⏱ 2 小时前 · 📄 3 文件 · 👥 2 协作
```

三点菜单：归档 / 共享到公共区 toggle / 重命名 / 删除（D19）。

来源差异：协作任务右上角 👥 角标（D20）。

筛选条：[范式 ▾] [排序 更新时间/创建时间/文件数/协作者数 ▾] [🔍 搜索]（D21）

### 3.3 `/workspace/:taskId` Workspace · D28–D62（35 决策）

**最大重构**。改动跨多组件：

#### 3.3.1 顶栏（D28-D30）

- 删除自写 nav，改用 TopNav workspace mode
- Agent 抽屉显示 Skills + 经验数 + 满意度
- 工具按钮：← / Agent 抽屉 / 📤导出 / 🔗分享 / ⚙设置 / 🌓 / 🔔 / 用户▾

#### 3.3.2 侧栏（D31-D32）

- 文件上传走 `useFileUpload` hook（D52）
- 删除按钮二次确认弹 ConfirmModal
- 公共文件分组**不显示** [×] 删除按钮（D53）

#### 3.3.3 ChatHeader（D36）

- 仅显示当前模型 + [💾 导出对话] [🗑 清空]
- 删除冗余 Agent 头像（与顶栏重复）

#### 3.3.4 RightPanel（D33-D35）

改为 4 Tab：[📄 文件] [⚙ 配置] [🤖 Agent] [👥 协作]

- 📄 文件 Tab：复用 FilePreview，**支持 csv/txt/json/sql/py 高亮**（D34）
- ⚙ 配置 Tab：范式 / 状态 / 模型 / 初始 Prompt
- 🤖 Agent Tab：当前 Agent + Skills + 最近经验卡片 3 条 + "→ Agent 详情"
- 👥 协作 Tab：协作者列表 + 邀请

文件预览顶部按钮：[⬇ 下载] [✏ 重命名] [✕]（D35）

HTML sandbox 改为 `sandbox=""`（不再 allow-scripts，D34）

文件 > 500KB 黄条提示（D34）

#### 3.3.5 ChatMessages（D37 / D47-D49）

- 切换到 `MarkdownRenderer` 组件
- 删除 `escapeAndFormat` 和 `dangerouslySetInnerHTML`
- 反馈条 `[👍][👎][✨]` hover 显示（D47）
- 沉淀经验 emoji 改 ✨（D48）
- CitationBar 默认展开第 1 条（D49）

#### 3.3.6 ToolCallCard（D38-D39）

- 工具中文名从 `Skill.name` 取（D38）
- "查看完整参数" 折叠展开
- 错误状态显示文本 + 错误码
- 失败按钮组 [🔁 重试] [📋 复制错误] [🚩 反馈]
- 增加 `timeout` 状态（30s）

#### 3.3.7 ChatInput（D40-D44）

- 文件 Tab 顺序：[工作文件] [公共文件] [知识库]（D40）
- ModelSelector 提到主输入框右上角（D41）
- 流式输出中 [▶] → [⏸ 暂停生成]（D42）
- placeholder 按 paradigm 区分（D43）
- 已引用上限 10 个（D44）
- 删除 `if (file.size > 2*1024*1024) continue` 静默忽略

#### 3.3.8 ShareModal（D50-D51）

完全重做：

- 邮箱/姓名/工号搜索（接 `GET /users/search?q=`）
- 用户卡片显示头像 + 姓名 + 角色 + 团队
- "我（创建者）"在列表中（不可移除）
- 邀请链接生成（D50）
- 移除带 ConfirmModal 二次确认
- error 改 v3 ErrorState

#### 3.3.9 KnowledgeBrowser（D54-D58）

- 飞书 + RAG 合并为统一"📚 知识库" Section
- 多 KB 同时展开（`Set<string>`）
- 文档点击进右栏 📄 文件 Tab（删除覆盖层 modal）
- 文件预览顶部加 [📎 引用此文档]
- 同步 toast 反馈
- KB 全空显示引导

#### 3.3.10 WorkspaceSettings（D59-D62）

- 删除 scheduled tab
- 归档改 v3 ConfirmModal + `useNavigate('/dashboard')`
- 加"更换 Agent"（同范式可换）
- 切换范式仅 admin 在后台（用户视角不显示）

### 3.4 `/agent/:agentId` Agent 详情 · D63–D70

按角色拆分（普通用户区 + admin 区）：

```text
═ 全用户可见 ═
- Agent 信息卡 + 主 CTA [+ 用此 Agent 创建任务] (D65)
- 能力（绑定 Skills）
- 已审批经验卡片（仅 approved，只读）(D66)
- 最近使用此 Agent 的公共任务（D69）

═ 仅 admin 可见 (D70 整 Section 不渲染) ═
- 🛡 管理区
  - 内嵌 Prompt 编辑器 + 测试对话沙盒 (D68)
  - 草稿经验卡片审批
  - Agent 记忆管理
  - 进化日志
```

删除全部 mock（D63）：MOCK_AGENT/SKILLS/MEMORIES/EXPERIENCES/TIMELINE。

### 3.5 `/create-task` 完整工坊 · D71–D76

3 Step 长表单（D71）：

```text
Step 1 · 选择起点
  [📋 从模板] [⚖ 范式 ▾] [+ 开放任务]

Step 2 · 任务基础
  名称 / 描述 / 💬 初始 Prompt（按 paradigm placeholder）

Step 3 · 高级配置（默认折叠 D73）
  ▾ 🤖 Agent 与 Skills
  ▾ 📂 预上传文件
  ▾ ⏱ 定时执行 (cron + 推送渠道) - D74
  ▾ 👥 协作者

底部 [☑ 创建后立即开始对话] [创建任务 →]
```

接收 query：`?agentId=&paradigm=&template=`（D72）

模板选择器（D75）：[我的模板 / 公共模板] tab + 选中后预填全字段。

### 3.6 `/scheduled-tasks` 定时任务 · D77–D82

- **删除** "任务模板" tab（D77）
- 顶部操作条：状态 chip + Agent/任务下拉 + 搜索 + [+ 创建]（D78）
- 接收 `?taskId=` 参数 filter（D78）
- 创建定时任务 modal：选已有 task → cron + prompt + 推送（D79）
- 任务卡操作：[▶ 立即执行] [⏸ 暂停/恢复] [✏ 编辑] [🗑 删除带二次确认]（D80）
- 历史 inline 详情（D81）：完整 prompt / tokens / 工具调用 / 错误 / 产出
- cron 自动可读（cronstrue）+ 常用预设按钮（D82）

### 3.7 `/register` 删除 · D83-D84

- 删除路由 + 文件
- 登录页底部文案改 "联系 @gongyunhe 申请"

### 3.8 `/guide` 使用指南 · D90–D95

- TopNav workspace mode + 面包屑（D90）
- 双栏布局：左 280px TOC + 右内容（D91）
- 桌面端 TOC 常驻，移动端抽屉
- TOC 自动从 markdown 提取 h2/h3
- 内容顶部信息条：[最后更新] [✉ 反馈] [🖨 打印]（D92 / D95）
- 关键词搜索高亮命中
- ReactMarkdown 升级（D90）
- 加载/错误状态升级 v3（D94）
- 编辑权限：admin 在 `/admin/files` 编辑（D93）

### 3.9 `/introduce` 产品介绍 · D96–D100

简化为业务介绍（D96）：

- 删除：模块 status / Roadmap / 架构图 / 技术栈 / Legend / Footer "PRD"
- 保留：Hero / 核心概念 / 功能特性（去状态）
- 新增：4 个实际场景案例（D97），从 `GET /agents/public` 读真实 Agent
- 强 CTA [立即体验 →] + Hero 4 数字真实化（D99）
- 删除自有 nav + theme，统一 TopNav + useTheme（D98）
- 配色升级 v3 范式色（D100）

### 3.10 管理后台 14 页

#### `/admin` AdminLayout 整体 · D101 / D124 / D132 / D133

- 删除自写 topbar，统一 TopNav workspace mode
- Sidebar 4 分组（D132 完整版）
- Sidebar 折叠按钮（D133）
- super_admin 专属项加 🛡 图标

#### `/admin` 概览 · D103-D105

- 删除 `MOCK_AGENT_RANKS`
- stats 加 sparkline + 时间筛选 chip
- 顶部"🚨 待处理事项"卡片
- super_admin 专属"全局开关"快捷面板

#### `/admin/users` · D106-D110

- `auth_role` 三级 chip + 编辑仅 super_admin
- 飞书绑定列 + [🔗 邀请] 按钮
- 创建用户双 Tab：白名单（默认）/ 临时密码
- 批量操作 + 角色/团队 select 化
- 删除/重置密码 v3 化

#### `/admin/agents` · D111-D112

- 测试对话改真实接口
- publish_status 收敛 2 种
- 创建/编辑跳转 `/admin/agents/:id/edit`

#### `/admin/agents/:id/edit` · D113-D114

- 4 Tab：[基础] [Skills 绑定] [测试对话] [经验/记忆/日志]
- Prompt 版本历史 + 回滚 + diff
- 保存敏感修改 ConfirmModal

#### `/admin/skills` + `/admin/paradigm-presets` · D115-D117

- 范式预设拆出新页 `/admin/paradigm-presets`
- AdminSkills 仅管 Skill CRUD
- tool_schema 加 JSON validator + 格式化按钮
- "测试运行 Skill" 按钮

#### `/admin/experience-cards` · D118

- Agent Tab 分组（全部 + 6 内置）
- 状态多选筛选 + 批量审批
- 驳回原因输入
- "原文对话"列跳转 workspace
- delete 改 v3 ConfirmModal

#### `/admin/knowledge-bases` · D119

- delete 改 ConfirmModal
- 同步 toast + 同步日志查看
- 同步频率配置（手动/每日/每周）
- source_type 收敛 2 种
- 加 KB 编辑

#### `/admin/files` · D120

- 加 [+ 上传文件] 按钮
- 文本类（md/txt）内容编辑器
- `is_pinned` 字段 + UI 标识
- 类型 / 来源筛选

#### `/admin/templates` · D121

- 字段扩展（agent / skills / file_seeds / has_schedule / visibility / status / reject_reason）
- 模板预览功能
- 审核流（draft → approved/rejected）
- "从任务生成模板"快捷入口

#### `/admin/public-tasks` · D122

- 删除 mock 对接真实接口
- 顶部审核制状态告警
- 审核驳回带原因
- 加"下架"操作

#### `/admin/review-center` 新增 · D123

- 顶部待办计数
- 3 Tab：经验卡片 / 公共任务 / 任务模板
- 每 sub-tab 顶部 [→ 完整管理]

#### `/admin/usage` · D125-D128

- 合并 `/admin/costs` 全部功能
- 工具条：[时间筛选] [📥 CSV] [⚙ 单价] [💰 月度预算]
- 5 Tab：日趋势 / 按模型 / 按用户 / 按 Agent / 按任务
- ECharts 配色升级 v3
- 单价配置 modal
- 月度预算 + 80%/100% 告警

#### `/admin/sql-audit` · D127-D128

- 筛选扩展：用户 / Agent / Workspace / 时间范围 / 全文搜索
- SQL hover popover 显示全文
- 详情 modal 加：用户名 / Agent / Workspace / 错误信息
- ECharts 配色 v3
- 导出 CSV

#### `/admin/settings` · D129-D131

- 整页 SuperAdminGuard
- 4 Tab：[全局开关] [LLM 模型] [系统参数] [公告管理]
- 全局开关 3 个：enable_open_register / enable_public_task_review / enable_feishu_strict_whitelist
- LLM 模型加单价字段
- 系统参数 5 组折叠 + [⟲ 恢复默认]
- 公告加 audience_scope / status / 立即发布
- 敏感修改 ConfirmModal

---

## 4. 实施优先级总览

### Phase 1 · 基础设施（P1）

跨页基础设施全部，约 9 项 hook/组件 + 配色全替换 + Mock 全清。

### Phase 2 · 核心页面（P1）

- 登录页 + 注册删除 + 三级角色 gate
- Dashboard 大重构
- Workspace 大重构（35 决策）
- Agent 详情按角色拆

### Phase 3 · 副路径页 + 后台（P1-P2）

- /create-task / /scheduled-tasks / /guide / /introduce
- 管理后台 14 页改造

### Phase 4 · 打磨（P2-P3）

- 移动端适配 / 虚拟滚动 / 批量操作 / 导出 CSV
- WebSocket subprotocol token（D46）
- Prompt 版本历史 UI 完善
- 设计稿与实现一致性 review

---

## 实现路径建议

按页面 + Phase 维度排期：

```text
W1-W2  | 基础设施 hooks + Mock 清理 + 配色 + TopNav
W3-W4  | 登录 + Dashboard + 三级角色
W5-W7  | Workspace 三块重构（含右栏 4 Tab + 协作 ShareModal + KB 重构）
W8     | Agent 详情 + Create-task + Scheduled
W9     | Guide + Introduce + Register 删除
W10-W12| 管理后台 5 组（A→E）
W13    | 移动端适配 + 打磨
```
