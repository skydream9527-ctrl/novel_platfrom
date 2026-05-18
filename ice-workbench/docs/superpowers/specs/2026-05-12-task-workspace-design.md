# 任务空间设计与流转 — Design Spec

- **Date**: 2026-05-12
- **Topic**: Task Workspace (creation, collaboration, sharing, agent iteration, external content import)
- **Status**: Approved by user — ready for implementation plan

## 0. 背景与现状

项目已有的"任务"能力：

- `tasks/{task_id}/` 子目录：`meta.json` / `workspace.json` / `collaborators.json` / `experience_cards.json` / `conversations/<cid>.jsonl` / `tool_calls/<cid>.jsonl` / `files/{input,output,uploaded}/`
- `task_svc.create_task` 支持 `agent_id` / `skill_ids` / `visibility` / `publish_status`
- `public_task_svc.share_task` / `unshare_task` + admin review gate (`enable_public_task_review`)
- `experience_card_svc` draft → admin review → `rebuild_agent_cards` 写 `agents/<aid>/prompt/cards.md` → `build_system_prompt` 注入
- `kb_svc` 支持 feishu_wiki / mify_rag，但仅做 KB 同步到 `.cache/`，未落到任务空间
- Agent / Skill 以 ID 引用共享库 `agents/<id>/` / `skills/<id>/`

本 spec 的增量集中在五个缺口：

1. Agent/Skill **轻量快照**进任务空间（C3 混合方案）
2. 共建的 **viewer/editor/owner** 三级权限 + join 申请
3. 外部链接（内部 KB / 飞书文档）抓取正文、**本地副本化**、手动刷新
4. 公共任务 agent snapshot 的**手动更新按钮**（pull by owner）
5. 多对话并行（每用户可开自己的对话 & 多条对话）

## 1. 核心决策速查

| 代号 | 决策 |
|---|---|
| C3 | 混合快照：Agent prompt + Skill SKILL.md 快照进任务；private=live（cards.md 动态读源），public=frozen（snapshot 冻结 + 手动更新按钮） |
| W3 | 分层共建：viewer（任意登录用户对 published public 任务）/ editor（通过 join 申请加入）/ owner（创建者唯一） |
| R2 | 外部导入即冻结本地副本，提供"从源刷新"按钮；不做自动追更 |
| Multi-Conv | 一个任务 N 条并行对话；每用户可开自己的；锁粒度 per `cid` |

## 2. 目录结构（增量加粗）

```text
tasks/{task_id}/
├── meta.json                         [扩展字段]
├── workspace.json                    [current_conversation_id 降级为客户端 hint]
├── collaborators.json                [扩展 role 语义]
├── experience_cards.json
├── snapshot.json                     ★ 新
├── join_requests.json                ★ 新
├── conversations/
│   ├── INDEX.json                    ★ 新 (对话列表)
│   ├── <cid>.jsonl
│   └── <cid>.lock                    ★ 新 (per-cid fcntl 锁)
├── tool_calls/
│   └── <cid>.jsonl
├── files/
│   ├── input/
│   ├── output/
│   ├── uploaded/
│   └── imported/                     ★ 新
│       ├── <file_id>.md
│       └── .meta/<file_id>.json
├── agent/                            ★ 新 (C3 快照)
│   ├── agent.json
│   └── prompt/
│       ├── system.md
│       └── cards.md
└── skills/                           ★ 新 (C3 快照)
    ├── INDEX.json
    └── <skill_id>/
        └── SKILL.md                  (仅 agentic 类别 copy 文件)
```

## 3. 数据模型

### 3.1 `meta.json` 扩展

在既有字段基础上新增：

```json
{
  "collaborator_policy": "request_to_join",
  "imported_file_count": 0
}
```

其余字段（`visibility`、`publish_status`、`shared_at` 等）沿用现状。

### 3.2 `snapshot.json`（新）

```json
{
  "mode": "live | frozen",
  "agent_source_version": "<sha256 of agents/<aid>/prompt/*.md concatenated>",
  "frozen_at": "ISO-8601 | null",
  "frozen_by": "user_id | null",
  "last_manual_update_at": "ISO-8601 | null",
  "last_manual_update_by": "user_id | null"
}
```

- `private` 任务：`mode = "live"`；其余冻结字段为 null
- `public` 任务（share 成功后）：`mode = "frozen"`；`frozen_at` / `frozen_by` 填；agent snapshot 此刻冻结

### 3.3 `collaborators.json`（role 语义扩展）

