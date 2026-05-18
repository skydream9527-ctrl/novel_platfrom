# ICE Data Workbench v3

AI 数据工作流工作台。设计文档见 [`design_decisions.md`](./design_decisions.md)（133 决策），需求规格见 [`requirements/`](./requirements/)，设计稿见 [`design_v3/`](./design_v3/)。

## 快速启动

```bash
# 一键安装 + 启动（首次约 2-5 分钟）
./deploy.sh --run
```

或分步：

```bash
make install   # 装 backend pip + frontend npm
make dev       # 启动前后端（:5173 / :8000）
```

打开浏览器访问 `http://localhost:5173`，默认账号 `admin / admin123`（首启自动种子化）。

`.env` 已随项目分发，包含 mify 模型网关凭证；可直接跑通 8 个模型对话。生产部署前请轮换 `ICE_SECRET_KEY` 与 `MIFY_GATEWAY_API_KEY`。

## 跨机部署

```bash
# 源机器
make pack                   # 先 npm run build 再打 zip（输出 ice-workbench-YYYYMMDD.zip）

# 发到目标机器
scp ice-workbench-*.zip user@target:~

# 目标机器（macOS / Linux 通用）
unzip ice-workbench-*.zip -d ice-workbench
cd ice-workbench
./deploy.sh --prod          # 生产：同端口伺服 SPA + API + WS，0.0.0.0:8000
# 或
./deploy.sh --run           # dev：前端 :5173 + 后端 :8000
```

`deploy.sh` 会：

1. 检查 Python 3.10+ / Node 18+
2. 创建 backend `.venv` 并 pip install，跑 pytest 自检
3. npm install + tsc typecheck
4. `--prod` 时按需构建 `frontend/dist/`（zip 已带预构建产物，可跳过），用 uvicorn 绑 `0.0.0.0:8000` 启动
5. `--run` 走 dev 双端口；不带参数只安装

`make pack` 会剔除 `.venv` / `node_modules` / `.cache` / 运行时用户数据，但**保留** `frontend/dist` 与 `.env`，解压即可跑 `--prod`。`DATA_ROOT` 默认解析到解压目录，无需手工改 .env。

## Linux 公网部署

```bash
unzip ice-workbench-*.zip -d /opt/ice-workbench
cd /opt/ice-workbench

# 可选：改默认端口
export ICE_BIND_HOST=0.0.0.0
export ICE_BIND_PORT=8000

./deploy.sh --prod          # 或：make prod
# 浏览器访问 http://<服务器公网 IP>:8000
# 健康检查  http://<服务器公网 IP>:8000/api/v1/health
```

**公网可达 checklist**

