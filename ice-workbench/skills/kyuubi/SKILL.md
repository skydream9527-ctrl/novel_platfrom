---
name: kyuubi
description: |
  使用 kyuubi-cli 执行 Kyuubi SQL 查询、更新和删除操作，以及表元数据管理和 workspace 验证。

  Triggers when user mentions:
  - "查一下"、"查询一下"、"帮我查"、"执行 SQL"
  - "查数据"、"数据查询"、"跑查询"
  - "kyuubi"、"kyuubi-cli"
  - "查一下数据"、"跑个 SQL"
  - "查看表"、"搜索表"、"表结构"、"看看表"、"表信息"
  - "查询历史"、"查看历史"、"历史记录"、"查询记录"
  - "workspace"、"工作空间"、"切换空间"、"切换区域"
  - "配置"、"环境"、"查看配置"、"有哪些环境"、"配置了哪些"
  - "安装 kyuubi"、"更新 kyuubi"、"卸载 kyuubi"
---

# Kyuubi CLI Skill

基于官方 `kyuubi-cli` 工具，通过 Kyuubi 网关执行 SQL 查询。

> 文档来源：https://git.n.xiaomi.com/olap/kyuubi-cli

---

## 版本要求

**最低版本：0.2.1**

使用本 skill 前，AI **必须**检查版本。低于最低要求则**拒绝执行并提示用户升级**，不得自动升级。

```
GOOD: "当前版本 0.1.1，最低要求 0.2.1。请先升级：
       pipx upgrade kyuubi-cli --index-url https://pkgs.d.xiaomi.net/artifactory/api/pypi/pypi-virtual/simple"
BAD:  自动执行升级命令
BAD:  版本过低仍继续执行
```

---

## 重要提示：配置查询

> **当用户询问配置、环境、workspace 时，必须使用命令查询，禁止读取配置文件。**

| 操作 | 正确方式 | 错误方式 |
|------|---------|---------|
| 查看当前配置 | `kyuubi config show` | 读取 `~/.kyuubi/config.yml` |
| 查看 JSON 格式 | `kyuubi config show --format json` | 读取配置文件 |
| 验证 workspace | `kyuubi workspace validate` | 读取配置文件 |

```
GOOD: 用户问"配置了哪些环境" → 执行 kyuubi config show
BAD:  用户问"配置了哪些环境" → cat ~/.kyuubi/config.yml
BAD:  用户问"配置了哪些环境" → Read ~/.kyuubi/config.yml
```

**原因：** 在权限受限的环境中（如容器中的 Agent），直接读取配置文件会导致 Permission denied 错误。`kyuubi config show` 通过 CLI 安全访问配置，不受文件权限限制。

---

## 环境准备

### 安装

**前置条件：** Python 3.12+

使用 pipx 安装（自动创建独立虚拟环境，不污染系统 Python）：

**安装 pipx（如未安装）：**
```bash
# macOS
brew install pipx && pipx ensurepath

# Linux
python3 -m pip install --user pipx
python3 -m pipx ensurepath

# Windows
scoop install pipx
pipx ensurepath
```
安装后需重新打开终端。

**安装/升级 kyuubi-cli：**
```bash
pipx install kyuubi-cli --pip-args="-i https://pkgs.d.xiaomi.net/artifactory/api/pypi/pypi-virtual/simple"
pipx upgrade kyuubi-cli --index-url https://pkgs.d.xiaomi.net/artifactory/api/pypi/pypi-virtual/simple
```

验证安装：
```bash
which kyuubi    # 确认使用的是 pipx 版本（路径含 .local/pipx/venvs）
kyuubi --version
```

**AI 行为：** 检测到 `kyuubi` 命令不存在时，建议用户使用 pipx 安装。

### 初始化配置

```bash
kyuubi config init                      # 生成配置文件模板（已存在时提示二次确认）
kyuubi config init --force              # 跳过确认直接覆盖（自动化/Agent 场景使用）
kyuubi config add-workspace --region chnbj --workspace 10000 --apikey YOUR_KEY
kyuubi config show                      # 验证配置
```

