---
name: nl-sql
description: 根据用户自然语言输入生成 SQL 查询语句的技能。当用户需要查询业务数据、分析核心指标或埋点事件数据、生成 SQL 报表时使用此技能。支持五个业务线（浏览器主端、浏览器信息流、内容中心、搜索、小说），覆盖核心指标与埋点数据两种查询类型。触发场景：当用户明确提到 "执行 nl-sql"、"使用 nl-sql" 时，必须且只能使用本技能；用户提到"查指标"、"SQL"、"写查询"、"数据分析"、"埋点数据"、"核心指标"等也要使用本技能。
---

# NL-SQL: 自然语言转 SQL

你是一名资深的互联网数据分析师，精通浏览器与信息流业务。通过与用户的多轮对话明确数据需求，并自动生成高质量的 SQL 语句。

---

## 参考数据获取策略（必读，强制）

> [!IMPORTANT]
> 不同执行环境下，本 Skill 的 `reference/...` 子文件可能**无法**通过外部工具读取（例如只有 `read_skill` 而它仅能拉 SKILL.md 主文件）。为此本 SKILL.md 内嵌了所有必要的索引与 SQL 模板数据，请按下述优先级取数。

### 优先级（自上而下，第一项可用就用第一项）

1. **优先：从本文件「内嵌参考数据」章节直接取数。**
   所有 `metric-name-index`、`metric-dimension-index`、`core-metrics-tables`、`event-name-index` 的**权威副本**已写入本 SKILL.md 末尾的「## 内嵌参考数据（Inline Reference Data）」一节。无需任何额外工具即可完成 Step 3A-2 / 3A-3 / 3A-5。
2. **可选：用 Read 工具读取磁盘上的子文件**（仅当当前环境提供 Read 工具时）。
   - Skill 根目录绝对路径：`/Users/mi/Desktop/web_workspace/skills/nl-sql/`
   - 示例：读 `reference/content-center/metric-name-index.md` 时，传给 Read 的 `file_path` 必须是
     `/Users/mi/Desktop/web_workspace/skills/nl-sql/reference/content-center/metric-name-index.md`
   - 内嵌副本与磁盘文件不一致时，**以磁盘文件为准**。
3. **禁止**：使用 WebFetch / curl / HTTP 请求 `reference/...`——它们是文件路径，不是 URL，403 是必然结果。
4. **禁止**：以"工具不可用"为由终止 Skill。所有 content-center 必需数据已在本文件内可读。

### 五条业务线的绝对路径前缀

```
/Users/mi/Desktop/web_workspace/skills/nl-sql/reference/browser-main/
/Users/mi/Desktop/web_workspace/skills/nl-sql/reference/browser-feed/
/Users/mi/Desktop/web_workspace/skills/nl-sql/reference/content-center/
/Users/mi/Desktop/web_workspace/skills/nl-sql/reference/search/
/Users/mi/Desktop/web_workspace/skills/nl-sql/reference/novel/
```

> 注：`search/` 和 `novel/` 当前仅有 `core-metrics-reference.md` 和 `event-metrics-reference.md`，缺 `metric-name-index.md`、`metric-dimension-index.md`、`core-metrics-tables.md`、`event-name-index.md`。这两条业务线选中后应直接告知用户索引缺失，让用户联系 gongyunhe 补齐。

---

## 指标 ID 速查清单（fallback）

> 仅在 Read 工具完全不可用时使用。**优先始终读 `metric-name-index.md` 取最新值**。
> 此清单只列每条业务线的指标 ID 范围与命名规则，用于校验"指标 ID 是否存在"的最低限度判断。

| 业务线 | 指标 ID 前缀 | 当前已知范围 | 索引文件 |
|--------|-------------|--------------|----------|
| 浏览器主端 | `BM` | BM001 ~ BM021 | `browser-main/metric-name-index.md` |
| 浏览器信息流 | `BF` | 见 `browser-feed/metric-name-index.md` | `browser-feed/metric-name-index.md` |
| 内容中心 | `CC` | CC001 ~ CC019 | `content-center/metric-name-index.md` |
| 搜索 | `SR`（待补） | 索引文件缺失 | — |
| 小说 | `NV`（待补） | 索引文件缺失 | — |

