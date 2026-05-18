# 小说埋点指标参考代码

## 概述
本文档包含小说相关的埋点指标SQL查询代码，用于小说业务的数据分析和用户行为监控。

## 指标说明

### 1. SDK有效阅读UV
**指标定义**: 通过SDK进行有效阅读的用户数
**数据源**: `iceberg_zjyprc_hadoop.dw.dwd_ot_event_di_31000000442`
**事件类型**: `book_read_quit_sdk`
**有效阅读条件**: 阅读时长在30秒到24小时之间
**排除类型**: 本地书籍

```sql
--SDK有效阅读UV
SELECT  date,
        count(distinct distinct_id)/10000 as sdk_valid_uv
FROM    iceberg_zjyprc_hadoop.dw.dwd_ot_event_di_31000000442
WHERE   date=${date-1}
        and pkg='com.android.browser'
        and event_name='book_read_quit_sdk'
        and properties ['read_time'] BETWEEN 30000 and 86400000
        and properties ['book_type']<>'local'
GROUP BY date
;
```

### 2. 浏览器小说uv、vv、时长
**指标定义**: 浏览器中小说的用户数、浏览量和阅读时长
**数据源**: `iceberg_zjyprc_hadoop.dw.dwd_ot_event_di_31000000442`
**事件类型**: `book_read_quit_sdk`
**小说类型**: 商店、预添加、盗版、短篇故事
**计算指标**:
- UV: 独立用户数
- VV: 翻页次数
- 时长: 阅读时长（分钟）

```sql
--浏览器小说uv、vv、时长
SELECT
    date,
    count(distinct distinct_id) uv, --uv
    sum(properties ['turn_pages']) as novel_vv, --vv
    sum(properties ['read_time'])/60000 read_time --时长
FROM
    iceberg_zjyprc_hadoop.dw.dwd_ot_event_di_31000000442
WHERE
    date=${date-1}
    and event_name='book_read_quit_sdk'
    and properties ['read_time'] BETWEEN 0 AND 86400000
    and properties ['book_type'] in ('store', 'pre_add_book', 'pirate', 'shortstory')
GROUP BY
    1;
```

### 3. 短故事vv单独计算
**指标定义**: 短故事的浏览量统计
**数据源**: `iceberg_zjyprc_hadoop.dw.dwd_ot_event_di_31000000442`
**事件类型**: `content_item_click_enter`
**内容类型**: `shortstory`

```sql
--短故事vv单独计算
SELECT
    count(distinct_id)
FROM
    iceberg_zjyprc_hadoop.dw.dwd_ot_event_di_31000000442
WHERE
    date=${date-1}
    and event_name='content_item_click_enter'
    and properties ['item_type']='shortstory'
;
```

### 4. 浏览器长篇uv、vv、时长
**指标定义**: 浏览器中长篇小说的用户数、浏览量和阅读时长
**数据源**: `iceberg_zjyprc_hadoop.dw.dwd_ot_event_di_31000000442`
**事件类型**: `book_read_quit_sdk`
**小说类型**: 商店、预添加、盗版（排除短篇故事）

```sql
--浏览器长篇uv、vv、时长
SELECT
    date,
    count(distinct distinct_id) uv,
    sum(properties ['turn_pages']) as vv,
    sum(properties ['read_time'])/60000 read_time
FROM
    iceberg_zjyprc_hadoop.dw.dwd_ot_event_di_31000000442
WHERE
    date=${date-1}
    and event_name='book_read_quit_sdk'
    and properties ['read_time'] BETWEEN 0 AND 86400000
    and properties ['book_type'] in ('store', 'pre_add_book', 'pirate')
GROUP BY
    1
;
```

### 5. 浏览器短故事uv/时长
**指标定义**: 浏览器中短故事的用户数和阅读时长
**数据源**: `iceberg_zjyprc_hadoop.dw.dwd_ot_event_di_31000000442`
**事件类型**: `book_read_quit_sdk`
**小说类型**: 短篇故事

```sql
--浏览器短故事uv/时长
SELECT
    date,
    count(distinct distinct_id) uv,
    sum(properties ['read_time'])/60000 read_time
FROM
    iceberg_zjyprc_hadoop.dw.dwd_ot_event_di_31000000442
WHERE
    date=${date-1}
    and event_name='book_read_quit_sdk'
    and properties ['read_time'] BETWEEN 0 AND 86400000
    and properties ['book_type']='shortstory'
GROUP BY
    1;
```

### 6. 短故事vv
**指标定义**: 短故事的浏览量统计（重复查询）
**数据源**: `iceberg_zjyprc_hadoop.dw.dwd_ot_event_di_31000000442`
**事件类型**: `content_item_click_enter`
**内容类型**: `shortstory`

```sql
--短故事vv
SELECT
    count(distinct_id)
FROM
    iceberg_zjyprc_hadoop.dw.dwd_ot_event_di_31000000442
WHERE
    date=${date-1}
    and event_name='content_item_click_enter'
    and properties ['item_type']='shortstory'
;
```

### 7. 内容中心小说uv、vv、时长
**指标定义**: 内容中心中小说的用户数、浏览量和阅读时长
**数据源**: `iceberg_zjyprc_hadoop.dw.dwd_ot_event_di_31000000297`
**事件类型**: `book_read_quit_sdk`
**时长范围**: 0到24小时

```sql
--内容中心小说uv、vv、时长
SELECT
    date,
    count(distinct distinct_id) uv,
    sum(properties ['turn_pages']) as vv,
    sum(properties ['read_time'])/60000 read_time
FROM
    iceberg_zjyprc_hadoop.dw.dwd_ot_event_di_31000000297
WHERE
    date=${date-1}
    and event_name='book_read_quit_sdk'
    and properties ['read_time'] BETWEEN 0 AND 86400000
 GROUP BY
    1
;
```

## 使用说明
1. 所有查询中的 `${date-1}` 表示前一天的日期
2. 时长相关指标需要除以60000转换为分钟
3. 用户去重使用 `distinct_id` 字段
4. 小说类型通过 `properties['book_type']` 区分
5. 阅读时长通过 `properties['read_time']` 获取

## 注意事项
- 查询结果需要按日期分组
- 注意数据过滤条件，确保数据准确性
- 时长计算需要考虑边界值（0和86400000毫秒）
- 小说类型需要根据业务需求进行筛选
- 短故事和长篇小说需要分别统计