1. **服务器防火墙**：`sudo ufw allow 8000` 或 `firewall-cmd --add-port=8000/tcp --permanent`
2. **云厂商安全组 / VPC**：开放 TCP 8000 入站
3. **反向代理（推荐）**：nginx 承接 443 + TLS，回源到 `127.0.0.1:8000`
4. **进程常驻**：systemd / pm2 / tmux 任选。systemd unit 示例：

   ```ini
   # /etc/systemd/system/ice-workbench.service
   [Unit]
   Description=ICE Data Workbench
   After=network.target

   [Service]
   Type=simple
   User=ice
   WorkingDirectory=/opt/ice-workbench
   Environment="ICE_BIND_HOST=0.0.0.0"
   Environment="ICE_BIND_PORT=8000"
   ExecStart=/opt/ice-workbench/backend/.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
   Restart=always

   [Install]
   WantedBy=multi-user.target
   ```

   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable --now ice-workbench
   ```

5. **首次登录后改 `admin` 密码**（`/admin/users`），在 `.env` 旋转 `ICE_SECRET_KEY`（≥ 32 字节）、`MIFY_GATEWAY_API_KEY`

**可选 CLI 工具**（Linux 用到 SQL / 飞书时才装）

```bash
pipx install xiaomi-kyuubi-cli     # Kyuubi SQL 网关
# feishu CLI：按内部文档安装
# 两者缺失时相关工具返回 *_NOT_CONFIGURED，不阻塞启动
```

## 仓库导航

### 📋 设计与决策

- [`design_decisions.md`](design_decisions.md) — 133 决策 + 3 全局约束
- [`requirements/SHARED.md`](requirements/SHARED.md) — 全局约束 / 设计 token / 协议规范
- [`requirements/FRONTEND.md`](requirements/FRONTEND.md) — 前端需求
- [`requirements/BACKEND.md`](requirements/BACKEND.md) — 后端需求
- [`design_v3/`](design_v3/) — 14 份 v3 HTML 设计稿
- [`reference/route-map.md`](reference/route-map.md) — 23 路由 ↔ 决策映射
- [`reference/api-map.md`](reference/api-map.md) — API ↔ 决策映射

### 💻 实现代码

- [`backend/`](backend/) — FastAPI + SQLAlchemy + JWT
- [`frontend/`](frontend/) — React 19 + Vite + TypeScript + Zustand
- [`agents/`](agents/) [`skills/`](skills/) [`files/`](files/) [`users/`](users/) [`tasks/`](tasks/) — G3 文件优先存储数据目录

### 📦 历史归档

- [`extracted/ice_data_workspace_v2/`](extracted/) — v2 源代码（仅参考，不再修改）

## 已实现

| 模块 | 状态 |
|---|---|
| 项目骨架 + Makefile 启动脚本 | ✅ |
| 文件优先存储 G3（双写 + portalocker + SQLite cache 索引） | ✅ |
| Auth：密码登录 + JWT 双 token + super_admin 飞书强制 | ✅ |
| 飞书 OAuth：真实 OAuth + 白名单 + 占位（未配置时 `FEISHU_NOT_CONFIGURED`） | ✅ |
| 三级角色 gate：`super_admin` / `admin` / `user` | ✅ |
| `/login` + 三步循环动画 + 测试快捷登录 | ✅ |
| `/introduce` 产品介绍（D96-D100） | ✅ |
| `/dashboard` + 5 范式 + 我的任务 + 团队资产 | ✅ |
| `/workspace/:taskId` 三栏 + 流式对话 + 5 轮 Tool Calling | ✅ |
| `/create-task` 3-Step 工坊（D71-D76） | ✅ |
| `/scheduled-tasks` cron 调度 + 历史回放（D77-D82） | ✅ |
| 后端 scheduler loop（每 20s 扫描，自动触发 cron） | ✅ |
| `/agent/:agentId` 详情页 + admin 区（Prompt 编辑/历史/沙盒）（D63-D70） | ✅ |
| `/guide` 使用指南（D90-D95） | ✅ |
| `/admin` 后台 shell + 概览 + Stats / Alerts / 排行 | ✅ |
| `/admin/users` 用户管理（CRUD + 三级角色 gate + 审计） | ✅ |
| `/admin/agents` + `/admin/agents/:id` 编辑（4 Tab + 版本历史 + 回滚 + 沙盒） | ✅ |
| `/admin/audit` 审计日志查看 | ✅ |
| 文件上传 / 引用 / 预览（useFileUpload hook） | ✅ |
| 通知中心（真实接口） | ✅ |
| Templates CRUD + 审核 | ✅ |
| MarkdownRenderer 统一（react-markdown + DOMPurify） | ✅ |
| ConfirmModal / Toast / ErrorState / Skeleton | ✅ |
| 启动种子（管理员 + 测试用户） | ✅ |

## 路由总览（已实现 24 路由）

| 路径 | 角色 | 说明 |
|---|---|---|
| `/login` | 公开 | 登录 |
| `/introduce` | 公开 | 产品介绍 |
| `/dashboard` | user+ | 任务首页 |
| `/workspace/:taskId` | user+ | 工作空间 + ✨ 沉淀经验 + 🔗 分享 |
| `/create-task` | user+ | 3-Step 工坊 |
| `/scheduled-tasks` | user+ | 定时任务 |
| `/agent/:agentId` | user+ | Agent 详情（admin 看到管理区） |
| `/guide` | user+ | 使用指南 |
| `/admin` | admin+ | 概览 |
| `/admin/usage` | admin+ | 用量与成本（5 Tab + 月度预算 + CSV） |
| `/admin/sql-audit` | admin+ | SQL 审计（3 级分类 + CSV） |
| `/admin/audit` | admin+ | 操作审计日志 |
| `/admin/review-center` | admin+ | 审核中心聚合（待办计数） |
| `/admin/experience-cards` | admin+ | 经验卡片审批（批准后注入 Agent） |
| `/admin/public-tasks` | admin+ | 公共任务审核 |
| `/admin/templates` | admin+ | 任务模板审核 |
| `/admin/agents` | admin+ | Agent 列表 |
| `/admin/agents/:agentId` | admin+ | Agent 编辑（4 Tab） |
| `/admin/skills` | admin+ | Skill CRUD + JSON schema 验证 + 沙盒 test-run |
| `/admin/knowledge-bases` | admin+ | KB CRUD + 飞书 wiki 同步 + 同步日志 |
| `/admin/files` | admin+ | 公共文件上传 / 编辑 / 置顶 |
| `/admin/users` | admin+ | 用户管理（角色编辑限 super） |
| `/admin/settings` | admin+ | 系统设置（开关/LLM/参数/公告） |

## 后续 Session 待补

- 飞书 KB 真实环境联调（需 FEISHU_APP_ID/SECRET + space_id）
- Mify RAG 集成
- 自定义 Skill 沙盒执行（HTTP wrapper）
- LLM 单价 / 月度预算 / SQL CSV 导出（D125-D128）
- 经验卡片审批闭环（D118）
- 公共任务审核流（D122）
- WebSocket subprotocol token 升级（D46，P2）
- 移动端适配 / 虚拟滚动 / ECharts 5 维统计

## 环境变量

详见 [`.env.example`](./.env.example)。

| 变量 | 必需 | 说明 |
|---|---|---|
| `ICE_SECRET_KEY` | ✅ | JWT 签名密钥（≥32 字节） |
| `MIFY_GATEWAY_BASE_URL` + `MIFY_GATEWAY_API_KEY` | ⚠ | mify 模型网关，支持 8 个预设（Claude / GPT / Gemini / GLM / MiMo） |
| `ANTHROPIC_API_KEY` | — | 旧版回退，仅当 mify 未配置时启用 |
| `FEISHU_APP_ID/SECRET` | ⚠ | 不填时飞书按钮返回 `FEISHU_NOT_CONFIGURED` |
| `KYUUBI_HOST/...` | ⚠ | 不填时 SQL skill 返回 `KYUUBI_NOT_CONFIGURED` |

## 飞书登录 + 自动建号

支持用飞书账号一键登录；首次登录自动在本地创建 `auth_role=user` 账号，无需 admin 预先白名单。

### 接入步骤

1. 在飞书开放平台（标准：`https://open.feishu.cn/app`，小米内部走对应内部入口）创建一个企业自建网页应用。
2. 添加权限作用域：`contact:user.id` `contact:user.base` `contact:user.email`。
3. 把回调 URL 加进白名单：`http://你的域:5173/auth/feishu/callback`（或线上域名）。
4. 在 `.env` 填入：

   ```ini
   FEISHU_APP_ID=cli_xxxxxxxxxxxx
   FEISHU_APP_SECRET=xxxxxxxxxxxxxxxxxxxxxx
   FEISHU_HOST=https://open.feishu.cn          # 小米内部改成内部域名
   FEISHU_REDIRECT_URI=http://10.192.138.179:5173/auth/feishu/callback
   ```

