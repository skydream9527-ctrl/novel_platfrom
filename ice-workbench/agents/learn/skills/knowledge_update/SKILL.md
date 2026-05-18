---
name: knowledge_update
description: 更新知识卡片、决策记录和最佳方案
triggers:
  - "更新知识"
  - "知识卡片"
  - "最佳方案"
  - "决策记录"
  - "对比"
  - "总结"
allowed_tools:
  - generate_digest
  - import_links
constraints:
  - 新信息如果只是补充，更新主题卡片
  - 新信息如果改变判断，新增决策记录
  - BEST_OPTION.md 只保留当前有效结论
  - 旧结论不删除，在决策记录中说明被替代原因
priority: 6
---

知识更新能力：管理知识卡片、决策记录和最佳方案体系。

更新规则：
- 补充性信息 → 更新对应主题卡片
- 判断性变化 → 新增决策记录 + 更新 BEST_OPTION.md
- 旧结论归档而非删除
