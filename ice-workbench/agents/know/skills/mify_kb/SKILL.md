---
name: mify_kb
description: Mify RAG 知识库的语义检索和文档管理
triggers:
  - "搜索知识"
  - "RAG"
  - "语义搜索"
  - "mify"
  - "知识检索"
  - "查资料"
allowed_tools:
  - mify_search
  - mify_upload
constraints:
  - 操作前必须通过预检脚本验证连接
  - 搜索白名单修改需用户确认
  - 飞书相关操作需验证 feishu_bound 状态
priority: 7
---

Mify RAG 知识库语义检索能力。

搜索：使用 hybrid_search + reranking 进行语义检索
上传：支持本地文件和飞书文档作为数据源
同步：支持批量同步飞书文档到 RAG 知识库
