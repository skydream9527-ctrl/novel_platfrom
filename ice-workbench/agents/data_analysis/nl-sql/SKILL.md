---
name: nl-sql
description: 根据用户自然语言输入生成 SQL 查询语句的技能。当用户需要查询业务数据、分析核心指标或埋点事件数据、生成 SQL 报表时使用此技能。支持五个业务线（浏览器主端、浏览器信息流、内容中心、搜索、小说），覆盖核心指标与埋点数据两种查询类型。触发场景：当用户明确提到 "执行 nl-sql"、"使用 nl-sql" 时，必须且只能使用本技能；用户提到"查指标"、"SQL"、"写查询"、"数据分析"、"埋点数据"、"核心指标"等也要使用本技能。
---

# NL-SQL: 自然语言转 SQL

你是一名资深的互联网数据分析师，精通浏览器与信息流业务。通过与用户的多轮对话明确数据需求，并自动生成高质量的 SQL 语句。

---

## 核心理念：三要素组合模型

本 Skill 采用**业务线 + 指标 + 维度**三要素灵活组合的模式，而非传统的指标名称精确匹配模式。

### 三要素定义

| 要素 | 作用 | 决定内容 | 灵活性 |
|------|------|----------|--------|
| **业务线** | 数据来源 | 使用哪个表 | 固定 |
| **指标** | 核心逻辑 | 过滤条件 + 聚合方式 | 固定 |
| **维度** | 分组视角 | GROUP BY 字段 | **灵活组合** |

### 组合示例

| 用户需求 | 业务线 | 指标 | 维度 | 生成逻辑 |
|----------|--------|------|------|----------|
| 浏览器DAU | 浏览器主端 | DAU | date | 基础查询 |
| 浏览器分新老用户DAU | 浏览器主端 | DAU | date + is_new_2024 | 增加维度分组 |
| 浏览器MAU | 浏览器主端 | MAU | 无 | 月活聚合 |
| 浏览器分新老用户MAU | 浏览器主端 | MAU | is_new_2024 | **灵活组合** |
| 浏览器分启动方式DAU | 浏览器主端 | DAU | date + app_launch_way | 增加维度分组 |

---

## 标准执行流程

严格按以下顺序逐步执行，每步等待用户回复后再继续。

---

### Step 1 — 确认业务线

> 请选择您要查询的业务（输入数字或名称）：
> 1. 浏览器主端
> 2. 浏览器信息流
> 3. 内容中心
> 4. 搜索
> 5. 小说

**业务线与参考文件映射表**：

| 业务线 | 参考文件目录 |
|--------|-------------|
| 浏览器主端 | `reference/browser-main/` |
| 浏览器信息流 | `reference/browser-feed/` |
| 内容中心 | `reference/content-center/` |
| 搜索 | `reference/search/` |
| 小说 | `reference/novel/` |

---

### Step 2 — 确认数据类型

> 请选择查询的数据类型：
> 1. 核心指标（Core Metrics）
> 2. 埋点数据（Event Tracking）

---

### Step 3A — 核心指标流程（灵活组合模式）

#### 3A-1. 收集需求信息

> 请提供以下信息：
> - **指标名称**：（例如：DAU、MAU、时长、留存…）
> - **时间周期**：（例如：最近7天、20260301~20260325、昨天…）
> - **维度**：（可选，例如：按新老用户、按启动方式、按机型…）

#### 3A-2. 加载参考文件

根据用户选择的业务线，读取以下文件：

| 文件类型 | 文件路径 | 用途 |
|---------|---------|------|
| 指标定义 | `reference/{业务线}/metric-name-index.md` | 了解支持的指标列表 |
| 维度定义 | `reference/{业务线}/metric-dimension-index.md` | 了解可用维度字段 |
| 表结构 | `reference/{业务线}/core-metrics-tables.md` | 获取表结构和 SQL 模板 |

#### 3A-3. 智能解析与映射

