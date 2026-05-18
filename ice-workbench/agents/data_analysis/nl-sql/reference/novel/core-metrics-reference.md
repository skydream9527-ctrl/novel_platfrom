# 小说核心指标参考代码

## 概述
本文档包含小说业务的核心指标SQL查询代码，用于多看平台的小说业务分析和运营监控。

## 指标说明

### 1. 多看DAU
**指标定义**: 多看平台的日活跃用户数
**数据源**: `iceberg_zjyprc_hadoop.dw.dwd_ot_event_di_1004465`
**事件类型**: `app_open`
**包名**: `com.duokan.reader`

```sql
--多看DAU
SELECT  date,
        count(distinct distinct_id) as duokan_dau
FROM    iceberg_zjyprc_hadoop.dw.dwd_ot_event_di_1004465
WHERE   date=${date-1}
        and pkg='com.duokan.reader'
        and event_name='app_open'
GROUP BY date
;
```

### 2. 多看阅读时长
**指标定义**: 多看平台的总阅读时长（分钟）
**数据源**: `iceberg_zjyprc_hadoop.dw.dwd_ot_event_di_1004465`
**事件类型**: `book_read_quit`
**时长范围**: 0到24小时
**排除类型**: 本地书籍

```sql
--多看阅读时长
SELECT  date,
        SUM(properties ['read_time'])/60000 as duokan_read_time
FROM    iceberg_zjyprc_hadoop.dw.dwd_ot_event_di_1004465
WHERE   date=${date-1}
        and pkg='com.duokan.reader'
        and event_name='book_read_quit'
        and properties ['read_time'] BETWEEN 0 and 86400000
        and properties ['book_type']<>'local'
        and properties ['book_type']<>'local_book'
GROUP BY date
;
```

### 3. 多看有效阅读UV
**指标定义**: 多看平台的有效阅读用户数
**数据源**: `iceberg_zjyprc_hadoop.dw.dwd_ot_event_di_1004465`
**事件类型**: `book_read_quit`
**有效阅读条件**: 阅读时长在30秒到24小时之间
**排除类型**: 本地书籍

```sql
--多看有效阅读UV
SELECT  date,
        count(distinct distinct_id) as duokan_valid_uv
FROM    iceberg_zjyprc_hadoop.dw.dwd_ot_event_di_1004465
WHERE   date=${date-1}
        and pkg='com.duokan.reader'
        and event_name='book_read_quit'
        and properties ['read_time'] BETWEEN 30000 and 86400000
        and properties ['book_type']<>'local'
        and properties ['book_type']<>'local_book'
GROUP BY date
;
```

### 4. 多看网文阅读时长
**指标定义**: 多看平台网文的阅读时长（分钟）
**数据源**: `iceberg_zjyprc_hadoop.dw.dwd_ot_event_di_1004465` + `iceberg_zjyprc_hadoop.duokan.dim_read_book_information`
**事件类型**: `book_read_quit`
**书籍类型**: 网文（book_type_status=1）
**计算逻辑**: 先按书籍聚合，再关联书籍信息表

```sql
--多看网文阅读时长
SELECT  date,
        SUM(read_time)/60000 as duokan_wangwen_read_time
FROM
    (
        SELECT  date,
                properties ['book_id'] book_id,
                SUM(properties ['read_time']) as read_time
        FROM    iceberg_zjyprc_hadoop.dw.dwd_ot_event_di_1004465
        WHERE   date=${date-1}
                and pkg='com.duokan.reader'
                and event_name='book_read_quit'
                and properties ['read_time'] BETWEEN 0 and 86400000
                and properties ['book_type']<>'local'
                and properties ['book_type']<>'local_book'
        GROUP BY date, properties ['book_id']
    ) t1
    join
    (
        SELECT  book_id
        FROM    iceberg_zjyprc_hadoop.duokan.dim_read_book_information
        WHERE   book_type_status=1
        GROUP BY book_id
    ) t2 on t1.book_id=t2.book_id
GROUP BY date
;
```

### 5. 多看网文有效阅读UV
**指标定义**: 多看平台网文的有效阅读用户数
**数据源**: `iceberg_zjyprc_hadoop.dw.dwd_ot_event_di_1004465` + `iceberg_zjyprc_hadoop.duokan.dim_read_book_information`
**事件类型**: `book_read_quit`
**书籍类型**: 网文（book_type_status=1）
**有效阅读条件**: 阅读时长在30秒到24小时之间