5. 重启后端，登录页的"使用小米账号登录"按钮就会变可点。

### 自动建号开关

`/admin/settings`（仅 super_admin）→ 全局开关：

| toggle | 默认 | 行为 |
|---|---|---|
| `enable_feishu_auto_register` | `true` | 飞书首次登录自动建号（推荐对内部全员开放时） |
| `enable_feishu_strict_whitelist` | `true` | 严格白名单：未在 users 表里的飞书账号被拒，与 auto_register 互斥 |

### 流程

```
点 [飞书登录]
  ↓
跳到飞书授权 (open.feishu.cn 或内部域)
  ↓
飞书 302 → /auth/feishu/callback?code=...&state=...
  ↓
SPA 把 code POST 给 /api/v1/auth/feishu/oauth/callback
  ↓
后端 code → user_access_token → user_info
  ↓
查 email/feishu_user_id:
  · 找到 → auto-bind + 签 JWT
  · 没找到 + auto_register=true → 建 user 账号 + 签 JWT
  · 没找到 + auto_register=false → 403 FEISHU_ACCOUNT_NOT_WHITELISTED
```

### 兜底：拒绝邮箱授权时也能登

飞书 OAuth 用户可能不授权 `contact:user.email`。代码会用 `feishu-{open_id前12位}@auto.local` 作为合成 email，不影响登录与后续平台使用。后续用户如果在 admin 后台补 email，下一次飞书登录会按 email 匹配自动合并账号。

## 模型网关路由

mify 网关按 model id 前缀路由不同协议端点，由 [llm_gateway.py](backend/app/services/llm_gateway.py) 统一适配：

| 前缀 | 路由 | 端点 | 协议 |
|---|---|---|---|
| `ppio/pa/claude-*` | `anthropic_native` | `/anthropic/v1/messages` | Anthropic native（含 tool_use streaming） |
| `azure_openai/*` | `openai_responses` | `/v1/responses` | OpenAI Responses API（SSE streaming） |
| `vertex_ai/*` / `xiaomi/*` | `openai_chat` | `/v1/chat/completions` | OpenAI Chat Completions（best-effort） |
| 无 `/` | `legacy_anthropic` | `ANTHROPIC_BASE_URL` | 旧 Anthropic 直连 |

## 验证

```bash
cd backend && . .venv/bin/activate && pytest -q
```

至少覆盖：auth flow / file_transaction 双写回滚 / task 创建。

## 常见问题

**SQLite 索引坏了**
```bash
cd backend && . .venv/bin/activate && python scripts/rebuild_index.py
```

**端口冲突**
- 后端：改 Makefile 中 `--port 8000`
- 前端：改 `frontend/vite.config.ts` 中 `server.port`

**飞书登录** 当前为占位实现，需在 `.env` 填 `FEISHU_APP_ID/SECRET` 并在飞书开发者后台填回调 URL `http://localhost:8000/api/v1/auth/feishu/oauth/callback` 后才能真正打通。