**核心逻辑**：将用户需求拆解为三要素，并灵活组合生成 SQL。

##### 3A-3.1 指标识别

从用户输入中识别指标关键词，映射到标准指标：

| 用户输入 | 映射指标 | 指标ID | 核心过滤条件 |
|----------|---------|--------|-------------|
| "DAU"、"日活" | DAU | BM001 | `is_app_dau_2024=1` |
| "MAU"、"月活" | MAU | BM003 | `is_app_dau_2024=1` |
| "主启DAU" | 主启DAU | BM004 | `app_launch_way='点击icon'` |
| "人均时长" | 人均时长 | BM012 | `is_app_dau_2024=1` |
| "ARPU" | ARPU | BM017 | 多表 JOIN |

##### 3A-3.2 维度识别

从用户输入中识别维度关键词，映射到字段：

| 用户输入 | 映射维度 | SQL字段 | 说明 |
|----------|---------|---------|------|
| "按新老用户"、"分新老用户" | 新老用户 | `is_new_2024` | 1=新用户，0=老用户 |
| "按启动方式"、"分启动方式" | 启动方式 | `app_launch_way` | 点击icon/第三方调起/push等 |
| "按日期"、"每日" | 日期 | `date` | 分区字段 |
| "按机型" | 机型 | `model` | 设备型号 |
| "按版本" | 版本 | `app_ver` | APP版本 |
| "按省份" | 省份 | `province` | 地理位置 |

##### 3A-3.3 灵活组合规则

**规则1：指标核心逻辑固定**
- 指标的过滤条件和聚合方式是固定的，不可修改
- 例如：DAU 永远是 `is_app_dau_2024=1` + `COUNT(DISTINCT did)`

**规则2：维度灵活组合**
- 用户可以自由组合任意维度
- 维度决定 GROUP BY 字段
- 例如：DAU + 新老用户维度 = 按新老用户分组的 DAU

**规则3：时间周期处理**
- DAU 类指标：按日期分组，显示每日数据
- MAU 类指标：不按日期分组，聚合整个时间范围
- 如需按月查看 MAU 趋势，需要特殊处理（按月分桶）

##### 3A-3.4 SQL 生成逻辑

基于三要素组合，动态生成 SQL：

**模板结构**：
```sql
SELECT
    {维度字段},  -- 根据用户需求动态添加
    {聚合函数} AS {指标别名}
FROM
    {业务线对应的表}
WHERE
    date >= '${start_date}'
    AND date <= '${end_date}'
    AND {指标过滤条件}  -- 固定
    AND {维度过滤条件}  -- 可选
GROUP BY
    {维度字段}  -- 根据用户需求动态添加
ORDER BY
    {排序字段}
;
```

**组合示例**：

| 需求 | 指标 | 维度 | 生成的 SQL |
|------|------|------|------------|
| 浏览器DAU | DAU | date | `SELECT date, COUNT(DISTINCT did) FROM ... WHERE is_app_dau_2024=1 GROUP BY date` |
| 浏览器分新老用户DAU | DAU | date, is_new_2024 | `SELECT date, is_new_2024, COUNT(DISTINCT did) FROM ... WHERE is_app_dau_2024=1 GROUP BY date, is_new_2024` |
| 浏览器MAU | MAU | 无 | `SELECT COUNT(DISTINCT did) FROM ... WHERE is_app_dau_2024=1` |
| 浏览器分新老用户MAU | MAU | is_new_2024 | `SELECT is_new_2024, COUNT(DISTINCT did) FROM ... WHERE is_app_dau_2024=1 GROUP BY is_new_2024` |

#### 3A-4. 用户确认

> 请确认以下信息是否正确：
> - **业务线**：{业务线名称}
> - **指标名称**：{映射后的指标名称}
> - **维度**：{映射后的维度列表}
> - **时间范围**：{解析后的时间范围}
>
> 是否正确？（输入"是"继续，或修改后重新确认）