```json
[
  {"user_id": "...", "role": "owner",  "joined_at": "...", "status": "active"},
  {"user_id": "...", "role": "editor", "joined_at": "...", "status": "active"}
]
```

- `owner`：唯一，创建者。即使 unshare 后也不变
- `editor`：通过 join 申请批准加入
- `viewer`：**不写入文件**。任意登录用户 + `visibility=public` + `publish_status=published` → 计算态 viewer

### 3.4 `join_requests.json`（新）

```json
[
  {
    "id": "req_xxx",
    "user_id": "...",
    "message": "我想参与这个 DAU 分析",
    "status": "pending | approved | rejected",
    "created_at": "...",
    "reviewed_at": "...",
    "reviewed_by": "..."
  }
]
```

`unshare_task` 时所有 `pending` 记录改 `rejected` + reason = `"task_unshared"`。

### 3.5 `conversations/INDEX.json`（新）

```json
[
  {
    "id": "conv_xxx",
    "title": "近7天浏览器DAU分析",
    "created_by": "user_id",
    "created_at": "...",
    "last_message_at": "...",
    "message_count": 14
  }
]
```

- `title` 默认：首条 user message 前 30 字
- 创建者或 owner 可 `PATCH` 改标题 / `DELETE` 删除

### 3.6 `files/imported/.meta/<file_id>.json`（新）

```json
{
  "file_id": "...",
  "filename": "飞书文档标题.md",
  "source_type": "kb_article | feishu_doc",
  "source_url": "https://xxx.feishu.cn/docx/abcd",
  "source_ref": {"obj_type": "docx", "obj_token": "abcd"},
  "imported_at": "ISO-8601",
  "imported_by": "user_id",
  "last_refreshed_at": "ISO-8601 | null",
  "last_refreshed_by": "user_id | null",
  "fetch_error": "string | null"
}
```

### 3.7 `skills/INDEX.json`（新）

```json
[
  {
    "id": "kyuubi_query",
    "name": "Kyuubi 查询",
    "description": "...",
    "category": "builtin | custom | agentic",
    "tool_entry": "app.services.tool_runner:kyuubi_query",
    "source_version": "<sha256 of SKILL.md if agentic, else null>"
  }
]
```

- `category=agentic` → copy `skills/<id>/SKILL.md` 到 `tasks/{tid}/skills/<id>/SKILL.md`
- `category=builtin|custom` → 仅登记 INDEX，不 copy 文件（它们是 schema+可执行实现，不是说明文档）

## 4. 行为规约

### 4.1 任务创建（`task_svc.create_task` 改造）

在既有 `file_transaction` 内追加三步，保证原子性：

1. **Agent snapshot**：`cp agents/<agent_id>/agent.json → tasks/{tid}/agent/agent.json`；`cp agents/<agent_id>/prompt/system.md → tasks/{tid}/agent/prompt/system.md`；`cp agents/<agent_id>/prompt/cards.md → tasks/{tid}/agent/prompt/cards.md`（cards.md 若源不存在则落空文件）；计算 `agent_source_version = sha256(sorted_concat_of_prompt_md_files)`
2. **Skills snapshot**：遍历 `skill_ids`；对 `agentic` 类 copy `SKILL.md`；所有类型写 `skills/INDEX.json`
3. **`snapshot.json`**：`{mode: "live", agent_source_version, frozen_at: null, frozen_by: null, last_manual_update_at: null, last_manual_update_by: null}`

### 4.2 `build_system_prompt(task_id)` 改造

```python
snap = read_json(tasks/{tid}/snapshot.json)
system_md = read(tasks/{tid}/agent/prompt/system.md)   # 任何模式都读快照
if snap.mode == "frozen":
    cards_md = read(tasks/{tid}/agent/prompt/cards.md)  # 冻结
else:
    # live: 优先读源 cards, 吃经验迭代; 若源 agent 已下架则回落任务内快照
    src = agents/<aid>/prompt/cards.md
    cards_md = read(src) if src.exists() else read(tasks/{tid}/agent/prompt/cards.md)
skills_catalog = read(tasks/{tid}/skills/INDEX.json)
return assemble(system_md, cards_md, skills_catalog)
```

> 注：live 模式下任务内 `agent/prompt/cards.md` 平时不被读，仅在源 agent 下架时作为兜底。创建时即 copy 这一步换来"源被删也不会导致任务瘫"的确定性。

### 4.3 Share / Unshare

