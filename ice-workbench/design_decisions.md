# ICE Data Workbench — 设计决策记录

> 按用户操作动线逐页评审，每页决策固化在此文件，可直接交付前端实现。
> 评审方法：现状卡 → 问题清单 → 决策。

---

## 页面 1 · 登录页 `/login`

**评审完成日期**：2026-05-07

### 布局

- 双栏布局，**左栏极简**（不再承担种草职责），右栏为登录卡片
- 单栏断点：≤900px 双栏 → 单栏，左栏内容上移到右栏顶部并压缩
- 背景：v3 L3 展示型（微网格 opacity ≤0.10 + 2 个暖色 orb opacity ≤0.10）
- 右上角悬浮 🌓 主题切换按钮，状态写入 localStorage

### 左栏内容（极简品牌区）

- Logo + 品牌名 `ICE Data Workbench`
- **一句话介绍**：`AI 数据工作流工作台`（不展开 4 个特性卖点）
- **产品形态缩略动画**（决策 Q3 = C）：
  极简三步循环动画，呈现"对话驱动数据流"的故事感：
  1. 用户气泡（"分析一下上周新版本的留存"）
  2. Tool Calling 卡片（执行 SQL → 完成）
  3. 报告卡片（带 sparkline）
  循环间隔 ~4 秒，使用 CSS animation + 淡入淡出，不用视频/Lottie
- 实现成本最高的选项，但承担"让人秒懂这是什么产品"的核心说服职责

### 右栏登录卡片（按视觉权重从上到下）

```text
1. 标题   "欢迎回来"
2. 副标   "选择登录方式进入工作台"
3. ┌─────────────────────────┐
   │  🪶 使用飞书账号登录     │  ← 主 CTA，飞书品牌色 #00d6b9 或保持暖色
   └─────────────────────────┘
4. ── 或使用账号密码 ──        ← 视觉降级分隔线
5. [账号 邮箱/工号]
6. [密码         忘记密码?]    ← 密码框右侧小字链接
7. [        登录工作台      ]  ← 次要 CTA，暖色 #e8915a
8. ▾ 🔧 测试快捷登录            ← 默认折叠
   展开后：
   ┌──────┐  ┌──────┐
   │ 张明远│  │ 李思涵│        ← 头像 + 姓名 + 角色
   │  PM  │  │ 数分 │
   └──────┘  └──────┘
   "仅测试环境可见"  ← --text-muted 小字
9. 没账号？创建 · 联系 @gongyunhe
```

### 登录方式 · 优先级

| 优先级 | 方式 | 视觉权重 | 触发 |
|---|---|---|---|
| 1（主推）| 飞书 OAuth | 大尺寸主按钮 | OAuth 跳转 |
| 2 | 账号 + 密码 | 标准表单 | `POST /auth/login` |
| 3（仅测试）| 无密码快捷登录 | 折叠 + 低饱和 | `POST /auth/login-by-account` |

### 测试快捷登录账号

**仅 2 个**：

- 张明远 · 产品经理 · 增长团队（PM 视角）
- 李思涵 · 数据分析师 · 商业化团队（数据视角）

> admin 与王子轩账号必须走密码或飞书登录。

### 飞书 OAuth 体验细节

- **跳转期**：登录卡片置 loading 蒙层 + spinner + "正在跳转飞书..."
- **失败回跳**：回到 `/login`，使用 v3 ErrorState 模式显示错误（图标 🔒 + warning-bg + 错误码小字）
- **首次登录**：**白名单制** — 飞书账号需要管理员先在 `/admin/users` 中预录入，未录入则提示"账号未授权，请联系 @gongyunhe 申请"

### 错误状态 · v3 ErrorState 模式

| 场景 | 图标 | 背景色 | 文案 | CTA |
|---|---|---|---|---|
| 密码错误 | 🔒 | warning-bg | 账号或密码错误 | 重新输入 / 忘记密码 |
| 账号被禁用 | ⛔ | error-bg | 账号已被禁用，请联系 @gongyunhe | 联系管理员 |
| 飞书授权失败 | 🪶 | error-bg | 飞书授权失败 | 重试 / 改用密码登录 |
| 登录频率超限 | ⏱ | warning-bg | 登录尝试过于频繁，请 60 秒后重试 | （倒计时禁用按钮） |
| 飞书未授权账号 | 🚫 | warning-bg | 账号未授权使用本系统 | 联系 @gongyunhe |

错误码小字（monospace --text-muted）始终显示在文案下方，便于排查。

### 安全/技术（后端工单，前端无感知）

- Token 存储：localStorage → `httpOnly cookie`（PRD v2 P1）
- 登录频率限制：同 IP 5 次/分钟，超限返回 429 + retry_after 秒数
- 密码强度：≥8 位 + 至少含字母和数字（PRD P2，注册页时再做）
- 登录/登出/密码修改写入 `audit_log`（PRD P2）

### 配色升级（修 PRD-v3 一致性）

- 主按钮、链接、focus 边框：`--primary` `#e8915a`
- 左栏 4 个特性图标的 cyan/amber/purple/green 改为 v3 范式色：
  - `--p-ab` 雾蓝 `#7bafd4`
  - `--p-biz` 暖金 `#d4a34e`
  - `--p-gray` 淡紫 `#9b8ec4`
  - `--p-data` 灰绿 `#6baa8e`
- 背景纯灰 `#1a1a1a`，移除冷蓝调

### 联系方式

- "联系管理员" 链接的具体内容：`@gongyunhe`（飞书 / 邮箱由实现方按公司目录填，超链跳飞书消息）

### 不做的事（明确排除）

- ❌ 用户协议/隐私政策（内部工具不需要）
- ❌ "记住我"复选框（refresh_token 7 天足够）
- ❌ 验证码（飞书 OAuth + 频率限制已足够）
- ❌ 注册页营销种草（保持当前简洁）
- ❌ 4 个特性卖点（左栏改极简）

### 实现优先级

| 优先级 | 项 |
|---|---|
| P1 | 飞书 OAuth 真实接入（不再 alert） |
| P1 | Token 改 httpOnly cookie + 登录频率限制 |
| P1 | 测试快捷登录收窄到 2 个账号 + 折叠 UI + "仅测试可见" 标识 |
| P1 | v3 配色全面替换 + 主题切换器 |
| P2 | v3 ErrorState 模式 + 错误码 |
| P2 | 左栏极简 + 三步循环动画 |
| P3 | 飞书白名单后台开关（在 `/admin/users` 增加"是否允许飞书登录"字段） |

---

## 全局约束（追加于 2026-05-07）

### G1 · 用户工作页面禁止虚构数据

**适用范围**：所有 user-facing 页面（Dashboard / Workspace / Agent详情 / Create-Task / Scheduled-Tasks / Guide / Introduce）

**含义**：所有展示的 Skills / Agents / Files / 知识库 / 任务 / 模板 / 定时任务，必须是真实本地存在的资源，不允许 mock 数据占位。

**当前需要清理的 Mock 数据**：

| 位置 | 处置 |
|---|---|
| `DashboardPage.tsx` `MOCK_KB_DATA` | **删除**。改读 `KnowledgeBase` 表，未配置走空状态 |
| `DashboardPage.tsx` `MOCK_PUBLIC_TASKS` | **删除**。改读真实公共任务 API |
| `DashboardPage.tsx` `MOCK_SCHEDULED_TASKS` | **删除**。改读 `/tasks/{id}/scheduled-tasks` |
| `DashboardPage.tsx` `MOCK_MY_TEMPLATES` / `MOCK_PUBLIC_TEMPLATES` | **删除**。改读 `/admin/templates` + 个人模板表 |
| 登录页 `alert("飞书 OAuth 即将上线")` | **删除**。真实接入 |

**真实可用的数据源**：

- `agents/` 目录 — 5 个本地 Agent（data_analysis / general / know / learn / shared）
- `skills/` 目录 — 25 个本地 Skill
- `files/` 目录 — 4 篇 MD（使用指南 / AB实验规范 / 指标口径字典 / 数据分析方法论）
- `KnowledgeBase` 表（管理员录入后才有数据）
- `Task` 表（实际创建后才有数据）

**附带工单**：管理后台"知识库管理"必须先实现真实飞书/Mify 接入流程，否则 Dashboard 的"在线知识库"区永远空（P1）。

> 管理后台、设计稿/Demo、states_demo.html 等纯展示场景不受此约束。

---

## 页面 2 · Dashboard `/dashboard`

**评审进行中**。已锁定决策按议题分组列出。

### 议题 1 · 顶部 Tab + Section 顺序与分组（已锁定）

#### D7 · 去掉顶部 Tab，使用方向 A 动作优先

- **删除** 顶部 "概览 / 定时任务" Tab
- 定时任务回独立路由 `/scheduled-tasks`，从 Dashboard 底部 "⏱ 定时任务" 卡片摘要跳转
- v3 PRD "三区同屏" 精神保留

#### D8 · 统计卡片压扁

- 不再做 4 个大卡 + sparkline
- 改为横向 1 行摘要："总任务 N · 本周 M · Token 剩余 X"
- 放在页面靠后位置（不再争夺首屏黄金区域）

#### D9 · 首屏首要动作 = 创建新任务

- Section 顺序（从上到下）：
  1. 顶部告警条（仅有事时显示）
  2. 一行欢迎语
  3. **⚡ 快速开始（创建新任务）** ← 首屏黄金位
  4. 📋 我的任务
  5. 🌐 团队资产
  6. 📊 我的工作概况（统计 1 行）
  7. ⏱ 定时任务摘要

#### D10 · 团队资产 Section 内含 3 个区块（按交互价值降序）

```text
🌐 团队资产
├── 公共任务（3列 Grid）         ← 真实数据，可加入协作
├── 在线知识库（2列卡片）         ← 真实 KnowledgeBase 表数据
└── 资产摘要胶囊                  ← [🤖5 Agents] [⚡25 Skills] [📄4 公共文件]
```

#### D11 · "共享任务区" 与 "公共任务" 合并为同一概念

- 命名统一为 **公共任务**
- 数据库字段已有 `Task.is_shared`，复用
- 用户动作叫 "**共享到公共区**"，对象叫 "**公共任务**"
- "共享任务区" 这一独立 Section 删除

### 议题 2 · 公共任务的协作语义（已锁定）

#### D12 · 加入语义 = 加入协作

- 用户点击公共任务卡片的 "加入协作" → 自己被加入 `TaskCollaborator` 列表
- 多人共用**同一个 Workspace**，共享对话历史、文件、Agent 进化记忆
- 不走 fork/副本路径

#### D13 · 加入后默认权限 = collaborate

- 加入即可：与 Agent 对话、上传文件、**下载公共任务中生成的文件**
- 原创建者保留"踢人"和"降权为 readonly"能力
- 不要求双方互相确认 — 公共任务本身就是为协作公开的

#### D14 · 发布流程 = 双轨制（默认无审核 + 后台开关）

- **默认**：用户点"共享到公共区" → 立即可见，无审核
- **管理员可在 `/admin/settings` 全局开启 "公共任务审核制"** → 切换为 PRD 原设计的 draft → approved 流程
- 管理员始终保留对公共任务的"下架"能力（`/admin/public-tasks`）

### 议题 3 · 创建新任务区（已锁定）

#### D15 · 三档创建入口 · 方向 A

```text
⚡ 快速开始

┌─── 选择工作范式 ────────────────────────────────────┐
│ ┌──────┬──────┬──────┬──────┬──────┐               │
│ │⚖     │📈    │🔌    │📊    │🔥    │               │
│ │AB实验 │经营分析│版本灰度│数据分析│波动分析│               │
│ │一句话 │一句话 │一句话 │一句话 │一句话 │               │
│ └──────┴──────┴──────┴──────┴──────┘               │
│                                                    │
│   [📋 从模板创建]    [+ 开放任务]   ← 次级，小一号   │
└────────────────────────────────────────────────────┘
```

- 5 范式卡片为主操作（视觉权重最高）
- 模板 / 开放任务并列为次级按钮，**删除"或者"分隔线**
- 范式卡描述简化为一句话

#### D16 · 范式卡 Skill Tag = Hover 浮现

- 默认卡片只显示：图标 + 范式名 + 一句话描述
- Hover 时显示 Tooltip 列出该范式预绑定的 4 个 Skills（保留信息但不占首屏空间）
- Tooltip 内容来源：从 `paradigm_presets` 表读，避免硬编码

#### D17 · 模态弹窗增强 · 加初始 Prompt + "立即开始"勾选