> **注意：** `config init` 在配置文件已存在时会交互式询问是否覆盖。
> 在自动化或 Agent 场景中，使用 `--force` / `-f` 跳过确认直接覆盖。

配置文件 `~/.kyuubi/config.yml` 结构：

```yaml
auth:
  regions:
    chnbj:
      workspaces:
        "10000":
          apikey: "your-api-key"
    chntj:
      workspaces:
        "10136":
          apikey: "another-api-key"

session:
  query.engine: "auto"
  query.timeout: 120
  query.poll_interval: 2.0
  query.tag: null
  query.limit: 10000
```

**无默认 region/workspace。** 每条命令都必须显式传入 `--region` 和 `--workspace`，不可省略。

---

## AI 使用规范

**HARD GATE：** 本 skill 只通过 `kyuubi-cli` 执行 SQL 数据操作。
- 不执行任何 DDL（CREATE TABLE / DROP TABLE / ALTER TABLE）
- `--region` 和 `--workspace` 是必填参数，不能省略，不确定时必须询问用户
- 不猜测 `--catalog`，不确定时必须询问用户
- `sql update` / `sql delete` 是危险操作，执行后**不会立即运行 SQL**，而是暂存到 pending 表并返回 `[PENDING]` 提示和 op-id
- 收到 `[PENDING]` 提示后，**必须**向用户完整展示 SQL 内容，明确询问用户是否确认执行
- 只有用户在对话中**明确回复确认**后，才可调用 `kyuubi sql confirm <op-id>`
- **禁止**在同一步骤或同一轮工具调用中连续执行 update/delete 和 confirm，中间必须有用户的明确回复
- `sql confirm` 与 `sql update` / `sql delete` 同等危险级别，不得自动调用
- `config init` 在配置文件已存在时，**必须先向用户确认是否覆盖，确认后才能带 `--force` 执行**，禁止自行决定覆盖

```
GOOD: 检测到配置文件已存在，询问用户"是否覆盖现有配置？" → 用户确认后执行 kyuubi config init --force
BAD:  直接执行 kyuubi config init --force（未经用户确认）
BAD:  执行 kyuubi config init（让 CLI 交互式询问，AI 无法处理交互）
```

### 查询前确认参数

执行 SQL 前**必须**确认以下参数：

| 参数 | 是否必填 | 说明 |
|------|---------|------|
| `--region` | **必填** | 服务区域，如 `chnbj`、`chntj`、`sg` |
| `--workspace` | **必填** | Workspace ID，如 `10000`、`10136` |
| `--catalog` | 通常必填 | 目标数据源，不确定时询问用户 |
| `--schema` | 可选 | 可通过 `--catalog mydb.public` 点号写法代替 |

```
GOOD: 用户说"查一下北京的订单" → 先确认 region/workspace/catalog 再执行
BAD:  省略 --region 或 --workspace
BAD:  直接猜测 --catalog
```

### SQL 语法与引擎选择

根据 catalog 前缀选择语法，查询时**必须通过 `--engine` 指定引擎**（默认 `auto` 不会自动识别）：

| catalog 前缀 | SQL 语法 | `--engine`（按优先级） |
|-------------|---------|------|
| `doris_*`（单集群） | Doris 语法 | `--engine doris` |
| `doris_*` + `doris_*` 跨集群联查 | Spark SQL | `--engine presto` 或 `--engine spark` |
| `iceberg_*` / `hive_*` | Spark SQL | `--engine presto` 或 `--engine spark` |

不同 `doris_*` catalog 对应不同集群，**不能跨集群使用 doris 引擎**。

**Doris 引擎限制：** Doris 2.x 不支持多 catalog，`--engine doris` 只能访问该单一集群内部的 schema/table，无法执行 `SHOW CATALOGS`。

**查询可用 Catalog 时必须使用 presto 引擎：**
```bash
kyuubi sql query 'SHOW CATALOGS' --engine presto --region <region> --workspace <workspace>
```
- **不要用 `--engine spark`**：spark catalog 为懒加载，未激活的 catalog 不会出现在列表
- **不要用 `--engine doris`**：Doris 2.x 不支持多 catalog，无法执行 SHOW CATALOGS