```sql
--多看网文有效阅读UV
SELECT  date,
        SUM(uv) as duokan_wangwen_valid_uv
FROM
    (
        SELECT  date,
                properties ['book_id'] book_id,
                count(distinct distinct_id) as uv
        FROM    iceberg_zjyprc_hadoop.dw.dwd_ot_event_di_1004465
        WHERE   date=${date-1}
                and pkg='com.duokan.reader'
                and event_name='book_read_quit'
                and properties ['read_time'] BETWEEN 30000 and 86400000
                and properties ['book_type']<>'local'
                and properties ['book_type']<>'local_book'
        GROUP BY date, properties ['book_id']
    ) t1
    join (
        SELECT  book_id
        FROM    iceberg_zjyprc_hadoop.duokan.dim_read_book_information
        WHERE   book_type_status=1
        GROUP BY book_id
    ) t2 on t1.book_id=t2.book_id
GROUP BY date
;
```

### 6. 多看出版阅读时长
**指标定义**: 多看平台出版书籍的阅读时长（分钟）
**数据源**: `iceberg_zjyprc_hadoop.dw.dwd_ot_event_di_1004465` + `iceberg_zjyprc_hadoop.duokan.dim_read_book_information`
**事件类型**: `book_read_quit`
**书籍类型**: 出版书籍（book_type_status=2）
**计算逻辑**: 先按书籍聚合，再关联书籍信息表

```sql
--多看出版阅读时长
SELECT  date,
        SUM(read_time)/60000 as duokan_copyright_read_time
FROM
    (
        SELECT  date,
                properties ['book_id'] book_id,
                SUM(properties ['read_time']) as read_time
        FROM    iceberg_zjyprc_hadoop.dw.dwd_ot_event_di_1004465
        WHERE   date=${date-1}
                and pkg='com.duokan.reader'
                and event_name='book_read_quit'
                and properties ['read_time'] BETWEEN 0 and 86400000
                and properties ['book_type']<>'local'
                and properties ['book_type']<>'local_book'
        GROUP BY date, properties ['book_id']
    ) t1
    join (
        SELECT  book_id
        FROM    iceberg_zjyprc_hadoop.duokan.dim_read_book_information
        WHERE   book_type_status=2
        GROUP BY book_id
    ) t2 on t1.book_id=t2.book_id
GROUP BY date
;
```

### 7. 多看出版有效阅读UV
**指标定义**: 多看平台出版书籍的有效阅读用户数
**数据源**: `iceberg_zjyprc_hadoop.dw.dwd_ot_event_di_1004465` + `iceberg_zjyprc_hadoop.duokan.dim_read_book_information`
**事件类型**: `book_read_quit`
**书籍类型**: 出版书籍（book_type_status=2）
**有效阅读条件**: 阅读时长在30秒到24小时之间

```sql
--多看出版有效阅读UV
SELECT  date,
        SUM(uv) as duokan_copyright_valid_uv
FROM
    (
        SELECT  date,
                properties ['book_id'] book_id,
                count(distinct distinct_id) as uv
        FROM    iceberg_zjyprc_hadoop.dw.dwd_ot_event_di_1004465
        WHERE   date=${date-1}
                and pkg='com.duokan.reader'
                and event_name='book_read_quit'
                and properties ['read_time'] BETWEEN 30000 and 86400000
                and properties ['book_type']<>'local'
                and properties ['book_type']<>'local_book'
        GROUP BY date, properties ['book_id']
    ) t1
    join (
        SELECT  book_id
        FROM    iceberg_zjyprc_hadoop.duokan.dim_read_book_information
        WHERE   book_type_status=2
        GROUP BY book_id
    ) t2 on t1.book_id=t2.book_id
GROUP BY date
;
```

## 使用说明
1. 所有查询中的 `${date-1}` 表示前一天的日期
2. 时长相关指标需要除以60000转换为分钟
3. 用户去重使用 `distinct_id` 字段
4. 书籍类型通过 `book_type_status` 区分（1=网文，2=出版）
5. 阅读时长通过 `properties['read_time']` 获取

## 注意事项
- 查询结果需要按日期分组
- 注意数据过滤条件，确保数据准确性
- 时长计算需要考虑边界值（0和86400000毫秒）
- 网文和出版书籍需要分别统计
- 书籍信息需要关联维度表获取
- 有效阅读需要设置时长下限（30000毫秒）