```text
[任务名称 *           ]
[任务描述（可选）       ]
─────────────────────
💬 初始 Prompt（可选）
[多行文本框，placeholder："例如：分析上周新版本的留存指标变化..."]
─────────────────────
☑ 创建后立即开始对话    ← 默认勾选
[(开放任务) Agent 选择]
─────────────────────
[需要更多配置？ → 完整创建页]   ← 跳 /create-task
[取消] [确认创建]
```

**行为**：

- 勾选"立即开始" + 填了初始 Prompt → 创建任务后自动跳转 workspace 并发送第一条消息
- 勾选"立即开始" + 未填 Prompt → 跳转 workspace，不自动发消息
- 不勾选 → 创建任务，回到 Dashboard（任务出现在"我的任务"列表）

#### D18 · Dashboard 入口 vs `/create-task` 完整页 = 跳转链（C 方案）

- Dashboard 模态承担 **80% 快速创建场景**：名称 + 描述 + 初始 Prompt + Agent 选择
- 模态底部 "需要更多配置？ →" 跳转 `/create-task` 完整页
- `/create-task` 完整页保留，承担 **20% 复杂场景**：定时任务配置、Skill 显式绑定、文件预上传、模板深度定制
- 两个入口共享同一份 `createTask` API

### 议题 4 · 我的任务区（已锁定）

#### D19 · 任务卡信息升级

```text
┌─────────────────────────────────────────┐
│▔▔▔▔▔▔▔▔▔▔ 范式色顶线 ▔▔▔▔▔▔▔▔▔▔│
│                                         │
│ 任务名                       [⋯ 三点菜单]│
│ [范式 tag] · 🤖 经营洞察 Agent           │
│                                         │
│ 💬 "上周新版本留存比上月..."  ← 最后对话摘要 │
│                                         │
│ ⏱ 2 小时前  ·  📄 3 文件  ·  👥 2 协作 │
└─────────────────────────────────────────┘
```

**字段**：

- 顶线：范式色
- 标题行：任务名 + 三点菜单
- 副标题行：范式 tag + Agent 名（从 `Workspace.agents[0].name` 取，1 行限定）
- **最后对话摘要**：截断到 50 字符；空对话时显示"还未开始对话"
- meta 行：⏱ 相对时间 / 📄 文件数 / 👥 协作者数

**三点菜单**：

- 📂 归档
- 🔗 共享到公共区 / ✓ 已共享（toggle）
- ✏ 重命名
- 🗑 删除（带二次确认）

#### D20 · 来源差异 = 卡片右上角小角标（A 方案）

- "我创建的"任务：无角标
- "我协作的"任务（即从公共任务加入的）：右上角 👥 小图标，鼠标悬停 tooltip：「协作者：来自 张明远」
- 不再做"我创建的 / 我协作的"filter chip — 角标已足够辨识

#### D21 · 顶部操作条（精简版）

```text
📋 我的任务（共 N 个）  [范式：全部 ▾]  [排序：更新时间 ▾]  [🔍 搜索任务名]
```

**保留 3 个控件**：

- 范式 chip：5 范式 + 开放 + 全部
- 排序 chip：**更新时间 / 创建时间 / 文件数 / 协作者数** 4 个选项
- 搜索框：实时过滤任务名

> "+新建"快捷按钮删除，因为正上方就是"⚡ 快速开始" Section。

#### D22 · 归档 = 底部独立折叠区

- "我的任务"列表默认只显示 `Task.status = active`
- 列表底部独立折叠区："⚙ 已归档任务（N）" 默认收起
- 展开后显示归档卡片（视觉降饱和度，不显示三点菜单的"归档"项，改为"恢复 / 永久删除"）
- 归档操作 toast 提示："已归档，可在底部归档区恢复"

#### D23 · 最后对话摘要纳入 P1

- 后端接口扩展：`GET /tasks` 响应中每个任务增加 `last_message_preview` 字段（来自 `Message.content` 末条，截断 80 字符在后端做）
- 实现成本评估：后端需要 SQL JOIN `Conversation` + `Message` 取最新一条；考虑加索引避免扫表
- 列入 P1 实现工单

#### D24 · 空状态 + 加载状态

- 加载：3 张骨架卡片 + shimmer 动画（v3 Skeleton 规范）
- 空（无任务）：CSS 插画 + "还没有任务" + "选择上方一个范式开始你的第一个任务" + 箭头视觉指向 ⚡ 快速开始
- 空（filter 后无结果）：小灰字 "没有匹配的任务" + [清除筛选] 按钮

### 议题 5 · 我的工作概况（已锁定）

#### D25 · 删除"完成率"，保留 3 个指标 · C 折叠抽屉

- 删除 `完成率`（个人样本小，噪声大，"完成"定义不清）
- 保留 3 个：`总任务数` / `本周活跃` / `Token 余额`
- 折叠样式：`📊 我的工作概况  ▾`，默认收起
- 展开后显示 3 个迷你卡片并排，每个含：当前值 + 趋势箭头 + 7 天微 sparkline（高度 16px）
- Token 余额低时由顶部告警条单独触发，不依赖此区域

### 议题 6 · 顶部告警条 + 定时任务摘要（已锁定）

#### D26 · 顶部告警条触发事项 + 并发规则

**触发事项**（7 项）：

| 级别 | 颜色 | 事项 | 角色 |
|---|---|---|---|
| error | 暗红 | WebSocket 断开 / 后端不可用 | 所有人 |
| error | 暗红 | Token 余额 < 1K（耗尽边缘） | 所有人 |
| warning | 暖金 | Token 余额 < 5K | 所有人 |
| warning | 暖金 | 知识库同步失败 | 所有人 |
| warning | 暖金 | 经验卡片待审批 N 条 | 仅 admin |
| info | 雾蓝 | 系统维护通知 / 公告（未读） | 所有人 |
| info | 雾蓝 | 公共任务待审核 N 条（仅在审核制开启时） | 仅 admin |

**并发规则**：

- 同时多条 → 最多 1 条可见，按优先级 `error > warning > info` 排序
- 用户关闭后，下一条 slideDown 滑入
- 关闭过的 warning / info 在 24h 内不再弹（localStorage 记 dismiss key）
- error 不可关闭，必须等问题解决后自动消失
- 复用 v3 `WarningBanner` 组件

#### D27 · 定时任务摘要

```text
⏱ 定时任务  ·  2 个运行中  ·  上次执行 09:00 成功  ·  下次 14:00       [→ 管理]
```

- 1 行只读摘要，不做创建/暂停操作
- "→ 管理" 跳转 `/scheduled-tasks`
- **没有任何定时任务时整个 Section 隐藏**（不显示"暂无"占位，也不显示创建 CTA）

---

## 页面 3 · Workspace `/workspace/:taskId`

**评审进行中**。按"布局/顶栏/侧栏/右栏 → 对话+ToolCalling+输入框 → 文件/知识库"三块推进。

### 议题 7 · 顶栏统一（已锁定）

#### D28 · 删除 WorkspacePage 自有 nav，统一用 TopNav workspace mode

