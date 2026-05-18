# Mify 知识库概述

Mify 是小米内部基于 RAG（检索增强生成）的知识库平台，使用 MiBRAG / MifyRAG 引擎，让 AI 能够理解和检索团队私域知识。

## 核心定位

- **RAG 知识库**：所有内容经过索引，AI 可通过语义检索召回相关内容
- **私域知识接入**：支持本地文件、飞书文档、飞书 Wiki 作为数据源
- **平台地址**：https://mify.mioffice.cn/datasets

## 推荐引擎

| 引擎 | 说明 | 适用场景 |
|------|------|----------|
| MifyRAG | 默认推荐 | 通用知识检索 |
| MiBRAG | 可选 | 创建时明确指定 |

## Skill 安装

- 安装来源：[Mi Code Hub skill #99](https://micode.mioffice.cn/#/skills/99)
- 当前最新版本：**v2.3.1**（mibrag_v2 引擎支持）
- 安装命令：
  ```bash
  micode skills add ai-team/mify-knowledge-base -y           # 默认安装到 MiCode
  micode skills add ai-team/mify-knowledge-base --agent claude -y   # Claude Code
  micode skills add ai-team/mify-knowledge-base --global -y  # 全局安装（所有项目）
  ```
- Trae 中 skill 路径：`~/.trae-cn/skills/mify-knowledge-base/`

## 近期更新摘要

| 版本 | 主要变更 |
|------|---------|
| v2.3.1 | 新增 mibrag_v2 引擎支持 |
| v2.3.0 | 飞书文档上传自动去重；交互式弹窗配置体验 |
| v2.2.0 | 飞书文档一键全量同步；查看知识库文档列表 |
| v2.1.0 | 知识库创建交互精简 |
| v2.0.0 | 全面重构 |
