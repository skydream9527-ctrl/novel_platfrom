# agents/ — 内置 Agent 目录

> 5 个公共 Agent，按业务领域命名

## 当前内容

| 目录 | Agent 名 | 范式 / 用途 |
|---|---|---|
| [`data_analysis/`](data_analysis/) | 数据分析 Agent | NL→SQL + 多专家辩论，覆盖 5 业务线 |
| [`general/`](general/) | 通用 Agent | 集成所有能力，开放任务专用（paradigm=null） |
| [`know/`](know/) | 知识库 Agent | 飞书 KB + Mify RAG 读写 |
| [`learn/`](learn/) | 学习 Agent | 网页抓取 + 知识沉淀 |
| [`_shared/`](_shared/) | 共享运行时 | runtime / llm_client / tool_registry / memory（不是 Agent） |

> 与 5 个**范式 Agent** 的对应关系：data_analysis 同时承担 5 范式中的多个；具体范式预设见 `/admin/paradigm-presets`（D115）。

## 子目录约定

每个 Agent 目录至少含：

```text
agents/{agent_name}/
├── agent.py            # AgentDefinition 注册入口
├── config.py           # API_BASE_URL / API_KEY / 其他常量
├── prompt/             # System Prompt 文件（identity.md / rules.md 等）
├── tools/              # 该 Agent 注册的工具 handler
├── skills/             # 该 Agent 默认的 SKILL.md 集合（可选）
└── README.md           # Agent 描述（可选）
```

## 与决策的关联

- **D63–D70**：Agent 详情页按角色拆分（普通用户看能力 / admin 调试 prompt）
- **D85**：Agent 受 super_admin/admin/user 三级角色权限矩阵约束
- **D113**：admin 后台 4 Tab 编辑（基础 / Skills / 测试 / 经验）
- **D114**：System Prompt 修改后写入 `agents/{name}/.history/prompt-{ISO}.md`