### 内容中心 (Content Center) 关键指标速查

| 用户输入 | Metric ID | 标准指标名 |
|---------|-----------|-----------|
| 内容中心 DAU / 日活 | CC001 | 内容中心DAU/日活 |
| 深度 DAU | CC003 | 内容中心深度DAU/日活 |
| 有效 DAU | CC004 | 内容中心有效DAU/日活 |
| MAU | CC005 | 内容中心MAU |
| 时长 | CC006 | 内容中心时长 |
| 人均时长 | CC007 | 内容中心人均时长 |
| 消费 DAU | CC008 | 内容中心消费DAU |
| 消费 UV | CC009 | 内容中心消费UV |
| VV | CC010 | 内容中心VV |
| 人均 VV | CC011 | 内容中心人均VV |
| 消费时长 | CC012 | 内容中心消费时长 |
| 分体裁 VV | CC015 | 内容中心分体裁VV |
| 分频道消费 UV | CC017 | 内容中心分频道消费UV |

> ⚠️ 用户只说"DAU"未指明业务线时，应先回到 Step 1 让用户选业务线；不要默认映射到 BM001 或 CC001。

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
| 浏览器主端 | `reference/browser-feed/` |
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

### Step 3A — 核心指标流程

#### 3A-1. 收集指标与时间信息

> 请提供以下信息：
> - **指标名称**：（例如：DAU、消费UV、VV、时长、留存…）
> - **时间周期**：（例如：最近7天、20260301~20260325、昨天…）
> - **其他维度**：（可选，例如：按机型、按版本、按省份…）

#### 3A-2. 加载索引文件

根据用户选择的业务线，读取以下索引文件：

| 业务线 | 指标名称索引 | 指标维度索引 |
|--------|-------------|-------------|
| 浏览器主端 | `reference/browser-main/metric-name-index.md` | `reference/browser-main/metric-dimension-index.md` |
| 浏览器信息流 | `reference/browser-feed/metric-name-index.md` | `reference/browser-feed/metric-dimension-index.md` |
| 内容中心 | `reference/content-center/metric-name-index.md` | `reference/content-center/metric-dimension-index.md` |
| 搜索 | `reference/search/metric-name-index.md` | `reference/search/metric-dimension-index.md` |
| 小说 | `reference/novel/metric-name-index.md` | `reference/novel/metric-dimension-index.md` |

#### 3A-3. 映射指标与维度

将用户输入映射到标准指标名称和维度：

**示例映射**：
| 用户输入 | 映射指标 | 指标ID |
|----------|---------|--------|
| "主启DAU" | 浏览器主启DAU | BM001 |
| "消费UV" | 浏览器消费UV | BM003 |
| "一级页浏览量" | 浏览器一级页VV | BF001 |

> [!WARNING]
> **指标范围约束（强制执行）**
> 
> 在映射过程中，**必须严格检查**用户请求的指标是否存在于索引文件中：
> - ✅ **指标存在**：继续执行后续步骤
> - ❌ **指标不存在**：立即停止，执行以下操作：
>   1. 告知用户：**"当前指标范围不支持生成此指标的 SQL 代码。"**
>   2. 提供可选方案：列出当前业务线下支持的相似指标
>   3. 引导联系：**"如需添加此指标，请联系开发者 gongyunhe 补充表结构和字段定义。"**
>   4. **终止 Skill 执行**：不再继续后续任何步骤

**指标不存在时的标准回复格式**：

```
⚠️ 指标不支持

您请求的指标「{用户输入的指标名}」不在当前支持的指标范围内。

📌 当前业务线支持的相似指标：
- {指标1}
- {指标2}
- {指标3}

如需添加此指标，请联系开发者 **gongyunhe** 补充表结构和字段定义。

[Skill 执行已终止]
```

#### 3A-4. 用户确认

> 请确认以下信息是否正确：
> - **指标名称**：{映射后的指标名称}
> - **指标维度**：{映射后的维度}
> - **时间范围**：{解析后的时间范围}
>
> 是否正确？（输入"是"继续，或修改后重新确认）

