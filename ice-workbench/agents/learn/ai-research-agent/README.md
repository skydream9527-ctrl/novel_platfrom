# AI Research Agent

一个学习研究型 Agent，用于持续吸收文档和网站中的 AI 知识，沉淀工具与框架理解，维护最新版最佳方案，并为后续讨论提供结构化材料。

## 目标

- 接收你手动投喂的链接并提炼知识
- 定期巡检预设信息源，补充最新资讯与变化
- 将知识沉淀为主题卡片、决策记录和最佳方案
- 在高影响变化出现时，优先输出讨论点而不是直接覆盖旧结论

## 目录结构

- `AGENT.md`：Agent 角色、工作方式、讨论原则
- `config/sources.yaml`：主动巡检的信息源
- `config/topics.yaml`：重点研究主题
- `inbox/links.md`：手动投喂链接入口
- `knowledge/raw/`：原始抓取记录占位
- `knowledge/notes/`：主题知识卡片
- `knowledge/decisions/`：决策记录
- `knowledge/news-digest/`：资讯简报
- `knowledge/BEST_OPTION.md`：当前最佳方案总表
- `prompts/`：提炼、对比、讨论模板

## 工作流

1. 你把链接发给 Agent，或记录到 `inbox/links.md`
2. Agent 读取内容，提炼事实、建议、风险和讨论点
3. Agent 更新对应主题卡片
4. 如果结论变化明显，新增一条决策记录
5. Agent 更新 `knowledge/BEST_OPTION.md`

## 默认输出格式

每次学习尽量输出四部分：

1. 事实层：来源、时间、主要结论
2. 建议层：推荐做法、适用条件、风险
3. 变化层：相对已有知识的新增、修正或推翻
4. 讨论层：需要你拍板的问题

## 使用建议

- 先聚焦 `AI Agent / RAG / Eval / MCP / Tooling` 这几类主题
- 每周至少做一次资讯巡检
- 每月复盘一次 `BEST_OPTION.md`

## 自动巡检

当前仓库已包含最小可用的自动巡检脚本与调度模板：

- `scripts/check_sources.sh`：按 `config/sources.yaml` 抓取网页标题并生成巡检快照
- `scripts/generate_weekly_digest.sh`：按最新快照生成周报草稿
- `scripts/import_links.sh`：读取 `inbox/links.md` 中的链接并落盘为学习记录
- `scripts/fetch_web_page.sh`：抓取普通网页正文并保存到原始记录
- `scripts/run_learning_cycle.sh`：串联导入、巡检和周报生成的一键学习周期
- `scripts/update_change_index.sh`：为知识与原始记录生成变化索引
- `automation/launchd/com.ai-research-agent.check-sources.plist`：macOS 定时巡检模板
- `automation/launchd/com.ai-research-agent.weekly-digest.plist`：macOS 周报模板

## 运行方式

手动运行巡检：

```bash
bash scripts/check_sources.sh
```

手动生成周报：

```bash
bash scripts/generate_weekly_digest.sh
```

导入收件箱中的链接：

```bash
bash scripts/import_links.sh
```

抓取单个网页正文：

```bash
bash scripts/fetch_web_page.sh https://example.com/post
```

执行一轮完整学习周期：

```bash
bash scripts/run_learning_cycle.sh
```

更新知识变化索引：

```bash
bash scripts/update_change_index.sh
```

## 定时任务

建议频率：

- 每天 09:00：巡检信息源
- 每周一 09:30：生成周报草稿

启用 `launchd` 前，需要先把模板中的 `__PROJECT_DIR__` 替换为本项目绝对路径：

`/Users/mi/Desktop/agents/learn_agent/ai-research-agent`

然后加载：

```bash
launchctl load automation/launchd/com.ai-research-agent.check-sources.plist
launchctl load automation/launchd/com.ai-research-agent.weekly-digest.plist
```

## 当前状态

这是第一版最小可用实现，已经具备：

- 手动链接学习入口
- 知识卡片与最佳方案沉淀
- 自动巡检与链接导入脚本
- 普通网页正文抓取脚本
- 一键学习周期脚本
- 变化索引脚本
- 周报草稿生成能力
- macOS 定时任务模板
