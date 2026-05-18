# skills/ — 本地 Skill 目录

> 25 个 Skill，启动时自动发现（解析 SKILL.md），可被 LLM function-calling 调用

## 当前清单

文档 / 内容生成：`docx` `pptx` `xlsx` `pdf` `remotion`
知识 / 搜索：`notebooklm` `enhanced-web-search` `feishu` `paper-2-web` `knowledge-2-web`
数据 / SQL：`kyuubi` `nl-sql`
可视化：`imagen` `manimgl-best-practices` `article-illustration-generator`
UI / 前端：`frontend-design` `playwright` `fad-executor-ui-figma` `fad-verifier-qc`
工程 / 规划：`fad-brownfield-style` `fad-plan-checker-gates` `fad-planner-align` `fad-doc-export-spreadsheet` `planning-with-files` `skill-creator`

## 子目录约定

```text
skills/{skill_name}/
├── SKILL.md            # 必需：tool_schema (JSON) + tool_entry + 描述
├── scripts/            # 可执行脚本（python / shell）
├── references/         # 参考资料（可选）
└── assets/             # 资源（可选）
```

## SKILL.md 必含 frontmatter

```yaml
---
name: {skill_name}
description: {一句话说明}
category: SQL | 统计 | 分析 | 输出 | ETL | 监控 | 其他
tool_schema:
  name: {function_name}
  description: ...
  parameters: { ... OpenAI function format ... }
tool_entry: {module:function}        # 例: tool_executor:query_data
source: local                         # local | managed
---
```

## 与决策的关联

- **D38**：工具显示名从 SKILL.md 的 `name` 字段取（不再硬编码）
- **D116**：tool_schema 编辑器需 JSON Schema validator + 格式化按钮
- **D117**：每个 Skill 支持沙盒"测试运行"
- **D52**：文件上传统一 hook（含 Skill 调用产生的文件落到 `tasks/{tid}/files/output/`）