```
GOOD: kyuubi sql query "..." --catalog doris_xxx --engine doris --region chntj --workspace 10136
GOOD: kyuubi sql query "..." --catalog iceberg_xxx --engine presto --region chnbj --workspace 10000
GOOD: kyuubi sql query 'SHOW CATALOGS' --engine presto --region chnbj --workspace 10000
BAD:  kyuubi sql query "..." --catalog doris_xxx  （缺少 --region、--workspace、--engine）
BAD:  kyuubi sql query 'SHOW CATALOGS' --engine spark  （catalog 懒加载，结果不完整）
BAD:  kyuubi sql query 'SHOW CATALOGS' --engine doris  （Doris 2.x 不支持多 catalog）
```

### 输出格式

- 交互展示 → 默认 `table`
- 需要程序解析 → `--format json`
- 导出数据 → `--format csv`（仅 `tables list`）
- 调试 → `--verbose`

---

## 命令速查

每个子命令的完整参数请通过 `kyuubi <cmd> -h` 查看。

```bash
# SQL 查询（--region 和 --workspace 必填）
kyuubi sql query "SELECT ..." --catalog mydb --region chnbj --workspace 10000
kyuubi sql query "..." --catalog mydb.public --region chnbj --workspace 10000 --format json
kyuubi sql query "..." --catalog doris_xxx --engine doris --region chntj --workspace 10136

# SQL 更新 / 删除（两步确认流程）
# 第一步：暂存操作（不执行，返回 op-id）
kyuubi sql update "INSERT INTO t VALUES (...)" --catalog mydb --region chnbj --workspace 10000
kyuubi sql delete "DELETE FROM t WHERE id=1" --catalog mydb --region chnbj --workspace 10000
# 第二步：用户确认后执行
kyuubi sql confirm op-8a3f1b2c    # 执行已暂存的操作
kyuubi sql cancel op-8a3f1b2c     # 取消已暂存的操作
kyuubi sql pending                 # 查看所有待确认操作

# 表元数据（list 和 desc 需要 --region 和 --workspace）
kyuubi tables list --region chnbj --workspace 10000
kyuubi tables list --region chnbj --workspace 10000 --keyword audit --format csv
kyuubi tables search proxy                           # 本地缓存搜索，无需 region/workspace
kyuubi tables search orders --limit 50
kyuubi tables desc mydb.public.users --region chnbj --workspace 10000
kyuubi tables desc mydb.public.users --region chnbj --workspace 10000 --refresh
kyuubi tables history --limit 10
kyuubi tables cache

# Workspace 管理
kyuubi workspace info
kyuubi workspace validate

# 配置管理
kyuubi config init                      # 已存在时提示二次确认
kyuubi config init --force              # 跳过确认直接覆盖（自动化场景）
kyuubi config show
kyuubi config show --format json
kyuubi config add-workspace --region chnbj --workspace 10000 --apikey YOUR_KEY
kyuubi config add-workspace --region chnbj --workspace 10000 --apikey NEW_KEY --force
kyuubi config remove-workspace --region chnbj --workspace 10000
kyuubi config set session.query.timeout 300
kyuubi config set session.query.engine spark
kyuubi config edit
```

**本地缓存：** `~/.kyuubi/kyuubi.db`

| 缓存表 | 来源 | TTL | 用途 |
|--------|------|-----|------|
| `table_metadata` | `tables list` 拉取 | 7 天 | 表元数据（名称/类型/owner/描述），供 `tables search` 搜索 |
| `schema_cache` | `tables desc` 查询 | 7 天 | 表结构（列名/类型/注释） |
| `query_history` | `sql query/update/delete` 自动记录 | 30 天 | 查询历史 |
| `workspace_info` | 连接时自动校验 | 永久 | Workspace 校验结果 |

**搜索工作流：** `tables search` 仅搜索本地缓存，首次使用需先执行 `tables list` 拉取数据。

---

## 使用场景示例

### 审计日志分析