- `share_task`：现有逻辑 + **新增**：`file_transaction` 内把 `snapshot.mode` 置 `frozen`、`frozen_at=now`、`frozen_by=owner_id`、重读源 `agents/<aid>/prompt/cards.md` 覆写到 `tasks/{tid}/agent/prompt/cards.md`
- `unshare_task`：现有逻辑 + **新增**：`snapshot.mode` 翻回 `live`；扫 `join_requests.json` 将所有 `pending` 改 `rejected`（`reason=task_unshared`）；不清空 `collaborators`

### 4.4 手动更新 Agent snapshot

`POST /tasks/{tid}/agent/refresh`（role: owner + admin）：

Body（可选）：`{"expected_agent_source_version": "<sha>"}` — 前端把进入页面时读到的 version 传回作并发保护。

1. `file_transaction` 获取 `tasks/{tid}/snapshot.json` 锁
2. 读源 `agents/<aid>/prompt/*.md`，计算 `new_version`
3. 若 body 传了 `expected_agent_source_version` 且 `new_version == 当前 snapshot.agent_source_version` → 直接返回 `{changed: false}`（源没变，无需刷新）
4. 若 body 传了 `expected_agent_source_version` 但与**当前 snapshot** 不一致 → `AGENT_SNAPSHOT_STALE (409)`（另一个 owner/admin 已抢先刷新）
5. 覆写 `tasks/{tid}/agent/{agent.json, prompt/system.md, prompt/cards.md}`
6. 更新 `snapshot.agent_source_version = new_version`；`snapshot.last_manual_update_at = now`；`snapshot.last_manual_update_by = user_id`；`mode` 不变
7. `admin_svc.audit(action="refresh_task_agent_snapshot", before=old_version, after=new_version)`
8. `notification_svc` 通知所有 `editor`
9. 响应 `{changed: true, diff_summary: {cards_added, cards_removed, system_changed}, new_version}`

### 4.5 `agent_update_available` 字段

`GET /tasks/{tid}` 返回体新增布尔字段，读时计算、不持久化：

- `visibility != "public"` → `false`
- 否则：`sha256(agents/<aid>/prompt/*.md) != snapshot.agent_source_version` → `true`
- 源 agent 被删（目录不存在） → `false`（兜底用快照）

### 4.6 多对话并行

- `workspace.json.current_conversation_id` 语义：**客户端 hint**（用户上次浏览位置），不再代表"任务的默认对话"
- Conversation inflight 锁：`tasks/{tid}/conversations/<cid>.lock`（`fcntl.flock(LOCK_EX|LOCK_NB)`）—— 冲突返回 `CONVERSATION_INFLIGHT (HTTP 409)`；不同 `cid` 间完全并行

### 4.7 外部内容导入

`POST /files/import`（role: editor+）：

```json
{
  "task_id": "...",
  "source_type": "kb_article | feishu_doc",
  "source_url": "...",
  "source_ref": {...}
}
```

- `kb_article`：`source_ref={kb_id, article_id}`；经 `kb_svc.get_article`
- `feishu_doc`：URL host 白名单后缀 `.feishu.cn`；parse `obj_type` / `obj_token`；经新 `feishu_import_svc`，复用 `services/feishu.py` tenant_access_token + `/open-apis/docx/v1/documents/<token>/raw_content`
- 抓取后落盘 `tasks/{tid}/files/imported/<file_id>.md` + `.meta/<file_id>.json`
- 同 `task_id` + 同 `source_url` 二次导入 → `IMPORT_DUPLICATE (HTTP 409)`，返回已有 `file_id`

### 4.8 刷新导入文件

`POST /files/{file_id}/refresh`：

- 权限：`imported_by` 本人 / owner / admin ✅；其他 editor → `FILE_REFRESH_FORBIDDEN (HTTP 403)`
- 重抓→对比：
  - 一致：仅更新 `last_refreshed_*`
  - 不一致：覆写 `.md` + 更新 `last_refreshed_*`
  - 抓取失败：记 `fetch_error`、不覆写、返回 `IMPORT_FETCH_FAILED (HTTP 502)`
- 响应：`{changed: bool, size: int, last_refreshed_at: str}`

### 4.9 经验卡片闭环（无需改动审核链路，只新增传播规则）

```text
editor draft  →  admin approve  →  rebuild_agent_cards()  →  agents/<aid>/prompt/cards.md
                                                 ↓
                               [private 任务] 下次对话自动吃到（4.2 动态读）
                                                 ↓
                               [public 任务]  agent_update_available=true
                                                 ↓
                                          owner 点按钮（4.4）→ snapshot 刷新
```