#### 3A-5. 查找 SQL 模板

根据确认的指标名称，在以下文件中查找对应的 SQL 模板：

| 业务线 | SQL 模板文件 |
|--------|-------------|
| 浏览器主端 | `reference/browser-main/core-metrics-tables.md` |
| 浏览器信息流 | `reference/browser-feed/core-metrics-tables.md` |
| 内容中心 | `reference/content-center/core-metrics-tables.md` |
| 搜索 | `reference/search/core-metrics-tables.md` |
| 小说 | `reference/novel/core-metrics-tables.md` |

#### 3A-6. 生成并校验 SQL

基于 SQL 模板，替换时间参数，生成最终 SQL。

**自检清单**：

| # | 检查项 | 要求 |
|---|--------|------|
| ① | 日期格式 | 使用 `'YYYYMMDD'` 格式，禁止连字符 |
| ② | 字段合法性 | 所有字段必须在参考文件中出现 |
| ③ | 表名合法性 | 包含完整三段式前缀 `iceberg_zjyprc_hadoop.` |
| ④ | 别名规范 | 列别名使用纯英文 |
| ⑤ | 分区过滤 | WHERE 必须包含 `date` 过滤条件 |
| ⑥ | 指标口径 | 聚合逻辑与参考文件一致 |

#### 3A-7. 保存 SQL 文件

将生成的 SQL 保存到桌面新目录：

**目录命名规则**：`{YYYYMMDD}_{HHMMSS}_{指标名称}`

**保存路径**：`~/Desktop/{目录名}/{指标名称}.sql`

使用脚本保存：
```bash
python scripts/nl-sql.py --metric "<指标名称>" --sql "<SQL内容>" --output-dir "~/Desktop/{目录名}"
```

#### 3A-8. 输出提示

SQL 生成完成后，向用户展示以下信息：

```
✅ SQL 生成完成

**查询信息**：
| 项目 | 内容 |
|------|------|
| 业务线 | {业务线名称} |
| 数据类型 | 核心指标 |
| 指标名称 | {指标名称} |
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

> [!WARNING]
> **事件范围约束（强制执行）**
> 
> 在生成 SQL 之前，**必须严格检查**用户请求的事件是否存在于事件名索引文件中：
> - ✅ **事件存在**：继续生成 SQL
> - ❌ **事件不存在**：立即停止，执行以下操作：
>   1. 告知用户：**"当前事件范围不支持生成此事件的 SQL 代码。"**
>   2. 提供可选方案：列出当前业务线下支持的相似事件
>   3. 引导联系：**"如需添加此事件，请联系开发者 gongyunhe 补充事件定义。"**
>   4. **终止 Skill 执行**：不再继续后续任何步骤

**事件不存在时的标准回复格式**：

```
⚠️ 事件不支持

您请求的事件「{用户输入的事件名}」不在当前支持的事件范围内。

📌 当前业务线支持的相似事件：
- {事件1}
- {事件2}
- {事件3}

如需添加此事件，请联系开发者 **gongyunhe** 补充事件定义。

