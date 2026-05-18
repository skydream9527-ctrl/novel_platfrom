# Mify 配置指南

## 配置分层

### 全局配置（禁止提交）

路径：`~/.mify/config.json`

```json
{
  "email": "your-name@xiaomi.com",
  "default_profile": "default-space",
  "profiles": {
    "default-space": { "api_key": "dataset-xxxxxxxx" }
  }
}
```

- 存放个人敏感信息（API Key、邮箱）
- 每位成员在自己本机维护，不共享、不提交

### 项目级配置（可提交）

路径：`.mify/config.json`（项目根目录）

```json
{
  "default_profile": "default-space",
  "search_profiles": ["default-space"]
}
```

- 只含非敏感设置，团队共享搜索配置
- 可提交到代码仓库

### .gitignore（自动生成，可提交）

路径：`.mify/.gitignore`

```
state/**/*.tmp
```

## 获取 API Key

前往：https://mify.mioffice.cn/datasets?category=api

格式为：`dataset-xxxxxxxxxxxxxxxx`

## 多 Profile 配置

多个团队空间时在 `~/.mify/config.json` 中定义多个 Profile：

```json
{
  "email": "your-name@xiaomi.com",
  "default_profile": "my-space",
  "profiles": {
    "my-space":   { "api_key": "dataset-aaa" },
    "team-space": { "api_key": "dataset-bbb" }
  }
}
```

项目配置中设置跨 Profile 搜索：

```json
{
  "search_profiles": ["my-space", "team-space"]
}
```

## 数据存储目录说明

| 路径 | 可提交 | 说明 |
|------|--------|------|
| `~/.mify/config.json` | 否 | 个人配置：email、API Key |
| `~/.mify/state/{profile}/kb-registry.json` | 否 | 知识库列表缓存 |
| `~/.mify/state/{profile}/feishu-{token}.json` | 否 | 飞书爬取结果（3天过期） |
| `.mify/config.json` | 是 | 项目设置：default_profile、search_profiles |
| `.mify/.gitignore` | 是 | 自动生成 |
| `.mify/state/{profile}/{kb_id}.json` | 是 | 本地文件上传追踪状态 |