- **审批不可逆**：`approved` 状态不允许改回 `rejected`（简化实现；`update_status` 强制拒绝该跳转）
- Agent 被下架后仍用本地 snapshot；前端横幅提示"该 Agent 已下架"

## 5. 权限矩阵

| Action | viewer | editor | owner | admin |
|---|---|---|---|---|
| 读 meta / conversation / files 列表 | ✅ | ✅ | ✅ | ✅ |
| 发对话消息 / 触发 agent 执行 | ❌ | ✅ | ✅ | ✅ |
| 创建/改标题/删对话 | ❌ | 创建✅；改/删仅限自建 | ✅ | ✅ |
| 上传文件 / 导入外部链接 | ❌ | ✅ | ✅ | ✅ |
| 刷新**自己导入**的文件 | ❌ | ✅ | ✅ | ✅ |
| 刷新**别人导入**的文件 | ❌ | ❌ | ✅ | ✅ |
| 删除**自己**上传/导入 | ❌ | ✅ | ✅ | ✅ |
| 删除**别人**的文件 | ❌ | ❌ | ✅ | ✅ |
| Draft 经验卡片 | ❌ | ✅ | ✅ | ✅ |
| 申请加入成为 editor | ✅ | — | — | — |
| 审批 join 申请 | ❌ | ❌ | ✅ | ✅ |
| 手动更新 Agent snapshot | ❌ | ❌ | ✅ | ✅ |
| 撤回公开 `public→private` | ❌ | ❌ | ✅ | ✅ |
| 删除整个任务 | ❌ | ❌ | ✅ | ✅ |
| 审批经验卡片 | ❌ | ❌ | ❌ | ✅ |

依赖封装：`backend/app/core/deps.py` 新增 `get_task_role(task_id, user) -> Literal["viewer","editor","owner","admin"]`；每个 handler 声明最低 role。

## 6. API 清单

### 6.1 新增

| Method | Path | 最低 role |
|---|---|---|
| POST | `/tasks/{tid}/agent/refresh` | owner |
| POST | `/tasks/{tid}/join-request` | viewer |
| GET  | `/tasks/{tid}/join-requests` | owner |
| POST | `/tasks/{tid}/join-requests/{rid}/review` | owner |
| DELETE | `/tasks/{tid}/collaborators/{uid}` | owner |
| GET  | `/tasks/{tid}/conversations` | viewer |
| POST | `/tasks/{tid}/conversations` | editor |
| GET  | `/tasks/{tid}/conversations/{cid}` | viewer |
| PATCH | `/tasks/{tid}/conversations/{cid}` | 创建者 or owner |
| DELETE | `/tasks/{tid}/conversations/{cid}` | 创建者 or owner |
| POST | `/files/import` | editor |
| POST | `/files/{file_id}/refresh` | 导入者 / owner |

### 6.2 改造

- `task_svc.create_task`：新增 agent/skills snapshot + `snapshot.json`
- `task_svc.get_task`：返回体加 `agent_update_available`
- `public_task_svc.share_task`：新增 snapshot 冻结
- `public_task_svc.unshare_task`：解冻 + reject pending join requests
- `build_system_prompt`：按 mode 分支读 cards.md
- `file_svc.list_task_files`：返回项加 `scope` + 导入文件的 `source_*` 字段
- `experience_card_svc.update_status`：拒绝 `approved → rejected` 状态跳转

### 6.3 错误码

| 错误码 | HTTP | 触发 |
|---|---|---|
| `CONVERSATION_INFLIGHT` | 409 | 同 cid 有 LLM inflight |
| `JOIN_ALREADY_PENDING` | 409 | 已有 pending 申请 |
| `JOIN_ALREADY_MEMBER` | 400 | 已是 owner/editor 再申请 |
| `AGENT_SNAPSHOT_STALE` | 409 | 并发刷新检测到源 version 已变 |
| `IMPORT_SOURCE_NOT_SUPPORTED` | 400 | source_type 非白名单 |
| `IMPORT_SOURCE_NOT_ACCESSIBLE` | 403 | 上游 KB/飞书 403 |
| `IMPORT_DUPLICATE` | 409 | 同任务同 source_url 二次导入 |
| `IMPORT_FETCH_FAILED` | 502 | 上游超时/5xx |
| `FEISHU_DISABLED` | 503 | `feishu_enabled=false` |
| `FILE_REFRESH_FORBIDDEN` | 403 | 非导入者 editor 尝试刷新 |