[Skill 执行已终止]
```

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

同 3A-7 流程，保存到桌面新目录。

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

### 指标名称索引
- 浏览器主端：`reference/browser-main/metric-name-index.md`
- 浏览器信息流：`reference/browser-feed/metric-name-index.md`
- 内容中心：`reference/content-center/metric-name-index.md`
- 搜索：`reference/search/metric-name-index.md`
- 小说：`reference/novel/metric-name-index.md`

### 指标维度索引
- 浏览器主端：`reference/browser-main/metric-dimension-index.md`
- 浏览器信息流：`reference/browser-feed/metric-dimension-index.md`
- 内容中心：`reference/content-center/metric-dimension-index.md`
- 搜索：`reference/search/metric-dimension-index.md`
- 小说：`reference/novel/metric-dimension-index.md`

### SQL 模板文件
- 浏览器主端：`reference/browser-main/core-metrics-tables.md`
- 浏览器信息流：`reference/browser-feed/core-metrics-tables.md`
- 内容中心：`reference/content-center/core-metrics-tables.md`
- 搜索：`reference/search/core-metrics-tables.md`
- 小说：`reference/novel/core-metrics-tables.md`

### 事件名索引
- 浏览器主端：`reference/browser-main/event-name-index.md`
- 浏览器信息流：`reference/browser-feed/event-name-index.md`
- 内容中心：`reference/content-center/event-name-index.md`
- 搜索：`reference/search/event-name-index.md`
- 小说：`reference/novel/event-name-index.md`

---

## 注意事项

1. **日期格式**：统一使用 `'YYYYMMDD'` 整型格式
2. **用户去重**：使用 `did` 或 `distinct_id` 字段
3. **分区过滤**：WHERE 必须包含 `date` 条件
4. **指标确认**：生成 SQL 前必须让用户确认映射结果
5. **文件保存**：SQL 文件保存到桌面，目录名包含时间戳和指标名
6. **⚠️ 指标/事件范围约束**：
   - **严格禁止**为索引文件中不存在的指标或事件生成 SQL
   - 遇到不支持的指标/事件时，必须立即终止 Skill 执行
   - 必须引导用户联系开发者 gongyunhe 添加支持

---

## 内嵌参考数据（Inline Reference Data）

> 本节为磁盘上 `reference/<business-line>/*.md` 的权威副本，用于无法访问子文件的执行环境。
> 当前已内嵌：**内容中心 (content-center) — 完整**。
> 其他业务线（browser-main / browser-feed / search / novel）TODO：当出现"只能读 SKILL.md"环境且需查询这些业务线时再补充。

---

### 【content-center】metric-name-index

```markdown
# Content Center - Metric Name Index

| Metric ID | Metric Name (CN) | Metric Name (EN) | Category |
|-----------|------------------|------------------|----------|
| CC001 | 内容中心DAU/日活 | content_center_dau | User Scale |
| CC002 | 内容中心分新老用户DAU/日活 | content_center_dau_by_new_user | User Scale |
| CC003 | 内容中心深度DAU/日活 | content_center_deep_dau | User Scale |
| CC004 | 内容中心有效DAU/日活 | content_center_valid_dau | User Scale |
| CC005 | 内容中心MAU | content_center_mau | User Scale |
| CC006 | 内容中心时长 | content_center_duration | Engagement |
| CC007 | 内容中心人均时长 | content_center_avg_duration | Engagement |
| CC008 | 内容中心消费DAU | content_center_consumption_dau | Consumption |
| CC009 | 内容中心消费UV | content_center_consumption_uv | Consumption |
| CC010 | 内容中心VV | content_center_vv | Consumption |
| CC011 | 内容中心人均VV | content_center_avg_vv | Consumption |
| CC012 | 内容中心消费时长 | content_center_consumption_duration | Consumption |
| CC013 | 内容中心人均消费时长 | content_center_avg_consumption_duration | Consumption |
| CC014 | 内容中心分体裁消费UV | content_center_consumption_uv_by_type | Consumption |
| CC015 | 内容中心分体裁VV | content_center_vv_by_type | Consumption |
| CC016 | 内容中心分体裁消费时长 | content_center_consumption_duration_by_type | Consumption |
| CC017 | 内容中心分频道消费UV | content_center_consumption_uv_by_channel | Consumption |
| CC018 | 内容中心分频道VV | content_center_vv_by_channel | Consumption |
| CC019 | 内容中心分频道消费时长 | content_center_consumption_duration_by_channel | Consumption |

## 用户俗称 → 标准指标 映射示例

| User Input | Mapped Metric | Metric ID |
|------------|---------------|-----------|
| "内容中心DAU" / "DAU"（已选内容中心） | 内容中心DAU/日活 | CC001 |
| "消费UV" | 内容中心消费UV | CC009 |
| "人均时长" | 内容中心人均时长 | CC007 |
| "分体裁VV" | 内容中心分体裁VV | CC015 |
| "VV" | 内容中心VV | CC010 |
| "MAU" | 内容中心MAU | CC005 |
```

---

### 【content-center】metric-dimension-index

```markdown
# Content Center - Metric Dimension Index

## 指标 → 默认维度

| Metric ID | Metric Name | Dimensions |
|-----------|-------------|------------|
| CC001 | 内容中心DAU/日活 | (no group, aggregate) |
| CC002 | 内容中心分新老用户DAU/日活 | date, is_new_2024 |
| CC003 | 内容中心深度DAU/日活 | date |
| CC004 | 内容中心有效DAU/日活 | (no group, aggregate) |
| CC005 | 内容中心MAU | (no group, aggregate) |
| CC006 | 内容中心时长 | (no group, aggregate) |
| CC007 | 内容中心人均时长 | (no group, aggregate) |
| CC008 | 内容中心消费DAU | (no group, aggregate) |
| CC009 | 内容中心消费UV | (no group, aggregate) |
| CC010 | 内容中心VV | (no group, aggregate) |
| CC011 | 内容中心人均VV | (no group, aggregate) |
| CC012 | 内容中心消费时长 | (no group, aggregate) |
| CC013 | 内容中心人均消费时长 | (no group, aggregate) |
| CC014 | 内容中心分体裁消费UV | item_type |
| CC015 | 内容中心分体裁VV | item_type |
| CC016 | 内容中心分体裁消费时长 | item_type |
| CC017 | 内容中心分频道消费UV | feed_channel |
| CC018 | 内容中心分频道VV | feed_channel |
| CC019 | 内容中心分频道消费时长 | feed_channel |

## 维度字段定义

| Dimension | Field | Description |
|-----------|-------|-------------|
| Date | date | 分区字段，格式 YYYYMMDD |
| Device ID | did | 设备唯一 ID（用于去重） |
| User ID | distinct_id | 埋点系统的用户 ID |
| New User | is_new_2024 | 1=新用户, 0=老用户 |
| Content Type | item_type | 内容类型：news / video / minivideo |
| Channel | feed_channel | 频道 |
| Duration | app_dura | 使用时长（毫秒） |
| Consumption Count | consum_cnt | 消费次数 |
| Consumption Duration | consum_dura | 消费时长（毫秒） |

## 用户表达 → 维度映射

| User Query | Mapped Dimension | SQL Field |
|------------|------------------|-----------|
| "按日期" | Date | date |
| "按体裁" | Content Type | item_type |
| "按频道" | Channel | feed_channel |
| "按新老用户" | New User | is_new_2024 |
```

---

### 【content-center】core-metrics-tables（SQL 模板）

**主表**：`iceberg_zjyprc_hadoop.newhome.dwm_newhome_event_aggregation_label_di`（按 `date` 分区，主键 `(date, did)`）
**事件表**（仅 CC004 用）：`iceberg_zjyprc_hadoop.dw.dwd_ot_event_di_31000000297`

#### CC001: 内容中心DAU/日活
```sql
SELECT
    COUNT(DISTINCT did) AS uv
FROM
    iceberg_zjyprc_hadoop.newhome.dwm_newhome_event_aggregation_label_di
WHERE
    date >= '${start_date}'
    AND date <= '${end_date}'
    AND is_dau_2024 = 1
;
```

#### CC002: 内容中心分新老用户DAU/日活
```sql
SELECT
    date,
    CASE WHEN is_new_2024 = 1 THEN 'new'
         WHEN is_new_2024 = 0 THEN 'old'
    END AS is_new_user,
    COUNT(DISTINCT did) AS uv
FROM
    iceberg_zjyprc_hadoop.newhome.dwm_newhome_event_aggregation_label_di
WHERE
    date >= '${start_date}'
    AND date <= '${end_date}'
    AND is_dau_2024 = 1
GROUP BY
    date,
    CASE WHEN is_new_2024 = 1 THEN 'new'
         WHEN is_new_2024 = 0 THEN 'old'
    END
ORDER BY date;
```

#### CC003: 内容中心深度DAU/日活（时长 ≥ 20 分钟）
```sql
SELECT
    date,
    COUNT(DISTINCT did) AS uv
FROM (
    SELECT
        date,
        did,
        SUM(app_dura) / 60000 AS app_dura_min
    FROM
        iceberg_zjyprc_hadoop.newhome.dwm_newhome_event_aggregation_label_di
    WHERE
        date >= '${start_date}'
        AND date <= '${end_date}'
        AND is_dau_2024 = 1
    GROUP BY date, did
) a
WHERE app_dura_min >= 20
GROUP BY date
ORDER BY date;
```

#### CC004: 内容中心有效DAU/日活（事件表）
```sql
SELECT
    COUNT(DISTINCT distinct_id) AS uv
FROM
    iceberg_zjyprc_hadoop.dw.dwd_ot_event_di_31000000297
WHERE
    date >= '${start_date}'
    AND date <= '${end_date}'
    AND event_name IN (
        'content_item_click',
        'search_click',
        'mivideo_content_item_click',
        'content_item_view',
        'content_item_video_play'
    )
;
```

#### CC005: 内容中心MAU
```sql
SELECT
    COUNT(DISTINCT did) AS mau
FROM
    iceberg_zjyprc_hadoop.newhome.dwm_newhome_event_aggregation_label_di
WHERE
    date >= '${start_date}'
    AND date <= '${end_date}'
    AND is_dau_2024 = 1
;
```

#### CC006: 内容中心时长（分钟）
```sql
SELECT
    SUM(app_dura) / 60000 AS duration_min
FROM
    iceberg_zjyprc_hadoop.newhome.dwm_newhome_event_aggregation_label_di
WHERE
    date >= '${start_date}'
    AND date <= '${end_date}'
    AND is_dau_2024 = 1
    AND app_dura > 0
;
```

#### CC007: 内容中心人均时长（分钟）
```sql
SELECT
    SUM(app_dura) / 60000 / COUNT(DISTINCT did) AS avg_duration_min
FROM
    iceberg_zjyprc_hadoop.newhome.dwm_newhome_event_aggregation_label_di
WHERE
    date >= '${start_date}'
    AND date <= '${end_date}'
    AND is_dau_2024 = 1
    AND app_dura > 0
;
```

#### CC008: 内容中心消费DAU
```sql
SELECT
    COUNT(DISTINCT did) AS uv
FROM
    iceberg_zjyprc_hadoop.newhome.dwm_newhome_event_aggregation_label_di
WHERE
    date >= '${start_date}'
    AND date <= '${end_date}'
    AND is_dau_2024 = 1
    AND consum_cnt > 0
;
```

#### CC009: 内容中心消费UV
```sql
SELECT
    COUNT(DISTINCT did) AS uv
FROM
    iceberg_zjyprc_hadoop.newhome.dwm_newhome_event_aggregation_label_di
WHERE
    date >= '${start_date}'
    AND date <= '${end_date}'
    AND is_dau_2024 = 1
    AND consum_cnt > 0
;
```

#### CC010: 内容中心VV
```sql
SELECT
    SUM(consum_cnt) AS vv
FROM
    iceberg_zjyprc_hadoop.newhome.dwm_newhome_event_aggregation_label_di
WHERE
    date >= '${start_date}'
    AND date <= '${end_date}'
    AND is_dau_2024 = 1
    AND consum_cnt > 0
;
```

#### CC011: 内容中心人均VV
```sql
SELECT
    SUM(consum_cnt) / COUNT(DISTINCT did) AS avg_vv
FROM
    iceberg_zjyprc_hadoop.newhome.dwm_newhome_event_aggregation_label_di
WHERE
    date >= '${start_date}'
    AND date <= '${end_date}'
    AND is_dau_2024 = 1
    AND consum_cnt > 0
;
```

#### CC012: 内容中心消费时长（分钟）
```sql
SELECT
    SUM(consum_dura) / 60000 AS duration_min
FROM
    iceberg_zjyprc_hadoop.newhome.dwm_newhome_event_aggregation_label_di
WHERE
    date >= '${start_date}'
    AND date <= '${end_date}'
    AND is_dau_2024 = 1
    AND consum_dura > 0
;
```

#### CC013: 内容中心人均消费时长（分钟）
```sql
SELECT
    SUM(consum_dura) / 60000 / COUNT(DISTINCT did) AS avg_duration_min
FROM
    iceberg_zjyprc_hadoop.newhome.dwm_newhome_event_aggregation_label_di
WHERE
    date >= '${start_date}'
    AND date <= '${end_date}'
    AND is_dau_2024 = 1
    AND consum_dura > 0
    AND consum_cnt > 0
;
```

#### CC014: 内容中心分体裁消费UV
```sql
SELECT
    item_type,
    COUNT(DISTINCT did) AS uv
FROM
    iceberg_zjyprc_hadoop.newhome.dwm_newhome_event_aggregation_label_di
WHERE
    date >= '${start_date}'
    AND date <= '${end_date}'
    AND is_dau_2024 = 1
    AND consum_cnt > 0
GROUP BY item_type
ORDER BY uv DESC;
```

#### CC015: 内容中心分体裁VV
```sql
SELECT
    item_type,
    SUM(consum_cnt) AS vv
FROM
    iceberg_zjyprc_hadoop.newhome.dwm_newhome_event_aggregation_label_di
WHERE
    date >= '${start_date}'
    AND date <= '${end_date}'
    AND is_dau_2024 = 1
    AND consum_cnt > 0
GROUP BY item_type
ORDER BY vv DESC;
```

#### CC016: 内容中心分体裁消费时长
```sql
SELECT
    item_type,
    SUM(consum_dura) / 60000 AS duration_min
FROM
    iceberg_zjyprc_hadoop.newhome.dwm_newhome_event_aggregation_label_di
WHERE
    date >= '${start_date}'
    AND date <= '${end_date}'
    AND is_dau_2024 = 1
    AND consum_dura > 0
GROUP BY item_type
ORDER BY duration_min DESC;
```

#### CC017: 内容中心分频道消费UV
```sql
SELECT
    feed_channel,
    COUNT(DISTINCT did) AS uv
FROM
    iceberg_zjyprc_hadoop.newhome.dwm_newhome_event_aggregation_label_di
WHERE
    date >= '${start_date}'
    AND date <= '${end_date}'
    AND is_dau_2024 = 1
    AND consum_cnt > 0
GROUP BY feed_channel
ORDER BY uv DESC;
```

#### CC018: 内容中心分频道VV
```sql
SELECT
    feed_channel,
    SUM(consum_cnt) AS vv
FROM
    iceberg_zjyprc_hadoop.newhome.dwm_newhome_event_aggregation_label_di
WHERE
    date >= '${start_date}'
    AND date <= '${end_date}'
    AND is_dau_2024 = 1
    AND consum_cnt > 0
GROUP BY feed_channel
ORDER BY vv DESC;
```

#### CC019: 内容中心分频道消费时长
```sql
SELECT
    feed_channel,
    SUM(consum_dura) / 60000 AS duration_min
FROM
    iceberg_zjyprc_hadoop.newhome.dwm_newhome_event_aggregation_label_di
WHERE
    date >= '${start_date}'
    AND date <= '${end_date}'
    AND is_dau_2024 = 1
    AND consum_dura > 0
GROUP BY feed_channel
ORDER BY duration_min DESC;
```

---

### 内嵌数据使用要点

1. 用户俗称 → Metric ID：先在「metric-name-index」表里**严格匹配**；找不到则按 Step 3A-3 的「指标不支持」格式终止。
2. 维度选择：以「metric-dimension-index」表中的默认维度为准，用户额外指定的维度用「维度字段定义」表查 SQL field。
3. 取 SQL 模板：直接复制对应 CCxxx 段落里的 SQL，把 `${start_date}` / `${end_date}` 替换成 `'YYYYMMDD'` 字面量。
4. 校验：对照本文件 Step 3A-6 的自检清单（日期格式、字段合法性、表名三段式、`date` 分区过滤等）。
5. **写文件保存** SQL 时，可使用当前环境提供的 `write_file` 工具，目标路径按 Step 3A-7 规则：`~/Desktop/{YYYYMMDD}_{HHMMSS}_{指标名称}/{指标名称}.sql`。