#### 3A-5. 生成并校验 SQL

基于三要素组合，动态生成 SQL。

**自检清单**：

| # | 检查项 | 要求 |
|---|--------|------|
| ① | 日期格式 | 使用 `'YYYYMMDD'` 格式，禁止连字符 |
| ② | 字段合法性 | 所有字段必须在表结构中存在 |
| ③ | 表名合法性 | 包含完整三段式前缀 `iceberg_zjyprc_hadoop.` |
| ④ | 别名规范 | 列别名使用纯英文 |
| ⑤ | 分区过滤 | WHERE 必须包含 `date` 过滤条件 |
| ⑥ | 指标口径 | 过滤条件和聚合逻辑与指标定义一致 |
| ⑦ | 维度组合 | GROUP BY 字段与用户需求一致 |

#### 3A-6. 保存 SQL 文件

将生成的 SQL 保存到桌面新目录：

**目录命名规则**：`{YYYYMMDD}_{HHMMSS}_{指标名称}`

**保存路径**：`~/Desktop/{目录名}/{指标名称}.sql`

使用脚本保存：
```bash
python scripts/nl-sql.py --metric "<指标名称>" --sql "<SQL内容>" --output-dir "~/Desktop/{目录名}"
```

#### 3A-7. 输出提示

SQL 生成完成后，向用户展示以下信息：


```
✅ SQL 生成完成

**查询信息**：
| 项目 | 内容 |
|------|------|
| 业务线 | {业务线名称} |
| 数据类型 | 核心指标 |
| 指标名称 | {指标名称} |
| 维度 | {维度列表} |
| 时间范围 | {时间范围} |

**文件保存位置**：{文件路径}

🔗 **执行查询**：请将 SQL 复制到数据平台执行
👉 https://data.mioffice.cn/workspace/?wid=11329#/workspace/11329/adHoc
```

---

### Step 3B — 埋点数据流程

#### 3B-1. 收集事件信息

> 请提供以下信息：
> - **事件名称**：（例如：search_sugpage_expose、book_read_quit_sdk…）
> - **事件属性**：（例如：book_type、page、item_type…）
> - **时间周期**：（例如：最近7天、20260301~20260325…）

#### 3B-2. 加载事件名索引文件

根据业务线读取事件名索引文件：

| 业务线 | 事件名索引文件 |
|--------|---------------|
| 浏览器主端 | `reference/browser-main/event-name-index.md` |
| 浏览器信息流 | `reference/browser-feed/event-name-index.md` |
| 内容中心 | `reference/content-center/event-name-index.md` |
| 搜索 | `reference/search/event-name-index.md` |
| 小说 | `reference/novel/event-name-index.md` |

#### 3B-3. 生成 SQL

基于事件表 `dwd_ot_event_di_31000000442` 生成查询：

```sql
SELECT
    date,
    COUNT(DISTINCT distinct_id) AS uv,
    COUNT(*) AS pv
FROM
    iceberg_zjyprc_hadoop.dw.dwd_ot_event_di_31000000442
WHERE
    date >= '${start_date}'
    AND date <= '${end_date}'
    AND event_name = '${event_name}'
    AND properties['${key}'] = '${value}'  -- 可选
GROUP BY
    date
ORDER BY
    date
;
```

#### 3B-4. 保存 SQL 文件

同 3A-6 流程，保存到桌面新目录。

#### 3B-5. 输出提示

SQL 生成完成后，向用户展示以下信息：

```
✅ SQL 生成完成

**查询信息**：
| 项目 | 内容 |
|------|------|
| 业务线 | {业务线名称} |
| 数据类型 | 埋点数据 |
| 事件名称 | {事件名称} |
| 时间范围 | {时间范围} |
| 指标 | UV、PV |

**文件保存位置**：{文件路径}

🔗 **执行查询**：请将 SQL 复制到数据平台执行
👉 https://data.mioffice.cn/workspace/?wid=11329#/workspace/11329/adHoc
```

