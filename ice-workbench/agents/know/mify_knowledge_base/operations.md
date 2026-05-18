# Mify 操作手册

Skill 路径：`~/.trae-cn/skills/mify-knowledge-base/`（Trae）或 `~/.agents/skills/mify-knowledge-base/`（其他）

**重要**：所有脚本必须从项目根目录执行，禁止 `cd` 到 skill 目录。

## 0. 设置 SKILL_DIR 变量

```bash
# Trae 用户
SKILL_DIR="$HOME/.trae-cn/skills/mify-knowledge-base"

# 其他工具（OpenCode / Claude Code）
SKILL_DIR="$HOME/.agents/skills/mify-knowledge-base"
```

## 1. 预检（每次操作前必须执行）

```bash
# 本地操作
python3 "$SKILL_DIR/scripts/preflight.py"

# 涉及飞书操作
python3 "$SKILL_DIR/scripts/preflight.py" --need-email --verify-feishu

# 指定 Profile
python3 "$SKILL_DIR/scripts/preflight.py" --profile team-space
```

预检结果 `ready: true` 才能继续，否则按 `errors` 逐项修复。

## 2. 知识库管理

```bash
# 列出所有知识库
python3 "$SKILL_DIR/scripts/list_knowledge_bases.py" list

# 创建知识库（默认 MifyRAG 引擎，团队可见）
python3 "$SKILL_DIR/scripts/list_knowledge_bases.py" create \
  --name "知识库名称" \
  --description "描述" \
  --permission all_team_members

# 创建 MiBRAG 知识库
python3 "$SKILL_DIR/scripts/list_knowledge_bases.py" create \
  --name "名称" --description "描述" --provider mibrag

# 查看知识库内文档
python3 "$SKILL_DIR/scripts/list_knowledge_bases.py" docs --kb "名称"
python3 "$SKILL_DIR/scripts/list_knowledge_bases.py" docs --kb "名称" --feishu-only
```

## 3. 上传文档

### 本地文件上传

```bash
python3 "$SKILL_DIR/scripts/create_documents.py" local --kb "名称" --dir ./docs
```

支持的文件类型：`.txt`、`.md`、`.pdf`、`.html`、`.xlsx`、`.docx`、`.csv`

### 飞书文档导入（3 步流程）

```bash
# 步骤 1：验证飞书授权
python3 "$SKILL_DIR/scripts/preflight.py" --need-email --verify-feishu
# feishu_bound: true 才继续

# 步骤 2：爬取飞书链接（先检查是否有缓存）
python3 "$SKILL_DIR/scripts/create_documents.py" status --url "https://mi.feishu.cn/wiki/TOKEN"
# 无缓存则爬取
python3 "$SKILL_DIR/scripts/create_documents.py" crawl --urls "https://mi.feishu.cn/wiki/TOKEN"

# 步骤 3：上传到知识库（自动设置 3 天自动同步）
python3 "$SKILL_DIR/scripts/create_documents.py" feishu --kb "名称" --urls "https://..."
```

爬取选项：
- `--timeout 600`：超时调大（默认 180 秒）
- `--max-depth 8`：加大 Wiki 递归深度（默认 4）

## 4. 更新文档

```bash
# 本地文件（自动检测 SHA256 变更，跳过未变更文件）
python3 "$SKILL_DIR/scripts/update_documents.py" local --kb "名称" --dir ./docs

# 同步 KB 内所有飞书文档（推荐）
python3 "$SKILL_DIR/scripts/update_documents.py" feishu-sync --kb "名称" --all

# 设置飞书文档自动同步频率（单位：天）
python3 "$SKILL_DIR/scripts/update_documents.py" set-frequency --kb "名称" --frequency 3 --doc-ids DOC_ID
```

## 5. 搜索知识库

```bash
# 基本搜索（hybrid_search + reranking，返回 top 5）
python3 "$SKILL_DIR/scripts/search_knowledge_base.py" --kb "名称" --query "关键词"

# 调整返回数量
python3 "$SKILL_DIR/scripts/search_knowledge_base.py" --kb "名称" --query "查询" --top-k 10

# 关闭重排
python3 "$SKILL_DIR/scripts/search_knowledge_base.py" --kb "名称" --query "查询" --no-rerank

# 指定 Profile
python3 "$SKILL_DIR/scripts/search_knowledge_base.py" --kb "名称" --query "查询" --profile team-space
```

搜索技巧：
- 每次用 2–3 个关键词，短而精准
- 如 `"配置 API 路径"` 而非长句

## 6. 状态管理

```bash
# 查看搜索白名单
python3 "$SKILL_DIR/scripts/list_knowledge_bases.py" search-config

# 状态同步（将本地与远端对齐）
python3 "$SKILL_DIR/scripts/list_knowledge_bases.py" sync-state --kb "名称"

# 清除本地状态
python3 "$SKILL_DIR/scripts/list_knowledge_bases.py" purge --kb "名称"

# 清除飞书爬取缓存
python3 "$SKILL_DIR/scripts/create_documents.py" purge-feishu --token TOKEN
```

## 常见问题排查

| 问题 | 原因 | 解决方案 |
|------|------|----------|
| `Configuration not found` | 未创建 `~/.mify/config.json` | 按配置指南创建 |
| `Feishu authorization required` | 飞书未授权 | 运行 `preflight --verify-feishu`，打开 `feishu_auth_url` 完成授权 |
| 爬取超时 | 默认 180s 不够 | 加 `--timeout 600` |
| Wiki 文档遗漏 | 目录层级太深 | 加 `--max-depth 8` |
| 搜索返回空 | 关键词太长或文档未建索引 | 换 2-3 词短关键词；等待几分钟建立索引 |
| 重复上传 | - | 不会重复，飞书文档以 `doc_token` 去重，本地文件以 SHA256 去重 |
