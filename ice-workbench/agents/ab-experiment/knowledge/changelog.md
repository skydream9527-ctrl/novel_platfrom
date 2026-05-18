# Knowledge 知识库变更日志

## v2.0 (2026-05-11) — 目录结构重组

- 按职能分层为 5 个子目录：rules/、metrics/、event_tracking/、analysis/、product_model/
- 新增 index.yaml 全局索引文件
- sql_templates/ 移入 metrics/ 子目录
- 埋点相关文件（db/yaml/readme/py）移入 event_tracking/
- CHANGELOG.md 重命名为 changelog.md（统一 snake_case）
- 同步更新 SKILL.md 中所有知识库文件路径引用

---

## page_structure.yaml 更新日志

## v1.0 (2026-04-28)
- 完成小米浏览器全部页面结构：首页、搜索首页、搜索SUG页、搜索结果页、图文详情页、沉浸式详情页、短剧详情页、我的页、任务详情页
- 完成内容中心核心页面结构：首页/推荐页、图文详情页、沉浸式详情页、短剧详情页、个人中心页、任务详情页
- 复用机制：内容中心的3个详情页复用浏览器的页面结构
- 删除冗余页面：视频详情页、小说阅读页、积分激励任务页、频道页
- 结构优化：为有明确卡片结构的页面增加 `cards` 层级
- 统一元素分类：`entries`、`content_areas`、`interactions`、`operations`

## v0.1 (2026-04-27)
- 初始骨架创建