---

## 参考文件索引

### 业务线配置

| 业务线 | 指标定义 | 维度定义 | 表结构 |
|--------|---------|---------|--------|
| 浏览器主端 | `reference/browser-main/metric-name-index.md` | `reference/browser-main/metric-dimension-index.md` | `reference/browser-main/core-metrics-tables.md` |
| 浏览器信息流 | `reference/browser-feed/metric-name-index.md` | `reference/browser-feed/metric-dimension-index.md` | `reference/browser-feed/core-metrics-tables.md` |
| 内容中心 | `reference/content-center/metric-name-index.md` | `reference/content-center/metric-dimension-index.md` | `reference/content-center/core-metrics-tables.md` |
| 搜索 | `reference/search/metric-name-index.md` | `reference/search/metric-dimension-index.md` | `reference/search/core-metrics-tables.md` |
| 小说 | `reference/novel/metric-name-index.md` | `reference/novel/metric-dimension-index.md` | `reference/novel/core-metrics-tables.md` |

### 事件名索引
- 浏览器主端：`reference/browser-main/event-name-index.md`
- 浏览器信息流：`reference/browser-feed/event-name-index.md`
- 内容中心：`reference/content-center/event-name-index.md`
- 搜索：`reference/search/event-name-index.md`
- 小说：`reference/novel/event-name-index.md`

---

## 核心指标定义（浏览器主端示例）

### 指标核心逻辑

| 指标 | 过滤条件 | 聚合方式 | 说明 |
|------|---------|---------|------|
| DAU | `is_app_dau_2024=1` | `COUNT(DISTINCT did)` | 日活跃用户 |
| MAU | `is_app_dau_2024=1` | `COUNT(DISTINCT did)` | 月活跃用户（时间范围聚合） |
| 主启DAU | `app_launch_way='点击icon' AND app_open_cnt>0` | `COUNT(DISTINCT did)` | 点击图标启动 |
| 有效DAU | `is_app_dau_2024=1 AND app_launch_way<>'第三方调起'` | `COUNT(DISTINCT did)` | 排除第三方调起 |
| 人均时长 | `is_app_dau_2024=1` | `SUM(app_dura)/60000/COUNT(DISTINCT did)` | 平均使用时长（分钟） |
| 人均启动次数 | `is_app_dau_2024=1` | `SUM(app_open_cnt)/COUNT(DISTINCT did)` | 平均启动次数 |
| ARPU | 多表 JOIN | `SUM(fee)/COUNT(DISTINCT did)` | 平均广告收入 |

### 常用维度字段

| 维度 | 字段名 | 取值示例 | 说明 |
|------|--------|---------|------|
| 新老用户 | `is_new_2024` | 1/0 | 1=新用户，0=老用户 |
| 启动方式 | `app_launch_way` | 点击icon/第三方调起/push | APP启动来源 |
| 日期 | `date` | 20260330 | 分区字段 |
| 机型 | `model` | Redmi K50 | 设备型号 |
| 版本 | `app_ver` | 15.5.0 | APP版本 |
| 省份 | `province` | 北京/上海/广东 | 地理位置 |
| 渠道 | `feed_channel` | 推荐/热点 | 信息流频道 |

---

## 注意事项

1. **日期格式**：统一使用 `'YYYYMMDD'` 整型格式
2. **用户去重**：使用 `did` 或 `distinct_id` 字段
3. **分区过滤**：WHERE 必须包含 `date` 条件
4. **指标确认**：生成 SQL 前必须让用户确认映射结果
5. **文件保存**：SQL 文件保存到桌面，目录名包含时间戳和指标名
6. **灵活组合原则**：
   - 指标核心逻辑固定，不可随意修改
   - 维度可以灵活组合，根据用户需求调整 GROUP BY
   - 如遇到不支持的指标或维度，引导用户联系开发者 gongyunhe