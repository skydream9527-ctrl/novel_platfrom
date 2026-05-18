# tasks/ — 任务数据目录

> 每个任务一个子目录，UUID 命名（与 `Task.id` 一致）

## 子目录结构

```text
tasks/{task_id}/
├── meta.json                  # 任务元信息（含 owner_id 反向关联）
├── workspace.json             # workspace 配置
├── conversations/             # 对话历史
│   └── {conv_id}.jsonl        # 每行一条 message（追加写）
├── files/                     # 任务关联文件
│   ├── input/                 # 用户上传的输入文件
│   ├── output/                # Agent 产出文件
│   └── uploaded/              # 对话中临时上传
├── collaborators.json         # 协作者列表
├── experience_cards.json      # 此任务沉淀的经验卡片
├── tool_calls/                # Tool calling 历史（按对话分文件）
│   └── {conv_id}.jsonl
└── scheduled.json             # 定时任务配置（无定时则不存在）
```

## meta.json schema

```json
{
  "id": "uuid",
  "name": "任务名",
  "paradigm": "ab_test | biz_analysis | gray_release | data_analysis | wave_analysis | null",
  "owner_id": "uuid",
  "agent_id": "uuid",
  "status": "active | archived",
  "is_shared": false,
  "share_review_status": "approved | pending | rejected | null",
  "description": "任务描述",
  "initial_prompt": "...",
  "last_message_preview": "...",     // D23 加速 Dashboard 任务卡渲染
  "created_at": "ISO-8601",
  "updated_at": "ISO-8601"
}
```

## workspace.json schema

```json
{
  "skill_ids": ["uuid1", "uuid2"],
  "kb_ids": ["uuid"],
  "active_conversation_id": "uuid",
  "selected_model": "model_id"
}
```

## conversations/{conv_id}.jsonl

每行一个 message（JSONL，append-only）：

```json
{"id":"uuid","role":"user|agent|system|tool","content":"...","content_type":"text|tool_call|tool_result","metadata":{...},"file_ref":"uuid","feedback":"up|down|null","created_at":"ISO-8601"}
```

## tool_calls/{conv_id}.jsonl

每行一个 tool 调用记录：

```json
{"tool_call_id":"uuid","conversation_id":"uuid","tool_name":"query_data","arguments":{...},"result":{...},"status":"executing|done|error|timeout","success":true,"duration_ms":1234,"error_message":"...","created_at":"ISO-8601"}
```

## collaborators.json schema

```json
[
  {
    "user_id": "uuid",
    "permission": "readonly | collaborate",
    "status": "active | pending",
    "invite_token": "...",        // pending 时存
    "invited_by": "uuid",
    "joined_at": "ISO-8601"
  }
]
```

## experience_cards.json schema

```json
[
  {
    "id": "uuid",
    "title": "...",
    "content": "...",
    "source_message_id": "uuid",
    "source_conversation_id": "uuid",
    "status": "draft | approved | rejected",
    "priority": 1,
    "reject_reason": "...",
    "approved_by": "uuid",
    "approved_at": "ISO-8601",
    "created_at": "ISO-8601"
  }
]
```

## scheduled.json schema

```json
{
  "id": "uuid",
  "cron_expression": "0 9 * * 1-5",
  "prompt": "...",
  "push_channels": ["file", "feishu", "email"],
  "is_active": true,
  "last_run_at": "ISO-8601",
  "next_run_at": "ISO-8601",
  "created_at": "ISO-8601"
}
```

## files/ 内容

### input/

用户上传的输入文件，文件名保留原名 + 防冲突后缀。元数据存 `.meta/{filename}.json`：

```json
{
  "id":"uuid","name":"...","format":"csv","size":1024,
  "uploaded_by":"uuid","uploaded_at":"ISO-8601"
}
```

### output/

Agent 产出文件（如 SQL / 报告 / 图表配置 JSON）。同样的 .meta 结构。

### uploaded/

对话中临时上传（与对话直接关联），同样的 .meta 结构。

## 与决策的关联

- **D11**：Task.is_shared 字段在 `meta.json`，配合 `collaborators.json` 实现公共任务
- **D12–D14**：协作者加入语义、权限、审核制
- **D17–D18**：创建任务流程（同步写 `meta` + `users/{owner}/tasks/index.json`）
- **D19–D24**：任务卡片信息源（meta.json）
- **D31–D32**：文件上传去 2MB 限制 + 二次确认删除
- **D67**：Agent 记忆存于 `agents/{aid}/memories/` 而非 task 内
- **D77–D82**：定时任务在 `scheduled.json`
- **D80**：定时任务执行历史在 `tasks/{tid}/.runs/` 隐藏目录（按月分 jsonl）
- **D118**：经验卡片审批跨任务全局视图，但数据存于 task 子目录
- **D134–D139**：文件优先存储 + 索引一致性

## 索引一致性双写

创建任务时：

1. 创建 `tasks/{task_id}/` 全套结构
2. 在 `users/{owner_id}/tasks/index.json` 添加索引项
3. 同步更新 SQLite cache（D134）

事务保证：任一步失败需回滚（D139）。
