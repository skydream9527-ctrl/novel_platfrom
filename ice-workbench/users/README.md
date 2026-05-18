# users/ — 用户数据目录

> 每个用户一个子目录，UUID 命名（与 `User.id` 一致）

## 子目录结构

```text
users/{user_id}/
├── profile.json           # 用户基础信息
├── settings.json          # 个人偏好
├── notifications/         # 通知历史（按月分文件）
│   └── 2026-05.jsonl
├── audit/                 # 操作审计（按月分文件）
│   └── 2026-05.jsonl
└── tasks/                 # 用户视角的任务索引
    └── index.json
```

## profile.json schema

```json
{
  "id": "uuid",
  "name": "张明远",
  "email": "zhang@ice.dev",
  "password_hash": "bcrypt...",       // null 时该用户仅可飞书登录
  "auth_role": "user | admin | super_admin",
  "role": "产品经理",
  "team": "增长团队",
  "avatar": "data-uri or url or null",
  "feishu_user_id": "ou_xxx | null",   // 飞书 OAuth 绑定（D89）
  "status": "active | disabled",
  "last_login_at": "ISO-8601 | null",
  "created_at": "ISO-8601",
  "created_by": "uuid (admin id)"      // D108 admin 后台创建
}
```

## settings.json schema

```json
{
  "theme": "dark | light",
  "default_model": "model_id",
  "notification_dismiss_keys": ["banner-token-warning-2026-05-07"],
  "sidebar_collapsed": false,           // admin 用户的 sidebar 折叠状态（D133）
  "guide_banner_dismissed": false       // 使用指南横幅 dismiss
}
```

## tasks/index.json schema

> 用户视角的任务清单（轻量）— 用于 Dashboard 我的任务列表渲染

```json
[
  {
    "task_id": "uuid",
    "name": "任务名",
    "paradigm": "biz_analysis | null",
    "status": "active | archived",
    "role": "owner | collaborator",
    "agent_id": "uuid",
    "agent_name": "经营洞察 Agent",
    "last_message_preview": "...",       // D23
    "last_updated_at": "ISO-8601",
    "file_count": 3,
    "collaborator_count": 2,
    "is_shared": false                   // 仅 owner 时有意义
  }
]
```

## notifications/{YYYY-MM}.jsonl

每行一个 JSON：

```json
{"id":"uuid","type":"experience|task-fail|collaboration|token-alert|system","title":"...","description":"...","read":false,"action_url":"...","created_at":"ISO-8601"}
```

## audit/{YYYY-MM}.jsonl

每行一个 JSON：

```json
{"id":"uuid","action":"login|create_task|share_task|...","target_type":"task|file|...","target_id":"uuid","metadata":{...},"ip":"...","created_at":"ISO-8601"}
```

## 与决策的关联

- **D85–D89**：三级角色 + 飞书绑定 + 白名单
- **D106–D110**：admin 后台用户管理
- **D134–D139**：文件优先存储（profile.json 是 source of truth）
- **D136**：本目录结构定义

## 索引一致性

- `users/{uid}/tasks/index.json` 与 `tasks/{tid}/meta.json.owner_id` + `tasks/{tid}/collaborators.json` 双向一致
- 任意一边写入需同步另一边（D139 文件锁 + 事务）
- 索引漂移检测：定时任务校验 mtime 一致性，不一致触发局部重建
