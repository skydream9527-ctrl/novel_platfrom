# BACKEND — 后端开发需求

> 决策原文见 [`../design_decisions.md`](../design_decisions.md)，全局约束见 [`SHARED.md`](SHARED.md)

## 目录

1. [G3 文件优先存储架构（重大变更）](#1-g3-文件优先存储架构)
2. [Schema 变更与 Migration](#2-schema-变更与-migration)
3. [新增 / 改造 API 端点](#3-新增--改造-api-端点)
4. [认证与角色](#4-认证与角色)
5. [WebSocket 升级](#5-websocket-升级)
6. [Tool Calling 系统](#6-tool-calling-系统)
7. [Agent 进化机制](#7-agent-进化机制)
8. [飞书 / Mify 集成](#8-飞书--mify-集成)
9. [LLM 成本与预算](#9-llm-成本与预算)
10. [安全与审计](#10-安全与审计)
11. [实施优先级](#11-实施优先级)

---

## 1. G3 · 文件优先存储架构（D134–D139）

**重大架构变更**。SQLite 不再是 source of truth。

### 数据落盘位置

```text
agents/{agent_dir}/         # 5 内置 Agent 已迁入
skills/{skill_name}/        # 25 Skill 已迁入
files/{file_name}.md        # 4 公共文件已迁入

users/{user_id}/
  profile.json
  settings.json
  notifications/{YYYY-MM}.jsonl
  audit/{YYYY-MM}.jsonl
  tasks/index.json

tasks/{task_id}/
  meta.json
  workspace.json
  conversations/{conv_id}.jsonl
  files/input/, output/, uploaded/
  files/.meta/{filename}.json
  collaborators.json
  experience_cards.json
  tool_calls/{conv_id}.jsonl
  scheduled.json (optional)
```

详细 schema 见 [`../users/README.md`](../users/README.md) 和 [`../tasks/README.md`](../tasks/README.md)。

### 写路径

```python
# 伪代码
def create_task(name, paradigm, owner_id, ...):
    task_id = uuid()
    with file_transaction():
        # 1. 写文件系统
        os.makedirs(f"tasks/{task_id}/conversations")
        os.makedirs(f"tasks/{task_id}/files/input")
        os.makedirs(f"tasks/{task_id}/files/output")
        os.makedirs(f"tasks/{task_id}/files/uploaded")
        os.makedirs(f"tasks/{task_id}/tool_calls")
        write_json(f"tasks/{task_id}/meta.json", {...})
        write_json(f"tasks/{task_id}/workspace.json", {...})
        write_json(f"tasks/{task_id}/collaborators.json", [{owner_id, "collaborate", "active"}])
        write_json(f"tasks/{task_id}/experience_cards.json", [])

        # 2. 更新用户索引（双写）
        with file_lock(f"users/{owner_id}/tasks/index.json"):
            index = read_json(...)
            index.append({task_id, name, paradigm, "owner", ...})
            write_json(...)

        # 3. 更新 SQLite cache 索引
        db.execute("INSERT INTO tasks_index VALUES (?, ?, ?, ?, ?)", ...)
    return task_id
```

### 读路径

```python
def get_user_tasks(user_id, page, page_size):
    # 默认从 cache 索引查询
    rows = db.execute("SELECT id FROM tasks_index WHERE owner_id = ? ORDER BY updated_at DESC LIMIT ? OFFSET ?", ...)
    # 详细内容回源文件
    return [read_json(f"tasks/{row.id}/meta.json") for row in rows]
```

### 索引重建（D134）

```python
# scripts/rebuild_index.py
def rebuild_all():
    db.execute("DROP TABLE IF EXISTS tasks_index, users_index, ...")
    create_indexes()
    for user_dir in glob("users/*"):
        index_user(user_dir)
    for task_dir in glob("tasks/*"):
        index_task(task_dir)
```

启动时检测：若 SQLite 缺失或表行数与文件系统不一致 → 自动 rebuild。

### 文件锁与并发（D139）

- 每个 `*.json` 文件写时获取 advisory lock（`fcntl.flock` 或 `portalocker`）
- 长时间持有锁会阻塞读 → 大文件改用 `*.jsonl` append-only（如对话历史）
- index.json 等热点改 → debounce 写或 batched flush
- 周期任务校验 mtime 一致性（每小时）

### Migration 一次性脚本

```python
# scripts/migrate_v2_to_v3.py
# 从旧 users_data/database/ice_workbench.db 反向写出文件结构
# 1. 读 SQLite 全表
# 2. 按 user_id 分组写 users/{uid}/profile.json, settings.json
# 3. 按 task_id 分组写 tasks/{tid}/meta.json, workspace.json, ...
# 4. 写 conversations/{conv_id}.jsonl 等
# 5. 校验完整性 → 删除旧 users_data/
```

### `.cache/` 索引位置

不放顶级目录，避免污染数据：

```text
.cache/
  index.db                 # SQLite 索引
  index.lock
```

`.cache/` 加入 `.gitignore`。

---

## 2. Schema 变更与 Migration

### D85 · auth_role 三级

```python
# alembic migration
op.execute("""
  UPDATE users SET auth_role = 'super_admin' WHERE email = 'admin' AND name = '管理员';
""")
op.alter_column('users', 'auth_role', type_=String(20))
# 旧 'admin' / 'user' 保留，新增 'super_admin'
```

### D89 · 飞书绑定字段

```python
op.add_column('users', sa.Column('feishu_user_id', String(50), unique=True, nullable=True))
op.add_column('users', sa.Column('feishu_bound_at', DateTime, nullable=True))
```

### D108 · 创建用户支持白名单

```python
op.alter_column('users', 'password_hash', nullable=True)  # 允许无密码（仅飞书登录）
```

### D111 · publish_status 收敛

```python
# 旧 5 种 → 新 2 种
op.execute("UPDATE agents SET publish_status = 'draft' WHERE publish_status IN ('pending','rejected','unlisted')")
```

### D114 · AgentPromptHistory 表

```python
op.create_table(
    'agent_prompt_history',
    sa.Column('id', String(36), primary_key=True),
    sa.Column('agent_id', String(36), sa.ForeignKey('agents.id')),
    sa.Column('system_prompt', Text),
    sa.Column('saved_by', String(36), sa.ForeignKey('users.id')),
    sa.Column('saved_at', DateTime),
    sa.Column('change_note', Text, nullable=True),
)
```

### D119 · KB source_type 收敛

```python
# 4 种 → 2 种
op.execute("DELETE FROM knowledge_bases WHERE source_type IN ('platform_files','uploaded_docs')")
op.alter_column('knowledge_bases', 'source_type', type_=Enum('feishu_wiki','mify_rag'))
```

### D120 · File.is_pinned + 公共文件防误删

```python
op.add_column('files', sa.Column('is_pinned', Boolean, default=False))
# 使用指南 is_pinned=true
op.execute("UPDATE files SET is_pinned = true WHERE name = '使用指南.md'")
```

### D121 · TaskTemplate 字段扩展

```python
op.add_column('task_templates', sa.Column('agent_id', String(36)))
op.add_column('task_templates', sa.Column('skill_ids', JSON))         # array
op.add_column('task_templates', sa.Column('file_seeds', JSON))         # array
op.add_column('task_templates', sa.Column('has_schedule', Boolean))
op.add_column('task_templates', sa.Column('schedule_config', JSON))
op.add_column('task_templates', sa.Column('visibility', String(20)))   # public/private
op.add_column('task_templates', sa.Column('status', String(20)))       # draft/approved/rejected
op.add_column('task_templates', sa.Column('reject_reason', Text))
```

### D126 · LLMModel 单价

```python
op.add_column('llm_models', sa.Column('input_unit_price', Float))      # USD per 1K tokens
op.add_column('llm_models', sa.Column('output_unit_price', Float))
```

### D127 · SQLAuditLog 字段补全

```python
op.add_column('sql_audit_logs', sa.Column('block_reason', Text, nullable=True))
op.add_column('sql_audit_logs', sa.Column('error_message', Text, nullable=True))
```

### D131 · Announcement 字段扩展

```python
op.add_column('announcements', sa.Column('audience_scope', String(50)))  # all/admin_only/team:{name}
op.add_column('announcements', sa.Column('status', String(20)))           # draft/published
op.add_column('announcements', sa.Column('published_at', DateTime, nullable=True))
```

### SystemConfig 新增 keys

| key | 默认 | 用途 |
|---|---|---|
| `enable_open_register` | false | D83 |
| `enable_public_task_review` | false | D14 |
| `enable_feishu_strict_whitelist` | true | D89 |
| `upload_max_size_mb` | 20 | D31 |
| `upload_max_size_hard_cap_mb` | 50 | D31 |
| `llm_budget_monthly_usd` | 200 | D126 |
| `llm_budget_alert_threshold` | 0.8 | D126 |

### LLMUsage 索引补全（D126）

```python
op.create_index('ix_llm_usage_agent_created', 'llm_usage', ['agent_id', 'created_at'])
op.create_index('ix_llm_usage_task_created', 'llm_usage', ['task_id', 'created_at'])
```

---

## 3. 新增 / 改造 API 端点

### 3.1 公开 / 认证（auth）

| 方法 | 路径 | 说明 | 决策 |
|---|---|---|---|
| GET | `/system-config/global-toggles` | 返回 3 个 enable_* 给前端 | E2 |
| GET | `/users/search?q=` | 用户搜索（非 admin 可用，限频 30/min，限定字段） | D51 |
| POST | `/auth/feishu/oauth/start` | 飞书 OAuth 起跳 | D89 |
| POST | `/auth/feishu/oauth/callback` | 飞书回调 + 白名单匹配 | D89 |
| POST | `/auth/feishu/bind` | 飞书账号与用户绑定 | D89 |
| GET | `/notifications` | 当前用户通知聚合（替代 mock） | D29 |
| POST | `/notifications/read-all` | 全部已读 | D29 |
| POST | `/notifications/{id}/read` | 单条已读 | D29 |
| GET | `/paradigm-presets` | 范式预设公开端点（CreateTask 用） | D76 |
| GET | `/agents/{aid}` | 单 Agent 详情公开 | D63 |
| GET | `/agents/{aid}/skills` | Agent 绑定 Skills 公开 | D63 |
| GET | `/agents/{aid}/experience-cards?status=approved` | 公开经验卡片 | D63 |
| GET | `/agents/{aid}/sample-tasks?limit=3` | 最近使用此 Agent 的公共任务 | D69 |

### 3.2 任务（tasks）

| 方法 | 路径 | 说明 | 决策 |
|---|---|---|---|
| GET | `/tasks` | 我的任务（含 last_message_preview） | D23 |
| GET | `/tasks/public` | 公共任务列表 | D11 |
| POST | `/tasks/{tid}/share` | 共享到公共区（双轨制：自动 published 或 pending） | D14 |
| POST | `/tasks/{tid}/unshare` | 撤回 | D11 |
| POST | `/tasks/{tid}/join` | 加入协作（默认 collaborate） | D12-D13 |
| GET | `/tasks/{tid}/invites/{token}` | 验证邀请链接 + 加入 | D50 |

### 3.3 经验卡片（experience-cards）

| 方法 | 路径 | 说明 | 决策 |
|---|---|---|---|
| GET | `/admin/experience-cards?agent_id=&status[]=` | 多筛选 | D118 |
| POST | `/admin/experience-cards/batch-review` | 批量审批（含 reject_reason） | D118 |
| GET | `/messages/{mid}/source` | 消息原文（用于跳回任务） | D118 |

### 3.4 公共任务（public-tasks）

| 方法 | 路径 | 说明 | 决策 |
|---|---|---|---|
| GET | `/admin/public-tasks?status=` | 列表 | D122 |
| POST | `/admin/public-tasks/{tid}/review` | 审核 + reason | D122 |
| POST | `/admin/public-tasks/{tid}/delist` | 下架 | D122 |
| GET | `/admin/review-center/summary` | 待办聚合计数 | D123 |

### 3.5 模板（templates）

| 方法 | 路径 | 说明 | 决策 |
|---|---|---|---|
| GET | `/templates?visibility=&status=` | 列表（含我的 + 公共） | D121 |
| POST | `/admin/templates/from-task/{tid}` | 从任务生成模板 | D121 |
| POST | `/admin/templates/{tid}/review` | 审核模板 | D121 |

### 3.6 知识库（knowledge-bases）

| 方法 | 路径 | 说明 | 决策 |
|---|---|---|---|
| GET/PATCH | `/admin/knowledge-bases/{kbid}` | 编辑（名称 / 频率 / 可见性） | D119 |
| GET | `/admin/knowledge-bases/{kbid}/sync-logs` | 同步日志 | D119 |
| POST | `/admin/knowledge-bases/{kbid}/test-connection` | 验证连接 | D119 |

### 3.7 文件（files）

| 方法 | 路径 | 说明 | 决策 |
|---|---|---|---|
| POST | `/admin/files/upload` | 公共文件上传 | D120 |
| PATCH | `/admin/files/{fid}/content` | 文本类内容编辑 | D120 |
| PATCH | `/admin/files/{fid}/pin` | 切换置顶 | D120 |

### 3.8 Agent 管理（admin/agents）

| 方法 | 路径 | 说明 | 决策 |
|---|---|---|---|
| POST | `/agents/{aid}/test-chat` | 沙盒测试对话（不入库不计费） | D68 / D111 |
| GET | `/admin/agents/{aid}` | 单 Agent 详情 | D63 |
| GET | `/admin/agents/{aid}/prompt-history` | Prompt 版本历史 | D114 |
| POST | `/admin/agents/{aid}/prompt-rollback` | 回滚版本 | D114 |
| GET | `/admin/agents/{aid}/memories` | Agent 记忆列表 | D113 |
| GET | `/admin/agents/{aid}/evolution` | 进化日志 | D113 |
| GET | `/admin/agents/ranking?period=` | 使用排行（替代 mock） | D103 |

### 3.9 Skill（admin/skills）

| 方法 | 路径 | 说明 | 决策 |
|---|---|---|---|
| POST | `/admin/skills/validate-entry` | tool_entry 路径校验 | D116 |
| POST | `/admin/skills/{sid}/test-run` | 沙盒执行 Skill | D117 |

### 3.10 用量与成本（admin/usage）

| 方法 | 路径 | 说明 | 决策 |
|---|---|---|---|
| GET | `/admin/usage/by-agent?days=` | 按 Agent 聚合 | D126 |
| GET | `/admin/usage/by-task?days=` | 按任务聚合 | D126 |
| GET | `/admin/usage/export.csv?period=&type=` | CSV 导出 | D126 |
| PATCH | `/admin/llm-models/{mid}/pricing` | 单价配置 | D126 |
| GET/PATCH | `/admin/system-config/llm-budget` | 月度预算 | D126 |
| GET | `/admin/sql-audit/export.csv?...` | SQL CSV 导出 | D127 |

### 3.11 用户管理（admin/users）

| 方法 | 路径 | 说明 | 决策 |
|---|---|---|---|
| POST | `/admin/users/{uid}/feishu-invite` | 发送飞书绑定邀请 | D107 |
| POST | `/admin/users/whitelist` | 创建白名单账号（无密码） | D108 |
| POST | `/admin/users/batch-disable` | 批量禁用 | D109 |
| POST | `/admin/users/batch-enable` | 批量启用 | D109 |

### 3.12 定时任务（scheduled-tasks）

| 方法 | 路径 | 说明 | 决策 |
|---|---|---|---|
| POST | `/scheduled-tasks/{sid}/run-now` | 立即执行一次 | D80 |
| GET | `/scheduled-tasks/{sid}/runs?limit=` | 执行历史 | D81 |

---

## 4. 认证与角色

### D85 · super_admin 飞书强制

```python
@router.post("/auth/login")
async def login(body: LoginRequest, ...):
    user = await get_user_by_email(body.email)
    if user.auth_role == 'super_admin':
        raise HTTPException(403, error_code="SUPER_ADMIN_REQUIRES_FEISHU")
    # 验证密码...
```

### D89 · 飞书 OAuth + 白名单

```python
@router.post("/auth/feishu/oauth/callback")
async def feishu_callback(code: str):
    feishu_user = await call_feishu_api(code)  # 取 feishu_user_id, email
    user = await get_user_by_email(feishu_user.email)
    if not user:
        raise HTTPException(403, error_code="FEISHU_ACCOUNT_NOT_WHITELISTED",
                            detail={"contact": "@gongyunhe"})
    if user.feishu_user_id and user.feishu_user_id != feishu_user.feishu_user_id:
        raise HTTPException(409, error_code="FEISHU_BINDING_CONFLICT")
    if not user.feishu_user_id:
        user.feishu_user_id = feishu_user.feishu_user_id
        user.feishu_bound_at = now()
        await save(user)
    return issue_tokens(user)
```

### D87 · 角色变更独享 super_admin

```python
@router.patch("/admin/users/{uid}")
async def update_user(uid, body, current_user = Depends(get_current_user)):
    if 'auth_role' in body:
        if current_user.auth_role != 'super_admin':
            raise HTTPException(403, error_code="PERMISSION_DENIED")
        if uid == current_user.id and body.auth_role != 'super_admin':
            raise HTTPException(400, error_code="CANNOT_DEMOTE_SELF")
        if await is_last_super_admin(uid) and body.auth_role != 'super_admin':
            raise HTTPException(400, error_code="LAST_SUPER_ADMIN_PROTECTED")
    # ...
```

### Token 安全（D 全局）

- localStorage → httpOnly cookie（P1 工单）
- WebSocket subprotocol 传递 token（D46，P2）
- 登录频率限制：5/min/IP（429 + retry_after）

---

## 5. WebSocket 升级（D45-D49）

### 协议契约

见 [SHARED.md §5](SHARED.md#5-websocket-协议-v2)

### 服务端实现要点

```python
@router.websocket("/ws/conversations/{cid}")
async def chat(ws, cid):
    await ws.accept(subprotocol='bearer')   # D46
    token = ws.headers.get('sec-websocket-protocol').split(',')[1].strip()
    user = verify_token(token)

    while True:
        msg = await ws.receive_json()
        if msg['type'] == 'abort':
            cancel_current_generation()    # D42
            continue
        if msg['type'] == 'user_message':
            await handle_user_message(ws, cid, msg, user)
```

### Tool calling 30s 超时（D39）

```python
async with asyncio.timeout(30):
    result = await execute_tool(...)
```

超时后发送：

```json
{"type": "tool_call_done", "tool_call_id": "...", "status": "timeout", "success": false, "error": {"code": "TOOL_TIMEOUT_30s"}}
```

---

## 6. Tool Calling 系统

### D38 · 工具显示名

LLM `tools[]` 注册时 name 用 `Skill.tool_schema.name`，前端显示用 `Skill.name`：

```python
def build_tools_for_llm(skill_ids):
    skills = await get_skills(skill_ids)
    return [
        {
            "type": "function",
            "function": {
                "name": s.tool_schema['name'],          # 给 LLM 用
                "description": s.tool_schema['description'],
                "parameters": s.tool_schema['parameters'],
            },
            "_meta": {"display_name": s.name},          # 给前端用
        }
        for s in skills
    ]
```

### D116-D117 · Schema 校验 + 沙盒执行

```python
@router.post("/admin/skills/validate-entry")
async def validate_entry(body):
    module_path, fn_name = body.tool_entry.split(':')
    try:
        module = importlib.import_module(module_path)
        if not hasattr(module, fn_name):
            return {"valid": False, "error": "Function not found"}
        return {"valid": True}
    except ImportError as e:
        return {"valid": False, "error": str(e)}

@router.post("/admin/skills/{sid}/test-run")
async def test_run(sid, body):
    skill = await get_skill(sid)
    # 沙盒执行（受限环境，不影响生产）
    with SandboxContext():
        result = await execute_tool(skill.tool_entry, body.arguments, timeout=10)
    return {"result": result, "stdout": ..., "stderr": ..., "duration_ms": ...}
```

---

## 7. Agent 进化机制（D63-D70 / D113-D114）

### Prompt 版本历史

```python
@router.patch("/admin/agents/{aid}/system-prompt")
async def update_system_prompt(aid, body, current_user):
    agent = await get_agent(aid)
    history = AgentPromptHistory(
        id=uuid(), agent_id=aid,
        system_prompt=agent.config['system_prompt'],   # 旧版
        saved_by=current_user.id, saved_at=now(),
        change_note=body.change_note,
    )
    await save(history)
    agent.config['system_prompt'] = body.system_prompt
    await save(agent)
    # 文件优先：写入 agents/{aid}/prompt/system.md（D134）
    write_file(f"agents/{aid}/prompt/system.md", body.system_prompt)
```

### 测试沙盒（D68）

```python
@router.post("/agents/{aid}/test-chat")
async def test_chat(aid, body, current_user):
    if current_user.auth_role not in ('admin', 'super_admin'):
        raise HTTPException(403)
    # 不入 conversations 表，不计费
    response = await llm.complete(
        system_prompt=body.system_prompt,    # 用户调试中的 prompt
        messages=body.messages,
        track_usage=False,
    )
    return {"response": response}
```

---

## 8. 飞书 / Mify 集成（D54-D58 / D119）

### 飞书知识库同步

```python
@router.post("/admin/knowledge-bases/{kbid}/sync")
async def sync_kb(kbid):
    kb = await get_kb(kbid)
    log = KBSyncLog(kb_id=kbid, started_at=now())
    try:
        if kb.source_type == 'feishu_wiki':
            docs = await feishu_cli.list_wiki(kb.space_id)
        elif kb.source_type == 'mify_rag':
            docs = await mify_cli.list_documents(kb.dataset_id)
        added, updated, failed = await upsert_kb_documents(kb, docs)
        log.added = added; log.updated = updated; log.failed = failed
        log.status = 'success'
    except Exception as e:
        log.status = 'failed'; log.error = str(e)
    log.ended_at = now(); log.duration_ms = ...
    await save(log)
    return {"summary": log}
```

### 同步频率配置（D119）

通过 cron 调度：

```python
# scheduler.py
@cron("0 9 * * *")  # 每日 9 AM
async def daily_kb_sync():
    kbs = await get_kbs(sync_frequency='daily')
    for kb in kbs:
        await sync_kb(kb.id)
```

---

## 9. LLM 成本与预算（D125-D128）

### 单价计算

每次 LLM 调用记录：

```python
async def record_usage(user, agent, model, input_tokens, output_tokens):
    model_config = await get_model(model)
    cost = (input_tokens / 1000 * model_config.input_unit_price +
            output_tokens / 1000 * model_config.output_unit_price)
    usage = LLMUsage(
        user_id=user.id, agent_id=agent.id, model=model,
        input_tokens=..., output_tokens=..., cost=cost,
        created_at=now(),
    )
    await save(usage)
    await check_budget()  # D126
```

### 月度预算告警

```python
async def check_budget():
    config = await get_config()
    if not config.llm_budget_monthly_usd:
        return
    used = await sum_cost_this_month()
    ratio = used / config.llm_budget_monthly_usd
    if ratio >= 1.0:
        publish_announcement_critical("超出本月预算", audience='admin')
    elif ratio >= config.llm_budget_alert_threshold:
        publish_warning_banner(...)
```

### 改单价后重新计算（D130）

修改 `LLMModel.input/output_unit_price` 不修改历史 usage 行的 cost；
查询时实时按当前单价计算（推荐）或重写历史（更慢但精确）。

---

## 10. 安全与审计

### audit_log 全覆盖（D131）

所有 admin write 操作（PATCH/POST/DELETE）写入：

```python
@router.patch("/admin/users/{uid}")
async def update_user(uid, body, current_user):
    old = await get_user(uid)
    new = update(...)
    await audit_log(
        action="update_user",
        target_type="user", target_id=uid,
        admin_id=current_user.id,
        diff=compute_diff(old.dict(), new.dict()),
    )
```

### SQL 审计三级（D 现状保留）

```python
def classify_sql(sql: str) -> tuple[str, str]:
    sql_upper = sql.strip().upper()
    if any(sql_upper.startswith(k) for k in ('DROP', 'TRUNCATE', 'DELETE')):
        if 'WHERE' not in sql_upper:
            return 'block', 'Bulk delete without WHERE'
    if sql_upper.startswith(('INSERT','UPDATE','CREATE','ALTER')):
        return 'block', 'DML/DDL not allowed'
    if sql_upper.startswith('SELECT'):
        if 'WHERE' not in sql_upper and 'LIMIT' not in sql_upper:
            return 'warn', 'SELECT without WHERE/LIMIT'
        return 'allow', None
    return 'block', 'Unknown SQL type'
```

---

## 11. 实施优先级

### Phase 1 · 基础（P1，约 3 周）

- G3 文件优先存储（含 migration 脚本）
- auth_role 三级 schema migration
- 飞书 OAuth + 白名单
- httpOnly cookie + 登录频率限制
- 9 个 SystemConfig 新键
- 真实数据接口替换 mock 配套

### Phase 2 · 核心（P1-P2，约 4 周）

- Workspace WebSocket subprotocol token + 协议升级
- Tool Calling 完整循环 + 沙盒
- ShareModal 用户搜索接口
- Agent prompt 版本历史 + 测试沙盒
- 飞书 / Mify 知识库同步

### Phase 3 · 增强（P2，约 3 周）

- 用量统计完整化（5 维度 / 单价 / 预算 / CSV）
- SQL 审计增强
- 公共任务 / 模板 / 经验卡片审批接口
- 审核中心聚合接口

### Phase 4 · 打磨（P3，约 2 周）

- WebSocket subprotocol 完成
- 索引重建 / 校验 / 监控
- 备份策略
- 性能压测 + 优化

---

## Migration 顺序

务必按以下顺序：

1. 备份现有 SQLite 数据库
2. 创建新顶级目录（已完成）
3. 跑 `migrate_v2_to_v3.py` 反向写出文件
4. 校验文件完整性
5. 切换后端到文件优先模式
6. 重建 SQLite 索引（基于文件）
7. 删除旧 `users_data/`（保留 backup）
