---
name: feishu_kb
description: 飞书知识库文档的读取、创建、更新和搜索操作
triggers:
  - "飞书"
  - "知识库"
  - "文档"
  - "wiki"
  - "feishu"
  - "写入文档"
  - "创建文档"
allowed_tools:
  - feishu_read
  - feishu_write
  - feishu_search
constraints:
  - 写入前检查飞书 CLI 认证状态
  - 优先使用 append/replace 模式
  - overwrite 模式需要用户明确确认
  - 标题层级不超过 4 层
priority: 8
---

飞书知识库操作能力。

读取：通过 feishu fetch 命令读取文档内容
写入：通过 feishu docx create/update 创建或更新文档
搜索：通过 feishu search 关键词搜索
浏览：通过 feishu wiki nodes 浏览知识库结构