- 删除 [WorkspacePage.tsx:180-215](frontend/src/pages/WorkspacePage.tsx#L180-L215) 自己实现的 `<nav>`
- 统一调用 `<TopNav mode="workspace" taskName=... paradigm=... agentInfo=... onBack=... />`
- 落地 v3 PRD §7 双层 Shell（Global Bar + Context Bar）
- 落地 Agent 抽屉：点击任务名/Agent 区域展开，显示 Skills 列表 + 经验数 + 满意度

#### D29 · TopNav MOCK_NOTIFICATIONS 必须删除

- [TopNav.tsx:113-119](frontend/src/layouts/TopNav.tsx#L113-L119) 中 `MOCK_NOTIFICATIONS` 5 条假通知 → **删除**（违反 G1）
- 改为从后端实拉：新增 `GET /notifications` 接口，返回真实通知聚合（经验卡片待审、定时失败、协作邀请、Token 告警、系统维护、公共任务待审）
- 后端聚合源：`ExperienceCard.status=draft` / `ScheduledRun.status=fail` / `TaskCollaborator.invited` / Token 实时余额 / `SystemConfig.maintenance_notice` / `Task.is_shared && pending_review`

#### D30 · Workspace 顶栏功能集（最终）

```text
[← 返回] [Agent 抽屉: 任务名 · Agent名 ●在线 · 范式]    [📤导出] [🔗分享] [⚙设置] [🌓] [🔔] [用户▾]
              ↓ 点击展开
        ┌─────────────────────────────────────┐
        │ Skills: 分流查询 · 指标计算 · ... │ 12经验 98%满意 │
        └─────────────────────────────────────┘
```

**保留**：← 返回 / Agent 抽屉 / 📤 导出 / 🔗 分享 / ⚙ 设置 / 🌓 主题切换 / 🔔 通知中心 / 用户胶囊菜单

**删除**：

- "我+Agent" 头像组（装饰意义低，占空间）
- 单独的 🔍 搜索按钮（统一通过 ⌘K 快捷键触发，遵循 v3 §7.4）

### 议题 8 · 侧栏（已锁定）

#### D31 · 文件上传上限：后端调大 + 前端不再静默忽略

- 后端 `MAX_UPLOAD_SIZE` 从 2MB 上调 — **建议默认 20MB**，硬上限 50MB（写入 `SystemConfig`，admin 可在 `/admin/settings` 调整）
- 前端不再 `if (file.size > 2*1024*1024) continue` 静默丢弃
- 超出后端上限时：显示 toast "文件 {name} 超过 {limit}MB 上限，无法上传"
- 上传中：显示 inline 进度条（每个文件一行 + percent + 取消按钮）
- 上传成功：toast "已上传 {name}"；失败：toast "上传失败：{reason}"，提供"重试"按钮
- 列入 P1 工单（前后端联动）

#### D32 · 文件删除二次确认

- 点击文件行的 × 按钮 → 弹 confirm modal："确认删除「{name}」？此操作不可撤销"
- modal 中 [取消 默认聚焦] [删除 危险色]
- 误删保护，受 v3 ErrorState 设计规范

### 议题 9 · ChatHeader + 右栏（已锁定）

#### D33 · 右栏改造为 4 Tab 切换

```text
┌─────────────────────────────────┐
│ [📄 文件] [⚙ 配置] [🤖 Agent] [👥 协作]   │
├─────────────────────────────────┤
│ 当前 Tab 内容                    │
└─────────────────────────────────┘
```

**Tab 内容定义**：

- **📄 文件 Tab**：当 `previewFileId` 有值时切换到此 Tab；显示文件预览（md / html sandbox / csv 表格 / txt / json / sql / py 高亮）
- **⚙ 配置 Tab**：任务范式、状态、模型、初始 Prompt、定时配置摘要；可编辑（重命名 / 切范式 / 切模型）
- **🤖 Agent Tab**：当前 Agent 详情（描述 + 绑定 Skills tag + 最近经验卡片 3 条 + "去 Agent 详情页 →"）
- **👥 协作 Tab**：协作者列表（头像 + 姓名 + 权限 + 在线状态 + 加入时间）；任务创建者可：邀请 / 移除 / 改权限

**默认 Tab 行为**：

- 用户从消息流 click 文件 → 自动跳到 📄 文件 Tab
- 进入 Workspace 时默认 ⚙ 配置 Tab
- 切换 Tab 不丢失之前 Tab 的状态

#### D34 · 文件预览支持格式扩展（v3 P2 一并实现）

| 格式 | 渲染方式 |
|---|---|
| md | ReactMarkdown |
| html | sandbox iframe（`sandbox=""` 不允许 scripts，安全加固） |
| csv | 表格预览 ≤100 行（>100 行显示前 100 + 提示"完整数据请下载"） |
| txt | `<pre>` 等宽 |
| json | 语法高亮 + 折叠 |
| sql | 语法高亮 |
| py | 语法高亮 |

文件 > 500KB：右栏顶部黄条提示"文件较大，建议下载查看 [⬇ 下载]"

**HTML 安全加固**：sandbox 改为空字符串（不再 `allow-scripts`），消除 XSS 风险

#### D35 · 文件预览面板顶部增加按钮

```text
[📄 文件名]                      [⬇ 下载] [✏ 重命名] [✕]
```

#### D36 · ChatHeader 简化

- v3 顶栏 Agent 抽屉已承担"显示 Agent + Skills"职责
- ChatHeader **改为只显示当前模型** + 极简切换：`[ Claude Opus 4.7 ▾ ]   [ 💾 导出对话 ] [ 🗑 清空 ]`
- 删除冗余的 Agent 头像 + 名称（避免与顶栏重复）

### 议题 10 · 消息渲染（已锁定）

#### D37 · 切换到 react-markdown + 语法高亮 + DOMPurify

- **删除** [ChatMessages.tsx:63-71](frontend/src/components/ChatMessages.tsx#L63-L71) 的 `escapeAndFormat` 和 [L19-61](frontend/src/components/ChatMessages.tsx#L19-L61) 的 `renderContent`
- 改用 `react-markdown` 渲染消息内容（与 FilePreview 保持一致）
- 代码块用 `react-syntax-highlighter`（建议主题：oneDark / vs2015）
- 代码块加复制按钮（hover 显示在右上角）
- 富文本经过 `DOMPurify.sanitize` 处理，**移除所有 `dangerouslySetInnerHTML`**
- 支持的 markdown：标题 / 列表 / 编号 / 链接（target="_blank"）/ 表格 / 引用 / 代码块（带语言标签）/ 内联代码

### 议题 11 · Tool Calling 卡片（已锁定）

#### D38 · 工具显示名从 Skill.name 取

- 删除硬编码 `TOOL_LABELS` 字典
- 渲染时通过 `tool_name` 反查 `workspaceStore.skills` 中的 `Skill.name` 显示
- Skill 表中找不到时 fallback 到 `tool_name` 原值（罕见情况，本地 Skill 也应注册到 DB）

#### D39 · 卡片功能升级

- **参数展开**：默认显示前 2 个参数 + 60 字符截断；底部加 "查看完整参数 ▾"，点击展开 monospace JSON
- **错误信息**：失败时卡片内显示错误文本 + 错误码（如 `error_code: TOOL_TIMEOUT_30s`，monospace --text-muted 小字）
- **失败按钮组**：失败时显示 `[🔁 重试] [📋 复制错误] [🚩 反馈]`
  - 🔁 重试：重新发送原 tool_call（前端记忆原 arguments）
  - 📋 复制错误：复制 `tool_name + arguments + error` 到剪贴板（便于报障）
  - 🚩 反馈：弹小窗收集用户描述，写入 `MessageFeedback`
- **超时状态**：前端 30s 计时，无 `tool_call_done` 即标记 status=`timeout`，状态图标 `⏱`，颜色 `--info`，按钮组同失败

### 议题 12 · 输入框（已锁定）

#### D40 · 文件 Tab 顺序 = [工作文件] [公共文件] [知识库]

工作文件最常用，提到第一位。

#### D41 · ModelSelector 上提到主输入框右上角

```text
┌─ 主输入区 ─────────────────────────────┐
│ [textarea autoGrow ≤120px]    [Model▾] │  ← 模型选择器
│  [📄] [⚡] [📎]              [▶ 发送]   │
└────────────────────────────────────────┘
[⌨ Enter 发送  ·  Shift+Enter 换行]      ← 底部 hint 简化
```

#### D42 · 流式输出中 [▶ 发送] → [⏸ 暂停生成]

- 检测 `isTyping` 或 `streamingRef.current` 时，发送按钮变为 ⏸
- 点击 ⏸ → 前端发送 `{ type: "abort" }` ws 事件，后端关闭 LLM 流并写入"已中止"消息
- 中止后立即恢复 ▶ 按钮

#### D43 · placeholder 按 paradigm 区分

| paradigm | placeholder |
|---|---|
| ab_test | 例如：分析「新版搜索」AB 实验的留存影响... |
| biz_analysis | 例如：分析上周经营指标的关键变化与归因... |
| gray_release | 例如：评估 v2.4.0 灰度版本的核心质量指标... |
| data_analysis | 例如：查询近 30 天的 DAU 趋势并可视化... |
| wave_analysis | 例如：定位昨天 DAU 异常下跌的根因... |
| open / null | 向 Agent 描述你的需求... |

#### D44 · 已引用上限 10 个

- `referencedFileIds + referencedSkillIds + selectedCitations.length` ≥ 10 时
- 禁用引用按钮 [📄] [⚡]，hover 提示 "已达 10 个引用上限，请减少引用"
- LLM context 估算：10 个 file × 平均 2K tokens ≈ 20K tokens，安全可控

### 议题 13 · WebSocket 健壮性（已锁定）

#### D45 · 指数退避 + 断开提示

- 重连退避序列：**1s, 2s, 4s, 8s, 16s, 30s 上限**（达到上限后保持 30s 重试）
- 重连成功 → toast "连接已恢复"
- 重连失败 N 次后 → 顶部告警条触发 error 级 "WebSocket 断开，请刷新页面"（受 D26 控制）
- 断开期发消息 → 输入框上方 inline 错误条："连接已断开，正在重连... ｜ [立即重试]"
- 待发消息进队列，连接恢复后自动 flush（最多保留最后 5 条，防止积压）

#### D46 · token 改用 subprotocol 传输（P2）

- 当前 `ws://...?token={JWT}` → 改为 `new WebSocket(url, ['bearer', token])`
- 后端 FastAPI 的 `subprotocols` 参数支持 — 列入 P2 工单

### 议题 14 · 反馈/经验/引用 UX（已锁定）

#### D47 · 反馈条 hover 显示

- `[👍][👎][✨]` 默认隐藏，鼠标悬停消息气泡时滑入显示
- 移动端：tap 消息气泡显示反馈条
- 已点击的反馈状态在 hover 区域显示 active 高亮（再次点击可撤销）

#### D48 · "沉淀为经验" emoji 改 ✨

- 区分推荐追问 `💡` 与沉淀经验 `✨`
- hover 时显示 tooltip "沉淀为 Agent 经验卡片"

#### D49 · CitationBar 默认展开第 1 条

- 第 1 条引用默认展开（含 title + snippet + score），后续条目折叠
- 标题 `📎 引用来源 (N)` 旁加 "全部展开 ▾" 按钮

### 议题 15 · 协作 ShareModal 重做（已锁定）

#### D50 · 完整重做 ShareModal

```text
┌─ 邀请协作者 ─────────────────[×]┐
│ [🔍 搜索 邮箱 / 姓名 / 工号       ]│
│   ↓ 实时搜索结果（debounce 300ms）│
│   [👤 张明远 · 产品经理 · 增长]    │
│   [👤 李思涵 · 数据分析师 · 商业化] │
│                                 │
│ 当前协作者                       │
│ [👤 我（创建者）]  ← 不可移除     │
│ [👤 王子轩 · 研发工程师  collab ▾] [×]│
│ [👤 李思涵 · 数据分析师  collab ▾] [×]│
│                                 │
│ 🔗 复制邀请链接                   │
│  ↳ 链接含 task_id + 一次性 invite_token│
└────────────────────────────────┘
```

**实现要点**：

- **搜索接口**：`GET /users/search?q={keyword}`（**新增非 admin 端点**，只返回团队内用户的 `id / name / role / team / avatar`，不返回邮箱密码等敏感字段）
- **邀请链接**：后端生成 `invite_token` 写入 `TaskCollaborator.status=pending`，链接形如 `/workspace/{taskId}?invite={token}`；对方访问后弹"接受邀请"确认框 → 写入 `status=active`
- **权限**：默认 `collaborate`（D13 已定），但 ShareModal 允许创建者下拉切换到 `readonly`（场景：审阅模式不能改任务）
- **移除二次确认**：弹 v3 Modal "确认移除「{name}」？该用户将无法再访问此任务。"
- **error 改 v3 ErrorState**：警告色背景 + 错误码（如 `USER_NOT_FOUND`）

#### D51 · 后端工单：用户搜索接口

- 新增 `GET /users/search?q={keyword}`，所有登录用户可调用
- 返回字段限定：`id / name / role / team / avatar`，**不返回 email / phone 等 PII**
- 限制查询频次：每用户 30 次/分钟
- 排除已被禁用账号（`status='disabled'`）

### 议题 16 · 统一文件上传（已锁定）

#### D52 · useFileUpload hook 抽出

- 新建 `frontend/src/hooks/useFileUpload.ts`
- 统一处理：上限校验 / 进度上报 / 错误重试 / 引用联动 / 取消
- 调用方：Sidebar 的 + 按钮和拖拽 / ChatInput 的 📎 和拖拽 / 拖拽到消息流（新增） — 全部复用
- 进度通过 NotificationCenter 累积显示（"3 个文件上传中... 67%"），支持点击取消
- D31 决策的"调大上限 + 不再静默"在 hook 内统一实现

#### D53 · 公共文件防误删

- Sidebar "公共文件" 分组下的文件 **不显示 [×] 删除按钮**
- 公共文件的 CRUD 只在 `/admin/files` 管理后台进行
- 普通用户点击公共文件只能"预览 / 引用 / 下载"
- 任意位置（Sidebar / ChatInput）尝试删除公共文件 ID 时后端拒绝（403）

### 议题 17 · 知识库重构（已锁定）

#### D54 · 飞书 + RAG 合并为统一"📚 知识库" Section

```text
📚 知识库  (3)
  ▾ 📖 GYH AI学习    [🔄 (今天 09:00)] ▾
      ├─ 产品规范
      ├─ 经营分析
      └─ 技术文档
  ▾ 🧠 数据产品 SQL   [🔄 (昨天 09:00)] ▾
      └─ ...
  ▸ 🧠 数据产品 beta  [🔄 (昨天 09:00)] ▸
```

- 类型用 `icon` 区分：📖 飞书 / 🧠 RAG
- 同步按钮 hover tooltip 显示上次同步时间

#### D55 · 多 KB 同时展开

- `expandedKb: string | null` → `expandedKbs: Set<string>`
- 用户可同时展开任意数量的 KB 目录树

#### D56 · 文档点击进右栏 Tab（与 D33 联动）

- 删除 `DocPreview` 覆盖层 modal
- 文档点击 → 调用 `setPreviewFileId` 等价机制，进右栏 "📄 文件" Tab
- 文件 Tab 顶部增加 "📎 引用此文档" 快捷按钮（D35 已规划，此处补充 KB 文档场景）

#### D57 · 同步反馈 toast

- 同步成功 → toast "知识库 「{name}」 同步完成（新增 N，更新 M）"
- 同步失败 → toast (error) "同步失败：{reason}"，附 [🔁 重试] 按钮
- 同步进行中：按钮显示 ⏳ 旋转

#### D58 · KB 全空引导

- 当 `feishuKBs.length === 0 && ragKBs.length === 0` 时
- 不再返回 null，而是显示空状态卡片：
  ```
  📚 知识库
  暂未配置任何知识库
  联系 @gongyunhe 配置飞书或 RAG 知识库
  ```

### 议题 18 · WorkspaceSettings 收敛（已锁定）

#### D59 · 删 scheduled Tab，统一到 /scheduled-tasks

- 删除 [WorkspaceSettings.tsx](frontend/src/components/WorkspaceSettings.tsx) 内的 scheduled Tab
- 改为单一 general Tab（不再需要 Tab 切换 UI）
- 设置内提供"→ 管理本任务的定时执行" 跳转链接到 `/scheduled-tasks?taskId={id}`

#### D60 · 归档改 v3 Modal + SPA 导航

- `confirm("确认归档此任务？")` → v3 ConfirmModal："归档后任务将从列表隐藏，可在 Dashboard 底部'已归档任务'区恢复"
- `window.location.href = '/dashboard'` → `useNavigate('/dashboard')`
- 归档操作 toast "已归档「{taskName}」"

#### D61 · 加"更换 Agent" 选项

- 同范式 Agent 之间可切换（如 5 个 biz_analysis paradigm 都可换 — 但目前 1 范式 1 Agent，实际为空名单 → 留扩展）
- 当前实现下：仅 paradigm=null 的开放任务可在多个公共 Agent 间切换
- 切换时弹确认："切换 Agent 后，新对话将使用新 Agent，历史对话保留但不会被新 Agent 使用"

#### D62 · 切换范式 = 默认禁用，仅 admin

- 用户视角：WorkspaceSettings 内**不显示**"切换范式"选项
- admin 视角：在 `/admin/agents` 或专用工具中可强制改 `Task.paradigm` 字段
- 切换范式会重置 Skills 绑定，是高风险操作 → admin 后台带强提示

---

## 页面 4 · Agent 详情页 `/agent/:agentId`

**评审完成日期**：2026-05-07

### 页面目的（角色定义）

| 角色 | 目的 |
|---|---|
| **普通用户** | 选 Agent / 看 Agent 能力 |
| **仅管理员** | 审阅经验卡片 / 调试 Prompt |

### 议题 19 · 页面整体重做（已锁定）

#### D63 · 删除全部 mock 数据，对接真实接口

[AgentDetailPage.tsx:32-102](frontend/src/pages/AgentDetailPage.tsx#L32-L102) 的 `MOCK_AGENT / MOCK_SKILLS / MOCK_MEMORIES / MOCK_EXPERIENCES / MOCK_TIMELINE` **全部删除**（违反 G1）。

**后端需新增/调整的接口**（P1 工单）：

| 接口 | 范围 | 说明 |
|---|---|---|
| `GET /agents/{aid}` | 公开 | 单 Agent 详情（id/name/icon/description/paradigm/badges/stats） |
| `GET /agents/{aid}/skills` | 公开 | 绑定 Skills 列表（用户可见基础信息） |
| `GET /agents/{aid}/experience-cards?status=approved` | 公开 | 仅返回已批准经验卡片（标题 + 引用次数） |
| `GET /agents/{aid}/sample-tasks?limit=3` | 公开 | 最近 3 个使用此 Agent 的公共任务（按 usage_count desc） |
| `GET /agents/{aid}/experience-cards` (all) | admin | 含 draft，用于审批 |
| `GET /agents/{aid}/memories` | admin | Agent 记忆管理 |
| `GET /agents/{aid}/evolution` | admin | 进化日志时间线 |
| `PATCH /agents/{aid}/system-prompt` | admin | 内嵌 Prompt 编辑用 |
| `POST /agents/{aid}/test-chat` | admin | 内嵌测试对话（不入库，纯沙盒） |

#### D64 · 顶栏使用 TopNav workspace 模式 + 面包屑

- 删除当前 `<TopNav mode="dashboard">` 用法
- 改用 workspace 模式风格的双层 Shell（与 D28 一致）
- Context Bar 显示面包屑：`首页 / 团队资产 / Agent / 经营洞察 Agent`

#### D65 · 主 CTA "用此 Agent 创建任务"

- 位置：Agent 信息卡**右上角**醒目按钮（v3 暖色主按钮）
- 行为：点击 → `useNavigate('/create-task?agentId={id}&paradigm={paradigm}')`
- `/create-task` 完整页接收 query 参数，**预填该 Agent + 范式**
- 与 D17 / D18 协调：用户也可从 Dashboard 创建模态进入并保留预选 Agent 的能力（未来扩展）

#### D66 · 经验卡片对普通用户：仅 approved

- 普通用户区只展示 `status=approved` 的经验卡片
- 显示字段：title / preview（截断 80 字符）/ 引用次数 / 批准日期
- 不显示 [批准] / [驳回] / [编辑] 按钮
- 让用户感受到"Agent 学到了什么"，但不暴露内部审批流

#### D67 · Agent 记忆 + 进化日志：仅 admin

- 普通用户**完全看不见**这两个 Section
- 记忆是中间产物（"待升级" / "被验证 N 次"等术语），普通用户看不懂
- 进化日志是 Agent 内部状态变化，对用户没操作意义
- admin 区折叠展示，默认收起

#### D68 · 调试 Prompt 入口：内嵌 (B 方案)

- admin 区 Section "🛡 管理区" 内**直接展开 Prompt 编辑器 + 测试对话面板**
- 不再依赖跳转 `/admin/agents/:id/edit`（该路由保留作为独立深度编辑入口，但本页提供同等能力）
- 编辑器：左侧 textarea (System Prompt) + 右侧 测试对话沙盒（`POST /agents/{aid}/test-chat`，不入库）
- 保存按钮：`PATCH /agents/{aid}/system-prompt`，带 v3 ConfirmModal "保存后该 Agent 在所有任务的后续对话中应用新 Prompt，确认？"
- 该 Section 默认折叠

#### D69 · 最近使用此 Agent 的公共任务（参考案例）

- 普通用户区新增 Section "💡 实际案例（最近使用此 Agent 的公共任务）"
- 显示最多 3 个公共任务卡片（复用 D19 任务卡设计）
- 数据来源：`GET /agents/{aid}/sample-tasks?limit=3`，后端按 `is_shared=true AND agent_id={id} ORDER BY usage_count DESC LIMIT 3`
- 不足 3 个时按实际数量显示；0 个时整 Section 隐藏

### 议题 20 · 重组后页面结构（已锁定）

```text
═══ 全用户可见 ═══════════════════════════════

[Agent 信息卡]
  📈 经营洞察 Agent
  描述...
  [系统预置] [经营分析范式]              [+ 用此 Agent 创建任务]   ← D65 主CTA

[能力（绑定 Skills）]
  4 个卡片网格

[Agent 学到的经验（仅 approved，只读）]
  N 条已批准经验，标题 + 引用次数

[💡 最近使用此 Agent 的公共任务]
  3 个公共任务卡片（D69）

═══ 仅 admin 可见（折叠区域，默认收起）═══════════

[🛡 管理区]
  [📝 内嵌 Prompt 编辑器 + 测试对话沙盒]   ← D68
  [▼ 草稿经验卡片审批 (N)]
  [▼ Agent 记忆管理]
  [▼ 进化日志]
```

#### D70 · admin 区角色 gate

- 通过 `useAuthStore.user.auth_role === 'admin'` 判断
- 非 admin **不渲染**整个 "🛡 管理区" 容器（不仅是按钮隐藏，DOM 也不存在 — 减少前端泄露）
- 后端所有 admin 接口同样做角色校验（前端隐藏 + 后端 403 双层防护）

---

## 页面 5 · 创建任务页 `/create-task`

**评审完成日期**：2026-05-07
**与 Dashboard 创建模态的关系**：D17（模态）+ D18（路由分工）+ D65（query 预填）

### 议题 21 · `/create-task` 重做为"完整工坊"（已锁定）

#### D71 · 保留路由，重做为完整工坊

- 删除当前实现中的"范式卡 + 模态弹窗"重复逻辑（与 Dashboard 模态雷同）
- 改为单页**长表单 + 高级配置折叠**结构：

```text
顶栏 TopNav + 面包屑：首页 / 创建新任务

═ Step 1 · 选择起点 ═
[📋 从模板创建]  [⚖ 范式 ▾ (5 范式)]  [+ 开放任务]
当前选中：{paradigm} · {agent_name}

═ Step 2 · 任务基础 ═
任务名称 *  [_______________]
任务描述    [_______________]
💬 初始 Prompt（可选，按 paradigm 显示 placeholder D43）
[多行文本框]

═ Step 3 · 高级配置（折叠，默认收起）═
▾ 🤖 Agent 与 Skills
   Agent: [{paradigm} 同范式 Agent 下拉 ▾]
   Skills: ☑预绑定的 Skills（可勾选删减）

▾ 📂 预上传文件（可选）
   [拖拽区 / + 选择文件]，复用 D52 useFileUpload hook
   已选文件列表

▾ ⏱ 定时执行（可选）
   ☐ 设为定时任务
   勾选展开：cron 表达式 + Prompt + 推送渠道（飞书/邮件/文件）

▾ 👥 协作者（可选）
   [复用 D50 用户搜索组件]
   已添加协作者列表

底部：[取消]  ☑ 创建后立即开始对话(D17)  [创建任务 →]
```

#### D72 · query 参数预填（D65 配套）

接收 query：

- `?agentId={id}` → 自动选中 Agent
- `?paradigm={key}` → 自动选中范式
- `?template={id}` → 预填 Skills / 初始 Prompt / 文件（来自模板）

参数到位后 `Step 1` 显示已选状态，用户仍可修改。

#### D73 · 高级配置默认折叠

- Step 3 全部默认收起（4 个折叠区）
- 减少新用户认知负担
- 已通过 query / 模板预填的项目，对应折叠区**自动展开**且高亮提示"已从模板/参数预填"

#### D74 · 定时任务在本页同步配置

- 勾选 "☐ 设为定时任务" 后展开：
  - cron 表达式输入（带常用预设按钮：每日 09:00 / 每周一 / 每月 1 日）
  - 执行 Prompt（默认继承 Step 2 初始 Prompt，可独立编辑）
  - 推送渠道：☑ 文件保存 ☑ 飞书通知 ☐ 邮件
- 创建任务时一并 POST 创建 `ScheduledTask` 记录
- 失败兜底：任务创建成功但定时任务创建失败 → toast 提示 + 链接 `/scheduled-tasks` 让用户手动重试

#### D75 · 模板入口 = 顶部 Step 1 [📋 从模板创建]

- 按钮位置：Step 1 第 1 个选项
- 点击 → 弹模板选择器 modal
- 模板列表：我的模板 + 公共模板（tab 切换）
- 选中模板 → 自动填充 paradigm / agent / skills / 初始 prompt / 文件清单（如有）
- 模板选完后用户仍可修改任何字段

#### D76 · 范式数据从 paradigm_presets 表读

- 删除 [CreateTaskPage.tsx:18-49](frontend/src/pages/CreateTaskPage.tsx#L18-L49) 硬编码 PARADIGMS
- 改为页面加载时调用 `GET /admin/paradigm-presets`（需调整为公开端点 `GET /paradigm-presets`）
- 数据：paradigm key / icon / title / desc / agent_id / skill_ids
- 后端工单：将 paradigm-presets 列表查询从 admin 移到公开层级

---

## 页面 6 · 定时任务页 `/scheduled-tasks`

**评审完成日期**：2026-05-07

### 议题 22 · 整页重做（已锁定）

#### D77 · 删除全部 mock + 删除"任务模板" tab

- [ScheduledTasksPage.tsx:44-146](frontend/src/pages/ScheduledTasksPage.tsx#L44-L146) 全部 mock 数据 → **删除**（违反 G1）
- 删除 "任务模板" tab — 模板入口已统一到 D75（`/create-task` Step 1）
- 本页只管"定时任务"，不再做 tab 切换

#### D78 · 顶部操作条 + 筛选

```text
[全部 (N)] [运行中] [已暂停] [失败 ≥1次]   [Agent ▾] [任务 ▾]   [+ 创建定时任务]
```

- 4 个状态 chip 切换
- Agent / 任务 两个下拉筛选
- 接收 `?taskId={id}` query 参数 → 自动选中"任务"过滤器（D59 联动）
- [+ 创建定时任务] 按钮：弹模态 → 选已有 task → 配 cron + prompt + 推送渠道

#### D79 · 创建定时任务的两个入口并存

| 入口 | 场景 |
|---|---|
| `/create-task` 同步创建（D74） | 创建新任务时一并配定时 |
| `/scheduled-tasks` 顶部 [+ 创建] 弹模态 | 针对已有任务追加定时 |

两者后端走同一 `POST /tasks/{id}/scheduled-tasks` 接口。

#### D80 · 任务卡操作集

每张定时任务卡新增按钮：

- `[▶ 立即执行]` — 不影响 cron 计划，立即触发一次（POST 新接口 `/scheduled-tasks/{id}/run-now`）
- `[⏸ 暂停 / ▶ 恢复]` — toggle `is_active`
- `[✏ 编辑]` — 弹模态修改 cron / prompt / 推送渠道
- `[🗑 删除]` — 删除定时任务，**带 v3 ConfirmModal 二次确认**："删除后任务本身保留，但不再自动执行"

#### D81 · 执行历史 inline 详情

- 卡片底部"执行历史"列表，最多展示 **10 条**
- 单行点击 → **inline 展开**当行详情（不弹 modal）：
  - 完整 prompt
  - LLM tokens 用量（input + output + 总）
  - 工具调用列表（按时间序的 tool_calls，含每次的 tool_name + status + duration）
  - 错误堆栈（失败时，monospace --text-muted）
  - 产出文件链接（成功时，点击进右栏 D33 文件 Tab 或下载）
- 末尾 "查看全部 →" 跳转到独立详情页 `/scheduled-tasks/{id}/runs`（新增路由，可分页查看完整执行历史）
- 历史接口：`GET /scheduled-tasks/{id}/runs?limit=10` （后端新增）

#### D82 · cron 自动可读 + 常用预设

- 用 `cronstrue` npm 库（约 5KB gzipped，支持多语言）
- 用户输入 `"0 9 * * 1-5"` → 输入框右侧显示 `"每周一至周五 09:00"`
- 创建/编辑表单提供常用预设按钮：
  - `[每日 09:00]` → `0 9 * * *`
  - `[每周一 09:30]` → `30 9 * * 1`
  - `[每月 1 日 09:00]` → `0 9 1 * *`
  - `[工作日 09:00]` → `0 9 * * 1-5`
  - 用户也可手动输入自定义 cron
- 输入非法 cron → 实时显示红色错误 "无效的 cron 表达式"

---

## 页面 7 · 注册页 `/register`

**评审完成日期**：2026-05-07

### 议题 23 · 关闭开放注册（已锁定）

#### D83 · 删除 `/register` 路由

- 前端：删除 `App.tsx` 中 `/register` 路由 + 删除 `pages/RegisterPage.tsx`
- 后端：`POST /auth/register` 接口**保留**，但默认禁用
  - 新增 `SystemConfig.enable_open_register` 字段，默认 `false`
  - 接口在 `enable_open_register=false` 时返回 403：`OPEN_REGISTER_DISABLED`
  - 仅 super_admin 可在 `/admin/settings` 切换该开关
- 用户开通流程改为：
  1. admin 在 `/admin/users` 创建账号（手填 email/姓名/角色/团队，可选生成临时密码）
  2. 用户用临时密码登录 → 强制重置密码
  3. 或用户首次飞书 OAuth → 自动绑定到 admin 创建的账号（按 email 匹配）

#### D84 · 登录页底部文案调整

- 当前：`没账号？创建新账号`
- 改为：`没账号？联系 @gongyunhe 申请`
- 链接行为：飞书 deeplink 到 @gongyunhe 私聊（或 fallback 到邮箱链接）

---

## 全局约束追加 · 三级角色体系（G2）

**生效日期**：2026-05-07

### G2 · 角色体系（三级）

#### D85 · 三级角色定义 + super_admin 飞书绑定

| 角色 | 标识 | 登录方式 |
|---|---|---|
| **super_admin** | 超级管理员 | **必须**走飞书 OAuth 登录，**不允许密码登录** |
| **admin** | 普通管理员 | 飞书 OAuth 或密码 |
| **user** | 普通用户 | 飞书 OAuth 或密码 |

数据库：

- `User.auth_role` 字段扩展枚举为 `super_admin / admin / user`（当前只有 `admin / user`）
- 需要 schema migration（P1 工单）：旧 `admin` 数据保留，新增 `super_admin` 通过 seed 显式标记

种子设定：

- 种子用户中名为"管理员"的 admin 账号 → seed 时标为 `super_admin`
- 该账号必须绑定飞书账号 ID（在 seed 阶段配置，或首次 OAuth 时绑定）
- super_admin 走密码登录将被后端拒绝（错误码 `SUPER_ADMIN_REQUIRES_FEISHU`）

#### D86 · 三级权限矩阵

| 能力 | super_admin | admin | user |
|---|:---:|:---:|:---:|
| 修改任意用户的 auth_role（提权/降权） | ✅ | ❌ | ❌ |
| 删除用户 | ✅ | ❌ | ❌ |
| 系统配置（模型/参数/公告） | ✅ | ❌ | ❌ |
| `enable_open_register` / `enable_public_task_review` 等全局开关 | ✅ | ❌ | ❌ |
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

#### D87 · 角色变更权限独享 super_admin

- `/admin/users` 页面的 `auth_role` 编辑控件 **仅 super_admin 可见**
- admin 看到的 `/admin/users` 用户卡片中 `auth_role` 字段是只读
- 后端 `PATCH /admin/users/{uid}` 接口对 `auth_role` 字段做 super_admin 角色校验
- super_admin **不能降级自己**（防止误操作锁死）
- 系统至少保留 1 个 super_admin（最后一个不能降级 / 不能删除）

#### D88 · admin Guard 升级

- 当前 `AdminGuard` 仅检查 `auth_role === 'admin'`
- 升级为：`auth_role === 'admin' || auth_role === 'super_admin'`（两者都能进 `/admin/*`）
- 在管理后台内部，super_admin 专属功能用 `<SuperAdminGuard>` 二级 gate（非 super_admin 该 Section 不渲染）

#### D89 · 飞书 OAuth 首次绑定流程

种子团队场景下首次飞书 OAuth：

- 用户在登录页点击"飞书账号登录" → OAuth 跳转飞书 → 回调
- 后端从飞书返回 `feishu_user_id + email`
- 后端按 `email` 在 `User` 表中匹配：
  - **匹配到** → 写入 `User.feishu_user_id` 完成绑定 → 颁发 token
  - **未匹配** → 拒绝："账号未授权，请联系 @gongyunhe"（D 决策白名单制）
- super_admin 必须先在 seed 阶段或 admin 后台预录入 + 标记 `auth_role=super_admin`，首次飞书登录时自动绑定

---

## 页面 8 · 使用指南 `/guide`

**评审完成日期**：2026-05-07

### 议题 24 · 升级 GuidePage（已锁定）

#### D90 · 顶栏统一 + Markdown 升级

- 删除当前 `<div className={styles.topBar}>` 简陋顶栏
- 替换为 TopNav workspace mode + 面包屑：`首页 / 使用指南`（与 D64 一致）
- ReactMarkdown 一并对接 D37：
  - DOMPurify sanitize
  - react-syntax-highlighter 代码块语法高亮 + 复制按钮
  - 外链 `target="_blank" rel="noopener"`，内链 `#锚点` 平滑滚动

#### D91 · 双栏布局 + 桌面端常驻 TOC

```text
┌──────────────┬──────────────────────────────────┐
│ 📚 目录       │  📖 ICE Data Workbench 使用指南  │
│ [🔍 搜索]    │  最后更新 2026-05-06              │
│              │  [✉ 反馈] [🖨 打印]              │
│ · 一、快速开始 │ ─────────────────────────────  │
│   · 1.1 ...  │  ## 一、快速开始                  │
│   · 1.2 ...  │  ...                             │
│ · 二、Agent  │                                  │
│ · 三、范式   │  ## 二、Agent                    │
│ ...          │                                  │
└──────────────┴──────────────────────────────────┘

桌面端 (≥1024px)：左 280px TOC 常驻 + 右内容区
平板/移动 (<1024px)：TOC 收到顶部抽屉，"📚 目录 ▾" 按钮触发
```

- TOC 自动从 markdown 提取 h2 / h3 标题
- 当前阅读章节自动高亮（IntersectionObserver）
- 点击 TOC 项平滑滚动到对应锚点

#### D92 · 工具条三件套（搜索 / 反馈 / 打印）

- **🔍 关键词搜索**：放 TOC 顶部
  - 输入框实时过滤 + 高亮命中段落
  - 支持 ⌘F 快捷键聚焦
  - debounce 200ms
- **✉ 反馈按钮**：放内容顶部信息条
  - 行为：飞书 deeplink 到 `@gongyunhe`，预填消息体 "针对使用指南章节《xxx》的反馈："（取当前阅读章节）
  - fallback：邮箱 `mailto:gongyunhe@xxx?subject=...`
- **🖨 打印 / 导出 PDF**：放内容顶部信息条
  - 触发浏览器原生 `window.print()`
  - 提供专用 `@media print` 样式：隐藏顶栏 / TOC / 工具条，仅打印内容区
  - PDF 导出依赖浏览器自带"打印 → 另存为 PDF"

#### D93 · 编辑权限统一到 admin

- 普通用户：**只读**
- admin / super_admin：在 `/admin/files` 找到 "使用指南.md"（is_pinned=true 置顶）→ 行内编辑或下载替换
- 编辑后 `files/使用指南.md` 实时更新（后端写文件 + 触发缓存失效）
- 不做产品内嵌富文本编辑器（避免开发成本，admin 后台已有简单文本编辑足够）

#### D94 · 加载 + 错误状态升级

- 加载：右侧内容区 5-7 段 Skeleton（不同宽度模拟标题/段落/列表）
- 失败：v3 ErrorState 卡片
  - 图标 ⚠
  - 文案 "无法加载使用指南"
  - 错误码 `GUIDE_LOAD_FAILED` (monospace 小字)
  - 按钮 [🔁 重试] [📋 复制错误]

#### D95 · 内容元信息显示

- 内容顶部信息条显示：
  - 文档标题（来自 markdown 第一个 H1 或后端返回的 `title` 字段）
  - 最后更新时间（从 `File.updated_at` 取，如 "最后更新 2026-05-06"）
  - 字数 / 阅读时长估算（可选："约 7000 字 · 阅读 ~12 分钟"）

---

## 页面 9 · 产品介绍 `/introduce`

**评审完成日期**：2026-05-07

### 议题 25 · 方向 A 简化为纯产品介绍（已锁定）

#### D96 · 重新定位：仅业务视角，删除 PRD/版本进度内容

页面承担**单一职责** = 对外展示"这是什么产品 + 能做什么 + 怎么开始"，不再承担 PRD 文档展示。

**保留**：

- Hero 区（一句话定位 + 强 CTA "立即体验"）
- Core Concepts × 6（描述改业务化）
- 功能特性（去掉 status 三态点，纯展示能力）
- 实际场景案例（新增）

**删除**：

- 模块功能列表里的 `done / new / planned` 状态点
- Roadmap 三阶段表（P1/P2/P3）
- ASCII 架构图
- Tech Stacks 技术栈区
- Legend 图例
- Footer 自爆 "PRD 文档" 标签

#### D97 · 新增"实际场景案例" Section

放在 Core Concepts 之后、功能特性之前（"概念 → 案例 → 能力"递进）：

| 场景卡 | 涉及 Agent | 一句话 |
|---|---|---|
| 跑一个 AB 实验分析 | 实验分析 Agent | 从分流验证到显著性结论一气呵成 |
| 做一份每日经营日报 | 经营洞察 Agent + 定时任务 | 每天早上自动到飞书 |
| 定位指标异常 | 波动归因 Agent | 多维下钻 + 根因 + 影响评估 |
| 写一段 SQL 跑数 | 数据分析 Agent | NL→SQL → 可视化 → 导出 |

**数据来源**：

- Agent 信息从 `GET /agents/public` 读，**禁止硬编码**（G1）
- 场景描述可硬编码（属于产品文案，不是数据）
- 卡片底部 CTA "用此 Agent 创建任务 →" 跳 `/create-task?agentId={id}`（与 D65 复用）

#### D98 · 统一主题切换 + 顶栏

- **删除** [IntroducePage.tsx:153-162](frontend/src/pages/IntroducePage.tsx#L153-L162) 自己实现的 `theme` state 与 `localStorage 'ice-theme'`
- 改用全局 `useTheme` hook（与登录页 + D 锁定一致，统一 storage key）
- **删除** [L172-192](frontend/src/pages/IntroducePage.tsx#L172-L192) 自定义 `<nav>`
- 改用 TopNav 简化模式（仅 Logo + 锚点导航 + 🌓 主题切换 + [立即体验] CTA）
- TopNav 新增 `mode="introduce"` 或复用 `mode="dashboard"` 但禁用搜索/通知/用户胶囊

#### D99 · Hero 区强 CTA + 真实统计数

- 顶部按钮组：[立即体验 →] (主) + [查看使用指南] (次)
- 主 CTA 跳 `/login`；次 CTA 跳 `/guide`
- 4 个统计数字（Hero 底部）从后端读：
  - 功能模块数（保留固定 10，属于文案性质）
  - **Agent 数**：`GET /agents/public` count
  - **Skills 数**：`GET /local-skills` count + DB Skill count（去重）
  - **LLM 模型数**：`GET /models` count
- 加载中先显示 `--` 占位，避免硬编码与真实数据脱节

#### D100 · 配色升级 v3 暖色

- 核心概念 6 张卡的 `iconPrimary / iconAmber / iconPurple / iconGreen / iconRed / iconBlue` 改为 v3 范式色：
  - `iconPrimary` → `--primary` (#e8915a 暖橙)
  - `iconAmber` → `--p-biz` (#d4a34e)
  - `iconPurple` → `--agent` (#9b8ec4)
  - `iconGreen` → `--p-data` (#6baa8e)
  - `iconRed` → `--p-wave` (#c97b7b)
  - `iconBlue` → `--p-ab` (#7bafd4)
- 背景 orb 三色改 v3 暖色板，opacity ≤0.10（v3 §3.1 L3 展示型规则）
- BgGrid 网格 opacity ≤0.10

---

## 管理后台 · A 组（总览 + 用户管理）

**评审完成日期**：2026-05-07

### 议题 26 · AdminLayout 重构（已锁定）

#### D101 · 顶栏统一 + Sidebar 分组导航

- **删除** [AdminLayout.tsx:38-59](frontend/src/layouts/AdminLayout.tsx#L38-L59) 自写 topbar
- 改用 TopNav workspace mode + 面包屑：`首页 / 管理后台 / {当前页}`
- 复用 D29 真实通知中心、D 锁定的全局主题切换、用户胶囊菜单
- Sidebar 13 个导航项改为 4 分组（带分组标题）：

```text
═ 监控 ═
  📊 概览
  📈 用量统计
  💰 成本追踪
  🔍 SQL 审计
═ 内容审核 ═
  💡 经验卡片
  🌐 公共任务
  📋 任务模板
  📁 文件管理
═ 资源管理 ═
  🤖 Agents
  ⚡ Skills
  📚 知识库
═ 用户与配置 ═
  👥 用户管理        ← 角色编辑仅 super_admin
  ⚙ 系统配置 🛡     ← super_admin 专属（路由 gate）
```

#### D102 · SuperAdminGuard 二级 gate

新增 `<SuperAdminGuard>` 组件：

- **整页 gate** 应用于：`/admin/settings` 完整路由
  - 非 super_admin 访问 → `useNavigate('/admin', {replace:true})` + toast `"该页面仅超级管理员可访问"`
- **字段级 gate** 应用于：`/admin/users` 的 `auth_role` 编辑控件
  - 普通 admin 看 `auth_role` 列：只读 chip
  - super_admin 看：可点击下拉编辑

后端所有 super_admin 专属接口同样做角色校验（前端隐藏 + 后端 403 双层防护）。

### 议题 27 · AdminDashboard 重做（已锁定）

#### D103 · 删除 mock + stats 升级

- **删除** [AdminDashboard.tsx:67-73](frontend/src/pages/admin/AdminDashboard.tsx#L67-L73) `MOCK_AGENT_RANKS`（违反 G1）
- 改读后端新增 `GET /admin/agents/ranking?period=7d|30d|month` （按对话数 desc）
- 8 个 stat 卡片升级：
  - 加 7 天微 sparkline（高度 16px，与 Dashboard D25 风格一致）
  - 加趋势 ↑↓
  - 顶部加时间筛选 chip：`[7天 | 30天 | 本月 | 自定义]`，影响所有 stats 与 ranking

#### D104 · 顶部"待处理事项"卡片

新增告警聚合卡片，放在 stats 之上：

```text
🚨 待处理事项
  · 5 条经验卡片待审批 [→]
  · 2 个公共任务待审核 [→]    （仅在 enable_public_task_review 开启时显示）
  · 1 个定时任务昨日失败 [→]
  · ⚠ Token 余额 850K，已低于告警阈值
```

每行可点击跳转对应管理页 + 自动应用筛选。无任何待处理事项时整卡隐藏。

#### D105 · super_admin 专属"全局开关"快捷面板

仅 super_admin 可见，放在概览页底部：

```text
🛡 全局开关（系统配置精选）
  ☐ 开放注册（enable_open_register）             [详情 →]
  ☐ 公共任务审核制（enable_public_task_review）   [详情 →]
  ☐ 飞书白名单严格模式                            [详情 →]
```

切换 toggle 直接调用后端接口（带 v3 ConfirmModal 二次确认）；"详情 →" 跳完整系统配置页。

### 议题 28 · AdminUsers 升级（已锁定）

#### D106 · 三级角色 + super_admin gate

- 后端 `User.auth_role` migration 加 `super_admin`（D85 已锁，此处补充前端层）
- 用户列表"权限"列改为彩色 chip：
  - `super_admin` 紫色 + 🛡 图标
  - `admin` 暖橙色
  - `user` 灰色
- "权限"列旁的编辑控件：
  - 普通 admin → 不可点（只读）
  - super_admin → 下拉编辑，**含三选项**（含说明 tooltip）
- super_admin 编辑自己 → 角色下拉禁用 `super_admin → 其它`，提示"不能降级自己"
- 系统至少保留 1 个 super_admin → 编辑最后一个 super_admin 时同样禁用降级，提示"系统至少需保留 1 个超级管理员"

#### D107 · 飞书绑定列 + 邀请按钮

用户表新增列：

```text
| 用户 | 邮箱 | 飞书 | 权限 chip | 状态 | 最后登录 | 操作 |
|     |     | ✓ 已绑 | super_admin 🛡 | active | 2小时前 | [⋯] |
|     |     | — 未绑 [🔗 邀请] | admin       | active | 1天前 | [⋯] |
|     |     | — 未绑 [🔗 邀请] | user        | active | 5天前 | [⋯] |
```

- ✓ 已绑：用户的 `feishu_user_id` 字段非空
- — 未绑：字段为空，显示 `[🔗 邀请]` 按钮
- 邀请按钮：发送飞书消息给目标用户（含一次性绑定链接，链接有效 7 天）+ toast "已发送邀请"
- 后端新增接口 `POST /admin/users/{uid}/feishu-invite`

#### D108 · 创建用户 = 双模式

```text
[创建用户 modal]
[🪶 白名单（飞书登录）默认]  [🔑 临时密码登录]   ← 顶部 Tab

🪶 白名单 Tab：
  姓名 *
  邮箱 *
  角色（产品经理 / 数据分析师 / 研发工程师 / 其他）
  团队
  权限：☐ admin（默认 user，super_admin 仅 super_admin 可选）
  → 创建后 toast "已创建白名单账号，请将下方飞书邀请链接发送给用户"
  → 显示一次性绑定链接 + 复制按钮

🔑 临时密码 Tab：
  姓名 *
  邮箱 *
  ☑ 生成临时密码（强制首次登录改密）
  角色 / 团队 / 权限同上
  → 创建后显示临时密码 + 复制按钮 + toast "请安全传递"
```

**默认 Tab = 飞书白名单**（D89 主推路径）。

#### D109 · 批量操作 + 角色 / 团队 select 化

- 列表前置 checkbox 多选 + 顶部出现批量条：[批量禁用] [批量启用] [批量飞书邀请] [取消]
- 角色 / 团队字段从自由文本改为 select + "其他" 选项可自定义
  - 角色预设：产品经理 / 数据分析师 / 研发工程师 / 设计师 / 运营 / 其他
  - 团队预设：增长 / 商业化 / 基础架构 / 平台 / 其他
- "其他"选项展开自由文本输入

#### D110 · 删除 + 重置密码 v3 化

- 删除 → v3 ConfirmModal："确认删除「{name}」？该用户的所有任务、对话、文件将一并不可访问。此操作不可撤销。"
- 重置密码后弹 v3 Modal 显示临时密码 + 复制按钮 + 提示 "⚠ 仅显示一次，请安全传递给用户"
- 普通 admin 不能删除 super_admin（前端按钮禁用 + 后端 403）

---

## 管理后台 · B 组（Agent + Skill + 经验卡片）

**评审完成日期**：2026-05-07

### 议题 29 · AdminAgents 简化（已锁定）

#### D111 · 测试对话改真实 + publish_status 收敛

- 删除 [AdminAgents.tsx:151-159](frontend/src/pages/admin/AdminAgents.tsx#L151-L159) `handleTestSend` 的 mock 响应（违反 G1）
- 改用真实接口 `POST /agents/{aid}/test-chat`（与 D68 配套，沙盒不入库不计 token）
- `publish_status` 枚举从 5 种 `published / pending / draft / rejected / unlisted` **收敛为 2 种** `draft / published`
- 数据库 schema migration：旧值 `pending → draft`、`rejected/unlisted → draft`（保留再上架可能）

#### D112 · 创建/编辑跳转完整页

- 列表页 `[+ 创建 Agent]` 按钮 → 跳 `/admin/agents/new`（新增路由）
- 列表行的 "编辑" 按钮 → 跳 `/admin/agents/:id/edit`
- 删除 [AdminAgents.tsx](frontend/src/pages/admin/AdminAgents.tsx) 内的创建/编辑 modal 整段
- 列表精简为：Agent / 范式 / 状态 / 用量 / 操作（去掉 "来源" 列，改用 `is_builtin` 字段）

### 议题 30 · AdminAgentEdit 重构（已锁定）

#### D113 · 4 Tab 结构

```text
[← 返回 Agents 列表]  | 🤖 经营洞察 Agent              [保存配置]

[基础] [Skills 绑定] [测试对话] [经验 / 记忆 / 日志]

基础 Tab：
  name / description / icon / color (v3 范式色) / paradigm
  System Prompt（大 textarea + 字符数 + token 估算）
  ⚠ 修改 prompt 保存时弹 v3 ConfirmModal："此 Prompt 将影响 N 个进行中任务的后续对话，确认保存？"

Skills 绑定 Tab：
  双列 — 左可选 Skills 多选 / 右已绑定（拖拽排序）

测试对话 Tab：
  左侧 Prompt 预览（只读快照）
  右侧测试沙盒（POST /agents/{aid}/test-chat，不入库不计费）
  支持工具调用模拟（与 D68 一致）

经验 / 记忆 / 日志 Tab：
  ▼ 经验卡片（按当前 Agent 过滤，draft/approved/rejected 三 sub-tab + 审批操作）
  ▼ Agent 记忆（结构化记忆列表 + 编辑 / 删除 / 手动升级为经验卡片）
  ▼ 进化日志（时间线，与 AgentDetailPage admin 区一致）
```

#### D114 · Prompt 版本历史（A 方案，保留）

- 每次保存 system_prompt 时写入新表 `AgentPromptHistory`：`id / agent_id / system_prompt / saved_by / saved_at / change_note`
- 基础 Tab 内增加 "📜 版本历史" 折叠区，按时间倒序列出最近 20 个版本
- 每个版本可：[查看] [回滚到此版本（带 ConfirmModal）] [对比当前版本（diff 视图）]
- 版本数无限保留（不主动清理），无清理压力（每个版本仅几 KB）

### 议题 31 · AdminSkills 拆分（已锁定）

#### D115 · 范式预设拆出新页

- 新增路由 `/admin/paradigm-presets`
- AdminLayout sidebar "资源管理" 分组内增加 "🧩 范式预设" 导航项
- 现有 [AdminSkills.tsx](frontend/src/pages/admin/AdminSkills.tsx) 内的范式预设区**整段删除**，AdminSkills 仅管 Skill CRUD
- 新页结构：5 个范式 Tab（ab_test / biz_analysis / gray_release / data_analysis / wave_analysis）
  - 每 Tab 内：绑定的 Agents（多选） + 绑定的默认 Skills（多选 + 排序）
  - 顶部统一保存按钮

#### D116 · tool_schema 编辑器升级

- tool_schema textarea → 升级为代码编辑器（如 Monaco lite 或 CodeMirror），支持：
  - JSON 语法高亮
  - JSON Schema validator 实时校验（输入非法 JSON 红色波浪线 + 提示）
  - "🔧 格式化" 按钮（一键 prettier JSON）
- tool_entry 字段加路径校验（保存时调用后端 `POST /admin/skills/validate-entry` 验证 module path 可导入）

#### D117 · "测试运行 Skill" 按钮

- 编辑 modal 底部新增 "🧪 测试运行" 按钮
- 弹子 modal：
  - 根据 tool_schema 的 properties 自动生成参数表单
  - 用户填参数 → 调用 `POST /admin/skills/{sid}/test-run`
  - 显示结果（含 stdout / stderr / 返回值 / 执行时长）
- 测试在沙盒环境，不影响生产数据

### 议题 32 · AdminExperienceCards 重构（已锁定）

#### D118 · 按 Agent 分组 Tab + 批量审批 + 原文对话跳转

- 顶部加 Agent Tab：`[全部] [实验分析] [经营洞察] [灰度监控] [数据分析] [波动归因] [通用]`
  - Tab 数据来自 `GET /agents/public`（与 G1 真实数据一致）
- 状态筛选改为 multi-checkbox：`☑ draft ☐ approved ☐ rejected`
- 列表前置 checkbox 多选 + 顶部出现批量条：
  - `[批量通过] [批量驳回]`（驳回时弹 modal 输入"驳回原因"）
  - 取消选择 / 全选
- 表格新增 **"原文对话"列**：
  - 显示对话片段摘要（截断 30 字）
  - 点击 → `useNavigate(/workspace/{taskId}#message-{mid})` 跳到对应任务并锚点到原始消息
- 删除按钮改 v3 ConfirmModal："确认删除经验卡片「{title}」？"
- 编辑面板支持优先级 (`priority`)、来源（自动提炼 / 用户手动标记）字段

### 议题 33 · 后端工单（B 组配套）

| 接口 | 说明 |
|---|---|
| `POST /agents/{aid}/test-chat` | 沙盒测试对话，不入库 |
| `GET /admin/agents/:aid` | 单 Agent 详情（取代当前从 list 找） |
| `GET /admin/agents/:aid/prompt-history` | Prompt 版本历史 |
| `POST /admin/agents/:aid/prompt-rollback` | 回滚到指定版本 |
| `GET /admin/agents/:aid/memories` | Agent 记忆列表 |
| `GET /admin/agents/:aid/evolution` | 进化日志 |
| `POST /admin/skills/validate-entry` | tool_entry 路径校验 |
| `POST /admin/skills/{sid}/test-run` | 沙盒执行 Skill |
| 数据库 migration | 新增 `AgentPromptHistory` 表 |
| 数据库 migration | `Agent.publish_status` 枚举收敛 |

---

## 管理后台 · C 组（知识库 + 文件 + 模板 + 公共任务）

**评审完成日期**：2026-05-07

### 议题 34 · AdminKnowledgeBases 升级（已锁定）

#### D119 · 知识库管理增强

- delete 改 v3 ConfirmModal："删除知识库「{name}」？关联的 N 个 Agent 将自动解绑，已同步的 M 个文档将保留为快照"
- 同步操作加 toast：
  - 进行中："正在同步「{name}」..."
  - 成功："已同步：新增 {n} / 更新 {m} / 失败 {k}"
  - 失败："同步失败：{reason}" + [🔁 重试]
- 列表新增"同步日志"操作 → 弹 modal 显示最近 10 次同步：时间 / 新增 / 更新 / 失败原因 / 耗时
- 编辑 modal：改名 / 同步频率（手动 / 每日 09:00 / 每周一 09:30）/ 可见性（公共 / 私有）
- `source_type` 枚举从 4 种 → **2 种** `feishu_wiki / mify_rag`
  - `platform_files / uploaded_docs` 删除 — 这两类是文件而非知识库，归 `/admin/files` 管理
  - 数据库 migration 处理旧数据
- 与 D54 工作空间内"飞书+RAG 合并 Section"保持一致

### 议题 35 · AdminFiles 强化（已锁定）

#### D120 · 文件管理升级

- 顶部新增 `[+ 上传文件]` 按钮，复用 D52 `useFileUpload` hook
- 文本类（md / txt）支持产品内编辑：
  - 列表 "编辑" 操作 → 打开编辑 modal
  - 内嵌简易 markdown 编辑器（textarea + 实时预览分屏）
  - 复用 react-markdown 渲染 + react-syntax-highlighter（与 D37 一致）
- 非文本类（csv / html / json / sql / py）：编辑按钮提示 "此格式不支持产品内编辑，请下载后替换上传"
- 新增 `is_pinned` 字段：
  - 表头加 📌 列（置顶状态）
  - 行内 toggle "置顶/取消置顶"
  - 置顶文件在 Dashboard 公共区 / 工作空间公共文件分组永远排第一
  - 默认 `使用指南.md` 自动 `is_pinned=true`
- 筛选条扩展：[格式 ▾] [类型 input/output/public ▾] [来源 平台预置/Agent产出/用户上传/飞书同步/Mify同步 ▾]
- 新增"来源"列：根据 `sync_source` + `creator_id + workspace_id` 推导

### 议题 36 · AdminTemplates 完善（已锁定）

#### D121 · 模板管理重做

模板字段扩展为完整集（与 D75 锁定一致）：

| 字段 | 类型 | 说明 |
|---|---|---|
| name | string | 模板名 |
| description | text | 描述 |
| paradigm | enum | 范式 |
| agent_id | uuid | 默认 Agent |
| skill_ids | array | 默认 Skills |
| initial_prompt | text | 初始 Prompt |
| file_seeds | array | 预上传文件清单（id 引用） |
| has_schedule | bool | 是否含定时配置 |
| schedule_config | json | 定时 cron / 推送渠道（has_schedule=true 时） |
| visibility | enum | public / private |
| status | enum | draft / approved / rejected |
| reject_reason | text | 驳回原因 |
| creator_id | uuid | 创建者 |
| usage_count | int | 使用次数 |

UI 增强：

- 列表增加"创建者"、"可见性"、"状态"、"含定时" 列
- 创建/编辑 modal 改为完整工坊式表单（字段同 `/create-task` 但是模板版）
- 新增"模板预览"功能：右侧实时渲染 `/create-task` 表单预填效果
- 审核操作：
  - draft → 按钮 [通过] [驳回（带原因输入）]
  - approved → 按钮 [下架（变 rejected）]
  - rejected → 按钮 [重新激活（变 draft）]
- 新增"从任务生成模板"快捷入口 → 选已有任务（admin 可选任意任务）→ 自动填充字段，admin 调整后保存

### 议题 37 · AdminPublicTasks 真实化（已锁定）

#### D122 · 完整重做

- **删除** [AdminPublicTasks.tsx:33-40](frontend/src/pages/admin/AdminPublicTasks.tsx#L33-L40) `MOCK_TASKS`（违反 G1）
- 对接真实接口（后端新增）：
  - `GET /admin/public-tasks?status=` — 列表
  - `POST /admin/public-tasks/:tid/review` — 审核（通过/驳回 + reason）
  - `POST /admin/public-tasks/:tid/delist` — 下架
- 顶部告警条：
  - 读取 `GET /admin/system-config` 中的 `enable_public_task_review` 字段
  - 显示当前审核制状态：`⚠ 公共任务审核制：[开启/关闭] [→ 系统配置]`
  - 关闭时表格自动过滤掉 `pending` 行（因为无审核流，pending 不会出现）
- 表格列扩展：
  - 任务名 / 范式 / 创建者 / 协作者数 / 复用次数 / 状态 / 操作
  - paradigm 字段用后端枚举 (`ab_test` 等)，前端展示中文映射
- 操作：
  - pending → [通过] [驳回（带原因 modal）]
  - published → [详情（跳 /workspace/:tid admin 视角）] [下架（带 ConfirmModal）]
- 下架操作独立于审核制始终可用：admin 任何时候都能下架不当公共任务
- 添加 paradigm + 创建者 + 复用次数排序

### 议题 38 · 审核中心（已锁定）

#### D123 · 新增 /admin/review-center 聚合页

- 路由：`/admin/review-center`
- 页面结构：

```text
[审核中心]
顶部摘要卡：
  📋 模板待审核 N    💡 经验卡片待审核 M    🌐 公共任务待审核 K（仅审核制开启时）

[Tab: 经验卡片 | 公共任务 | 任务模板]

每个 sub-tab 内：
  - 待审核列表（紧凑版）
  - 顶部 [→ 完整管理] 跳深度路由（D118 / D121 / D122）
  - 批量操作（与各深度页保持一致）
```

- sub-tab 数据来自各自 admin 接口（带 `status=draft/pending` 过滤）
- 每条审核行支持快速 [通过] [驳回] 操作（与深度页一致）
- 复杂操作（编辑/详情）跳深度路由

#### D124 · Sidebar 导航微调

修订 D101 的 sidebar 分组，"内容审核" 组改为：

```text
═ 内容审核 ═
  🛡 审核中心          ← 新主入口（聚合视图）
  💡 经验卡片          ← 深度入口（保留）
  🌐 公共任务          ← 深度入口（保留）
  📋 任务模板          ← 深度入口（保留）
  📁 文件管理          ← 文件管理保留独立（不是审核流）
```

- 审核中心是"先来这里看待办"的入口
- 深度入口用于细粒度操作 / 历史查询 / 批量管理

### 议题 39 · 后端工单（C 组配套）

| 接口 | 说明 |
|---|---|
| `GET/PATCH /admin/knowledge-bases/{kbid}` 编辑 | 改名 / 频率 / 可见性 |
| `GET /admin/knowledge-bases/{kbid}/sync-logs` | 同步日志（最近 N 次） |
| 数据库 migration | KB.source_type 枚举收敛为 2 种 |
| 数据库 migration | File.is_pinned 字段 |
| `POST /admin/files/upload` | 公共文件上传 |
| `PATCH /admin/files/{fid}` 内容编辑 | 文本类编辑 |
| 数据库 migration | TaskTemplate 表扩展字段（agent_id / skill_ids / file_seeds / has_schedule / schedule_config / visibility / status / reject_reason） |
| `POST /admin/templates/from-task/:tid` | 从任务生成模板 |
| `GET /admin/public-tasks` | 公共任务列表 |
| `POST /admin/public-tasks/{tid}/review` | 审核 |
| `POST /admin/public-tasks/{tid}/delist` | 下架 |
| `GET /admin/review-center/summary` | 聚合待审核计数 |

---

## 管理后台 · D 组（用量 + 成本 + SQL 审计）

**评审完成日期**：2026-05-07

### 议题 40 · 合并 /admin/costs 到 /admin/usage（已锁定）

#### D125 · 删除 /admin/costs，统一到 /admin/usage

- **删除路由** `/admin/costs` + `AdminCosts.tsx`
- 所有成本相关功能并入 `/admin/usage`（重命名为"用量与成本"统一管理）
- AdminLayout sidebar "监控" 分组移除"💰 成本追踪"，仅保留"📈 用量统计"
- 二者本就调用同一组接口（`getUsageSummary / getUsageDaily / getUsageByModel / getUsageByUser`），合并消除重复实现

#### D126 · `/admin/usage` 完整重构

```text
顶部工具条：
[时间筛选 7/30/90/自定义 ▾]   [📥 导出 CSV]   [⚙ 单价配置]   [💰 月度预算]

[Summary 4 卡]
  总调用次数 / 总 Tokens / 总成本 $X / 月度预算 ▰▰▰▱▱ 65%（达 80% 告警）

[Tabs: 日趋势 | 按模型 | 按用户 | 按 Agent | 按任务]

日趋势：双轴 — 柱：Tokens（暖色） + 折线：Cost（暖金）
按模型/用户/Agent/任务：饼图 + 排序表（点击表头排序）
```

**单价配置**（弹模态）：

- 每个 LLM 模型可配 `input_unit_price` 和 `output_unit_price`（$ / 1K tokens）
- 单价信息存 `LLMModel` 表（已有字段）或 `SystemConfig.llm_pricing` JSON
- 修改单价后，所有历史成本**重新计算**（基于 stored tokens × 当前单价）

**月度预算**：

- super_admin 在"月度预算"按钮设置：本月 / 季度 / 年度预算 ($)
- 实时计算：本月已用 / 预算 比例
- 达 80% → 顶部告警条 warning："已使用本月 LLM 预算 80%（{used}/{total}）"
- 达 100% → error："超出本月预算"
- 数据存 `SystemConfig.llm_budget_monthly`

**按 Agent 维度**（新增）：

- 后端新增 `GET /admin/usage/by-agent?days=N`
- 聚合：每个 Agent 的 calls / tokens / cost
- 排序按成本降序

**按任务维度**（新增）：

- 后端新增 `GET /admin/usage/by-task?days=N`
- 聚合：top 50 高成本任务（含 task name + owner + total cost + total calls）

**导出 CSV**：

- 当前筛选条件下的全部数据
- 文件名：`usage_{YYYYMMDD}_{period}.csv`
- 包含原始 `LLMUsage` 表行（每次调用一行：date / user / agent / model / input_tokens / output_tokens / cost）

### 议题 41 · SQL 审计增强（已锁定）

#### D127 · `/admin/sql-audit` 升级

**筛选扩展**：

- 现有：risk_level / sql_type
- 新增：用户（dropdown 多选）/ Agent（dropdown 多选）/ Workspace（dropdown 单选）/ 时间范围（DateRangePicker）
- 新增 **🔍 SQL 全文搜索**：实时输入关键词，后端模糊匹配 `sql_text LIKE '%xxx%'`

**列表行交互**：

- SQL 列 hover → 显示 popover 全文（max-height 400px + 滚动）
- 复制 SQL 按钮 hover 时浮现
- 长 SQL 在详情 modal 内用 monospace 等宽字体 + 语法高亮（用 `react-syntax-highlighter` 配 SQL 主题）

**详情 modal 完整化**：

```text
[SQL 详情 modal]

SQL 语句（含语法高亮 + 复制按钮）

| 类型 | SELECT |
| 风险级别 | warn (拦截原因：缺 WHERE 条件) |
| 执行耗时 | 1450ms |
| 影响行数 | 12,345 |

| 用户 | 张明远 (产品经理 · 增长团队) |
| Agent | 经营洞察 Agent |
| Workspace | Q2 经营复盘 [→ 进入任务] |
| 错误信息 | （如失败）连接超时... |

[关闭] [📋 复制 SQL]
```

- Workspace 链接：`useNavigate('/workspace/{taskId}')`
- 失败/被拦截时显示具体原因（read from `SQLAuditLog.block_reason` 或 `error_message` 字段，如不存在需后端补字段）

**导出 CSV**：

- 同 D126 模式，导出当前筛选条件下的所有审计记录

### 议题 42 · ECharts v3 配色统一（已锁定）

#### D128 · 全管理后台图表统一配色

| 用途 | 颜色 token |
|---|---|
| 主线 / 主柱 / 主指标 | `--primary` `#e8915a` 暖橙 |
| 辅助折线 / 第二指标 | `--p-biz` `#d4a34e` 暖金 |
| 饼图 / 多色对比 5 色循环 | `--p-ab` 雾蓝 → `--p-biz` 暖金 → `--p-gray` 淡紫 → `--p-data` 灰绿 → `--p-wave` 暗红 |
| 网格线 / 轴线 | `--border` |
| 文本 | `--text-dim` |
| 背景 | `transparent`（继承页面） |

应用范围：

- AdminUsage 所有图表
- AdminDashboard sparkline + 排行 bar
- 所有未来新加的统计图表

### 议题 43 · 后端工单（D 组配套）

| 接口 / migration | 说明 |
|---|---|
| `GET /admin/usage/by-agent?days=N` | 按 Agent 聚合 |
| `GET /admin/usage/by-task?days=N` | 按任务聚合 |
| `GET /admin/usage/export.csv?period=&type=` | CSV 导出 |
| `PATCH /admin/llm-models/{mid}/pricing` | 单价配置 |
| `GET/PATCH /admin/system-config/llm-budget` | 月度预算 |
| `LLMUsage` 表加索引 | (agent_id, created_at) 和 (task_id, created_at) 加速聚合 |
| `SQLAuditLog` 字段补全 | `block_reason / error_message` 列 |
| `GET /admin/sql-audit/export.csv` | SQL 审计 CSV 导出 |

---

## 管理后台 · E 组（系统配置 + AdminLayout 最终架构）

**评审完成日期**：2026-05-07

### 议题 44 · AdminSettings 重构（已锁定）

#### D129 · 整页 super_admin gate

- 路由 `/admin/settings` 套 `<SuperAdminGuard>` 整页保护
- 普通 admin 访问 → 跳 `/admin` 概览 + toast "该页面仅超级管理员可访问"
- AdminLayout sidebar 中"⚙ 系统配置"项标 🛡 图标提示

#### D130 · 4 Tab 结构 + 全局开关置顶

```text
[Tabs: 全局开关 | LLM 模型 | 系统参数 | 公告管理]
```

**Tab 1 · 全局开关**（新增，置顶最高频）：

| 开关 | 字段 | 默认 | 影响 |
|---|---|---|---|
| 开放注册 | `enable_open_register` | false | true 时 `POST /auth/register` 可用（D83） |
| 公共任务审核制 | `enable_public_task_review` | false | true 时新共享任务进 pending（D14） |
| 飞书严格白名单 | `enable_feishu_strict_whitelist` | true | true 时未预录入飞书账号无法登录（D89） |

每个开关切换前弹 v3 ConfirmModal 二次确认。

**Tab 2 · LLM 模型**（升级）：

```text
| 模型 ID | 显示名 | 提供商 | 启用 | 默认 | input $/1K | output $/1K | 操作 |
| azure_openai/gpt-5.4 | GPT-5.4 | OpenAI | ✓ | ✓ | $0.005 | $0.015 | 编辑/删除 |

[添加/编辑模型 modal]
  model_id / display_name / provider / badge / 启用 / 默认
  input_unit_price (USD per 1K tokens)
  output_unit_price (USD per 1K tokens)
```

- 单价字段联动 D126 用量与成本页的成本计算
- 删除模型时 ConfirmModal："删除后已选此模型的对话将自动切换到默认模型"

**Tab 3 · 系统参数**（5 组折叠）：

```text
▾ 身份与会话
  access_token_expire_minutes (60)
  refresh_token_expire_days (7)
  [⟲ 恢复默认]

▾ LLM 调用
  llm_max_tokens (4096)
  llm_default_temperature (0.7)
  llm_timeout_seconds (120)
  conversation_history_limit (20)
  [⟲ 恢复默认]

▾ RAG 检索
  rag_top_k (5)
  rag_similarity_threshold (0.7)
  rag_timeout_seconds (5)
  [⟲ 恢复默认]

▾ 文件上传
  upload_max_size_mb (20)              ← D31 默认值
  upload_max_size_hard_cap_mb (50)     ← D31 硬上限
  [⟲ 恢复默认]

▾ 月度预算
  llm_budget_monthly_usd (200)
  llm_budget_alert_threshold (0.8)
  [⟲ 恢复默认]
```

**敏感修改 ConfirmModal**：

| 修改项 | 提示 |
|---|---|
| `access_token_expire_minutes` 缩短 | "修改后所有用户需要重新登录" |
| `refresh_token_expire_days` 缩短 | "已发出的 refresh_token 部分失效，用户可能需重登" |
| `enable_open_register=true` | "开启后任何人可注册账号，请确认" |
| `upload_max_size_hard_cap_mb` 缩小 | "已上传超出新上限的文件保留，但用户无法新上传更大文件" |

**Tab 4 · 公告管理**（增强）：

字段扩展：

| 字段 | 类型 | 说明 |
|---|---|---|
| title | string | 标题 |
| content | text | 内容 |
| announce_type | enum | info / warning / critical |
| **audience_scope** | enum | all / admin_only / team:{name} |
| **status** | enum | draft / published |
| created_at / published_at | datetime | |

UI：

- 列表新增"受众"、"状态"列
- 创建/编辑表单新增受众下拉 + ☐ 立即发布勾选
- 草稿状态可编辑后再发布；已发布也可"撤回为草稿"

**公告 ↔ 顶部告警条联动**（与 D26）：

- 公告 `status=published` 且 `audience_scope` 命中当前用户 → 作为 `info` 级别告警条候选
- 与 D26 其它 6 项触发事项按优先级 `error > warning > info` 合并
- 用户关闭后 24h 不再弹（与 D26 一致）
- 同一公告对同一用户只触发一次告警条（多次发布同 ID 公告除外）

#### D131 · 配置/模型/公告修改写 audit_log

- 所有写操作（PATCH/POST/DELETE）触发 `AuditLog` 记录：
  - action: `update_config / create_model / update_model / delete_model / create_announcement / update_announcement / delete_announcement`
  - target_type: `system_config / llm_model / announcement`
  - 记录 before/after 值（diff）
- 后端补全 `audit_log` 写入逻辑（如未有）

### 议题 45 · AdminLayout 最终架构（已锁定）

#### D132 · Sidebar 4 分组 14 项最终版

合并所有 sidebar 决策（D101 / D115 / D124 / D125）：

```text
═ 监控 ═
  📊 概览                  /admin
  📈 用量统计              /admin/usage           （D125 含成本）
  🔍 SQL 审计              /admin/sql-audit

═ 内容审核 ═
  🛡 审核中心              /admin/review-center   （D123 新增聚合页）
  💡 经验卡片              /admin/experience-cards（深度入口）
  🌐 公共任务              /admin/public-tasks    （深度入口）
  📋 任务模板              /admin/templates       （深度入口）
  📁 文件管理              /admin/files

═ 资源管理 ═
  🤖 Agents                /admin/agents
  ⚡ Skills                /admin/skills
  🧩 范式预设              /admin/paradigm-presets （D115 新增）
  📚 知识库                /admin/knowledge-bases

═ 用户与配置 ═
  👥 用户管理              /admin/users           （角色编辑仅 super_admin）
  ⚙ 系统配置 🛡           /admin/settings        （整页 super_admin 专属）
```

#### D133 · Sidebar 折叠 + 顶栏统一

- Sidebar 顶部加折叠按钮 ◁ — 折叠后宽度 56px，仅显示 icon，hover 显示完整标签 tooltip
- 折叠状态记忆到 localStorage（`admin-sidebar-collapsed`）
- TopNav 统一为 workspace mode + 面包屑（D101 锁定基础上确认）：
  - Logo + "管理后台" 标题
  - 中间面包屑：`首页 / 管理后台 / {分组} / {当前页}`
  - 右侧 [🌓] [🔔] [用户▾]（与全局一致）
- 删除 [AdminLayout.tsx](frontend/src/layouts/AdminLayout.tsx) 自写 topbar，改用 TopNav 组件

### 议题 46 · 后端工单（E 组配套）

| 接口 / migration | 说明 |
|---|---|
| `SystemConfig` 字段补全 | `enable_open_register / enable_public_task_review / enable_feishu_strict_whitelist / upload_max_size_hard_cap_mb / llm_budget_monthly_usd / llm_budget_alert_threshold` |
| `LLMModel` 字段补全 | `input_unit_price / output_unit_price` |
| `Announcement` 字段补全 | `audience_scope (enum) / status (enum) / published_at (datetime)` |
| 所有 admin write 操作 | 写入 `AuditLog`（含 before/after diff） |
| `GET /system-config/global-toggles` | 返回 3 个 enable_* 给前端（公开端点，但只暴露布尔值） |

---

## 全局架构追加 · G3 · 文件优先存储

**决策日期**：2026-05-07
**影响范围**：整个后端 + 部分前端（仅 API 契约）

### D134 · 文件系统是 source of truth，SQLite 改为 cache/索引

新数据架构：

- **写**：先落盘到文件系统 → 触发 SQLite 索引更新（事务）
- **读**：默认从 SQLite 查询索引 → 必要时回源文件读取详细内容
- **重建**：后端启动时扫描文件系统全量重建索引（disaster recovery）

**好处**：

- 数据可读、可 grep、可 git 化
- 单条任务/用户可独立备份/迁移/分享
- 离线工具链友好（直接读文件而非启动 DB）

**代价**：

- 写路径变长（文件 + DB 双写需事务一致性）
- 大量小文件可能影响 IO 性能（SSD 上可控）
- 需要文件锁机制（多写者并发）

### D135 · 顶级数据目录命名（全小写复数）

```text
agents/    skills/    files/    users/    tasks/
```

- 替代旧 `users_data/`（D136 删除）
- 现有 `extracted/.../agents/ skills/ files/` 内容**复制**为初始数据

### D136 · users/{user_id}/ 目录结构

```text
users/{user_id}/
├── profile.json           # 基础信息
├── settings.json          # 个人设置
├── notifications/         # 通知历史
│   └── {YYYY-MM}.jsonl
├── audit/                 # 操作审计
│   └── {YYYY-MM}.jsonl
└── tasks/                 # 用户的任务索引
    └── index.json         # [{task_id, name, paradigm, status, role: owner/collaborator, updated_at}]
```

**`tasks/index.json`** 是用户视角的任务清单（轻量级）：

- 列出该用户作为 owner 创建的所有任务 + 作为 collaborator 加入的任务
- 包含每条任务的轻量元信息（不含完整内容）
- 用于 Dashboard 我的任务列表渲染（不需要遍历 `tasks/` 全部）
- 创建/加入/移除协作者时同步更新

`{user_id}` 命名：UUID（与现有 `User.id` 字段一致）

### D137 · tasks/{task_id}/ 目录结构

```text
tasks/{task_id}/
├── meta.json              # 任务元信息（含 owner_id 反向关联）
├── workspace.json         # workspace 配置
├── conversations/
│   └── {conv_id}.jsonl    # 每行一条 message（追加写）
├── files/
│   ├── input/             # 用户上传的输入文件
│   ├── output/            # Agent 产出文件
│   └── uploaded/          # 对话中临时上传
├── collaborators.json     # [{user_id, permission, joined_at, status: active/pending, invite_token?}]
├── experience_cards.json  # 此任务沉淀的经验卡片
├── tool_calls/            # Tool calling 历史
│   └── {conv_id}.jsonl    # 按对话分文件，每行一条 tool_call 记录（含 args/result/duration/status）
└── scheduled.json         # 定时任务配置（可选，无定时则不存在）
```

**`meta.json`** 字段：

```json
{
  "id": "uuid",
  "name": "任务名",
  "paradigm": "biz_analysis | null",
  "owner_id": "uuid",          // 反向关联到 users/{owner_id}/
  "agent_id": "uuid",
  "status": "active | archived",
  "is_shared": false,
  "created_at": "ISO-8601",
  "updated_at": "ISO-8601",
  "description": "...",
  "last_message_preview": "..."  // 加速 Dashboard 任务卡渲染（D23）
}
```

**关联**：

- 任务通过 `meta.owner_id` 反向关联到 `users/{user_id}/`
- 协作者通过 `collaborators.json` 关联多个 user_id
- 创建任务时**双写**：在 `tasks/{task_id}/` 创建目录 + 在 `users/{owner_id}/tasks/index.json` 添加索引

### D138 · 删除旧 users_data/ 完整重构

- 删除 `users_data/` 整个目录（含 `database/ uploads/ exports/ backups/`）
- 数据库文件迁移到 `agents/.cache/` 或 `tasks/.cache/`（隐藏目录），仅作索引
- 后端启动时检测：
  - 若文件系统已有数据 → 重建索引
  - 若索引缺失 → 全量扫描重建
- 提供一次性迁移脚本：`scripts/migrate_v2_to_v3.py`（从 SQLite 反向写出文件结构）

### D139 · 索引一致性策略

- 写操作走 transaction：begin → 写文件 → 写索引 → commit；任一失败回滚
- 文件锁：写 `meta.json` / `index.json` 等结构化文件时获取 advisory lock（fcntl 或 portalocker）
- 周期性校验：定时任务检查文件 vs 索引 mtime 一致性，不一致触发局部重建
- 索引 schema migration 通过 alembic（保留），但只管 cache 结构，不影响主数据






