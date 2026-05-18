---
name: knowledge_qa
description: 知识库搜索与问答
triggers:
  - "知识库"
  - "搜索文档"
  - "飞书"
  - "查资料"
  - "文档"
  - "wiki"
  - "找一下"
allowed_tools:
  - search_knowledge
  - feishu_read
  - feishu_publish
constraints:
  - 回答需标注信息来源
  - 检索无结果时明确告知
  - 不编造知识库中不存在的内容
priority: 7
---

知识检索与问答能力：从飞书知识库和 Mify RAG 中检索信息并回答问题。

工作流程：
1. 理解用户问题
2. 选择合适的知识库进行检索
3. 基于检索结果生成回答
4. 标注来源并提供相关推荐
