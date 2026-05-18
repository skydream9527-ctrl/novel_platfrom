# 搜索埋点指标参考代码

## 概述
本文档包含搜索相关的埋点指标SQL查询代码，用于搜索业务的数据分析和用户行为监控。

## 指标说明

### 1. 搜索SUG页uv
**指标定义**: 搜索建议页面的用户访问数
**数据源**: `iceberg_zjyprc_hadoop.dw.dwd_ot_event_di_31000000442`
**事件类型**: `search_sugpage_expose`
**指标用途**: 统计用户在搜索建议页面的曝光情况

```sql
--搜索SUG页uv
SELECT
    date,
    distinct_id did
FROM
    iceberg_zjyprc_hadoop.dw.dwd_ot_event_di_31000000442
WHERE
    date=${date-1}
    and event_name='search_sugpage_expose'
GROUP BY
    1,
    2
;
```

## 使用说明
1. 查询中的 `${date-1}` 表示前一天的日期
2. 用户去重使用 `distinct_id` 字段
3. 事件类型为 `search_sugpage_expose` 表示搜索建议页面曝光

## 注意事项
- 查询结果需要按日期分组
- 注意数据过滤条件，确保数据准确性
- 该指标主要用于统计搜索建议功能的用户触达情况
- 搜索建议页面是用户搜索行为的重要前置环节