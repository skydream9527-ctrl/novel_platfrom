# 飞书知识库操作指南

飞书 CLI（`feishu`）可完整管控飞书文档、知识库、云盘等资源。

## CLI 安装与版本

```bash
# 检查版本
feishu --version

# 安装（如未安装）
npm install -g @mi/feishu@latest --registry https://pkgs.d.xiaomi.net/artifactory/api/npm/mi-npm/

# 升级
feishu update
```

## 认证

```bash
feishu auth login    # 浏览器 OAuth 登录
feishu auth status   # 查看 token 状态
feishu auth logout   # 清除 token
```

## 读取飞书文档

```bash
# 读取任意飞书资源（自动识别 URL 类型）
feishu fetch "https://mi.feishu.cn/wiki/TOKEN"
feishu fetch "https://mi.feishu.cn/docx/TOKEN"

# 下载文档中的图片
feishu fetch "https://..." --download-images ./assets
```

## 写入飞书知识库

```bash
# 创建新文档（存入个人知识库）
feishu docx create "文档标题" -c "# 内容"

# 创建文档到指定知识空间
feishu docx create "标题" -c "内容" --wiki-space SPACE_ID
feishu docx create "标题" -c "内容" --wiki-node WIKI_NODE_TOKEN

# 从文件创建
feishu docx create "标题" -f content.md --wiki-node WIKI_NODE_TOKEN

# 追加内容（推荐，非破坏性）
feishu docx update "https://..." --mode append -c "## 新章节\n内容"

# 替换内容
feishu docx update "https://..." --mode replace --select "旧内容...结尾" -c "新内容"

# 删除章节
feishu docx update "https://..." --mode delete --select-title "## 过时章节"

# 覆盖全文（破坏性，慎用）
feishu docx update "https://..." --mode overwrite --force -c "# 全新内容"
```

## 管理知识空间（Wiki）

```bash
# 列出所有知识空间
feishu wiki spaces

# 列出空间下的节点
feishu wiki nodes SPACE_ID

# 获取节点详情（包含 space_id、node_token 等）
feishu wiki get "https://mi.feishu.cn/wiki/TOKEN"

# 创建知识库页面
feishu wiki create SPACE_ID "标题" --type docx
feishu wiki create SPACE_ID "标题" --parent PARENT_NODE_TOKEN

# 重命名节点
feishu wiki rename SPACE_ID NODE_TOKEN "新标题"

# 移动节点
feishu wiki move SPACE_ID NODE_TOKEN --target-space TARGET_ID --target-parent TARGET_NODE
```

## 搜索文档

```bash
feishu search "关键词"
feishu search "关键词" --sort edit_time
feishu search --created last_30_days
```

## 权限管理

```bash
# 查看文档权限
feishu perm list TOKEN --type docx

# 添加编辑权限
feishu perm add TOKEN --type docx --member-id name@xiaomi.com --perm edit

# 删除权限
feishu perm remove TOKEN --type docx --member-id name@xiaomi.com
```

## 作为 Mify 数据源

飞书文档可作为 Mify RAG 知识库的数据源导入，详见 [../mify_knowledge_base/operations.md](../mify_knowledge_base/operations.md) 的「飞书文档导入」章节。

飞书授权：如 Mify 提示 `Feishu authorization required`，前往 https://mify.mioffice.cn/datasets/create?show-accountsetting=data-source 完成授权。