```bash
kyuubi sql query "SELECT COUNT(*) as cnt FROM iceberg_zjyprc_hadoop.olap.trino_audit_log WHERE date = CURRENT_DATE" \
  --catalog iceberg_zjyprc_hadoop --engine presto --region chnbj --workspace 10000

kyuubi sql query "SELECT inputs, COUNT(*) as cnt FROM iceberg_zjyprc_hadoop.olap.trino_audit_log WHERE date = CURRENT_DATE GROUP BY inputs ORDER BY cnt DESC LIMIT 10" \
  --catalog iceberg_zjyprc_hadoop --engine presto --region chnbj --workspace 10000
```

### 表结构探索

```bash
kyuubi tables list --region chnbj --workspace 10000
kyuubi tables search audit --catalog iceberg_zjyprc_hadoop
kyuubi tables desc iceberg_zjyprc_hadoop.olap.trino_audit_log --region chnbj --workspace 10000
```

### 多 workspace 场景

```bash
# 北京 workspace
kyuubi sql query "SELECT * FROM t" --catalog mydb --region chnbj --workspace 10000

# 天津 workspace（不同 token）
kyuubi sql query "SELECT * FROM t" --catalog doris_c4prc_canoe --engine doris --region chntj --workspace 10136
```

### 配置查询

```bash
# 查看所有配置的 region 和 workspace
kyuubi config show

# JSON 格式输出（适合程序解析）
kyuubi config show --format json

# 验证 workspace 连通性
kyuubi workspace validate
```

---

## 权限错误处理

遇到权限不足时，使用权限申请地址：

```
https://data.mioffice.cn/data/#/safeCenter/requestAuth/Alpha?from={数据源类型}.{集群}.{库名}.{表名}
```

**转换规则：** catalog 下划线在地址中转为点号。

| Catalog | 地址参数 |
|---------|---------|
| `iceberg_zjyprc_hadoop.miuiads.dwd_fact_ad_event_all_di` | `iceberg.zjyprc-hadoop.miuiads.dwd_fact_ad_event_all_di` |
| `doris_akprc_xiaomi.db.table` | `doris.akprc-xiaomi.db.table` |

---

## 常见错误处理

### No API key configured

```
Configuration error: No API key configured for region 'chntj' and workspace '10136'.
Run: kyuubi config add-workspace --region chntj --workspace 10136 --apikey YOUR_KEY
```

解决：按提示执行 `config add-workspace`。

### No region / No workspace specified

```
Configuration error: No region specified. Please provide --region.
Configuration error: No workspace specified. Please provide --workspace.
```

解决：命令中补充 `--region` 和 `--workspace`，两者均为必填。

### Workspace 验证失败

```
Workspace validation failed.
  Config workspace: '10000'
  Token belongs to: '10192' (OLAP引擎私有空间)
```

原因：token 实际所属 workspace 与命令中指定的不一致。

解决：
```bash
kyuubi config remove-workspace --region chnbj --workspace 10000
kyuubi config add-workspace --region chnbj --workspace 10192 --apikey YOUR_KEY
```

### Region has multiple workspaces / not found

```
Configuration error: Region 'chnbj' has multiple workspaces configured. Please specify --workspace: 10000, 20000
```

解决：在命令中加上正确的 `--workspace`。

### 查询超时

解决：`kyuubi config set session.query.timeout 300`，或加 `--verbose` 排查。

### kyuubi 命令未找到

```bash
# 检查 pipx 安装的命令是否在 PATH 中
pipx ensurepath
# 重新打开终端后验证
which kyuubi
kyuubi --version
```

---

## 区域列表

| 区域 | 代号 |
|------|------|
| 中国天津测试 | `staging` |
| 中国天津 | `chntj` |
| 中国北京 | `chnbj` |
| 中国上海 | `chnsh` |
| 中国上海2 | `chnsh2` |
| 中国天津自驾合规区 | `ksytjv` |
| 印度普纳 | `indpn` |
| 荷兰阿姆斯特丹 | `nlams` |
| 俄罗斯莫斯科 | `rusmos` |
| 新加坡 | `sg` |
| 新加坡自驾合规区 | `alisgp` |
| 德国法兰克福 | `de` |