## 7. 并发与一致性

- **文件事务**：所有跨文件写沿用现有 `file_transaction` + 目标文件列表锁
- **Conversation 锁**：per `cid`、`fcntl.flock(LOCK_EX|LOCK_NB)`；只护 LLM inflight 阶段的 assistant message 追写
- **Agent snapshot 并发**：两位 owner/admin 同时点刷新按钮 → 第二个校验 `snapshot.agent_source_version` 是否与 fs 上一致；不一致 → `AGENT_SNAPSHOT_STALE (409)`，让前端重试
- **Import 去重**：查询 `files_index` 的 `task_id + source_url` 复合索引（新增 `files_index.source_url TEXT NULL` 列 + 索引）

## 8. 安全

遵循 `.claude/rules/security.md`：

1. SSRF 防御：`feishu_doc` host 后缀硬白名单 `.feishu.cn`，不开放配置
2. 凭证复用：飞书抓取走现有 `services/feishu.py` tenant_access_token，不引二套凭证
3. 导入以导入者身份进行；上游返回 403 → `IMPORT_SOURCE_NOT_ACCESSIBLE`
4. 文件大小沿用 `MAX_SIZE_HARD_CAP_MB=50`
5. 抓取超时 30s；失败保留上一份可用副本

## 9. 审计

按 CLAUDE.md Audit Logging Rules，下列动作每次写 `.planning/audit/runs/<run-id>/` step：

- `share_task` / `unshare_task`
- `refresh_task_agent_snapshot`
- `approve_join_request` / `reject_join_request`
- `refresh_imported_file`（仅 `changed=true` 单独写；`changed=false` 每日批量合并以控日志膨胀）
- 既有 `review_experience_card`

## 10. 测试清单（TDD 强制）

### 10.1 Service 单测（必须测先于实现）

1. `test_create_task_snapshots_agent_and_skills`
2. `test_create_task_skills_snapshot_agentic_vs_builtin`
3. `test_build_system_prompt_live_mode_reads_source_cards`
4. `test_build_system_prompt_frozen_mode_reads_snapshot_cards`
5. `test_share_task_freezes_snapshot`
6. `test_unshare_task_thaws_and_rejects_pending_joins`
7. `test_refresh_agent_snapshot_by_owner_ok`
8. `test_refresh_agent_snapshot_forbidden_for_editor`
9. `test_refresh_agent_snapshot_stale_version_409`
10. `test_agent_update_available_flag_computation`
11. `test_role_derivation_owner_editor_viewer`
12. `test_editor_cannot_refresh_others_imported_file`
13. `test_import_feishu_doc_happy_path` (mock)
14. `test_import_duplicate_returns_409`
15. `test_import_feishu_url_whitelist_rejects_non_feishu_host`
16. `test_conversation_inflight_lock_per_cid`
17. `test_multi_conversation_parallel_llm_no_interference`
18. `test_join_request_approval_adds_editor`
19. `test_join_request_forbidden_when_already_member`
20. `test_card_approval_triggers_rebuild_and_bumps_agent_source_version`
21. `test_card_status_transition_approved_to_rejected_forbidden`

### 10.2 API 集成测

- Share → refresh → unshare 完整链路
- 权限矩阵 E2E（每行至少一条测试）
- Import → refresh（changed=true / changed=false / fetch fail）

### 10.3 前端最小检查（Playwright smoke）

- 任务详情页对话列表 tab 展示 & 切换
- Public 任务横幅 "🆕 Agent 有 N 条新经验可合入"
- Imported 文件角标 + 刷新按钮点击路径
- Join 申请入口 + owner 侧审批页

## 11. 向后兼容

- 既有 `tasks/{tid}/` 目录无 `snapshot.json` → `task_svc.get_task` 按需懒创建（`mode=live`、`agent_source_version=null`）
- 既有 `collaborators.json` 仅有 owner → 自动兼容
- 既有 `files/uploaded/` / `input/` / `output/` 不动
- 既有 `/tasks/{tid}/conversation`（单数）保留：返回用户最近活跃对话的 messages（`INDEX.json` 按 `last_message_at` desc 取第一条；空则创建默认对话）

## 12. YAGNI 明确不做

- 自动追更导入文件（R3）
- 一键全刷所有导入文件
- 审批回滚（`approved → rejected`）及连带 public 任务"撤下经验"流程
- 任意 URL 导入（仅 KB + 飞书文档）
- editor 改 agent snapshot
- 共建多 owner / owner 转让
- 每对话独立 agent snapshot
