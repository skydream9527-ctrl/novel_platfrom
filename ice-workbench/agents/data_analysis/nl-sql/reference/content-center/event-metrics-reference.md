# 内容中心埋点指标参考代码

## 概述
本文档包含内容中心相关的埋点指标SQL查询代码，用于数据分析和业务监控。

## 指标说明

### 1. 内容中心有效DAU
**指标定义**: 内容中心的有效日活跃用户数
**数据源**: `iceberg_zjyprc_hadoop.dw.dwd_ot_event_di_31000000297`
**事件类型**: 
- `content_item_click` - 内容点击
- `search_click` - 搜索点击
- `mivideo_content_item_click` - 视频内容点击
- `content_item_view` - 内容浏览
- `content_item_video_play` - 视频播放

```sql
--内容中心有效DAU
SELECT
    date,
    distinct_id did
FROM
    iceberg_zjyprc_hadoop.dw.dwd_ot_event_di_31000000297
WHERE
    date=${date-1}
    and event_name in (
        'content_item_click',
        'search_click',
        'mivideo_content_item_click',
        'content_item_view',
        'content_item_video_play'
    )
GROUP BY
    1,
    2
;
```

### 2. 激励DAU
**指标定义**: 激励中心页面的日活跃用户数
**数据源**: `iceberg_zjyprc_hadoop.dw.dwd_ot_event_di_31000000297`
**事件类型**: `page_expose`
**页面标识**: `reward_center`

```sql
--激励DAU
SELECT
    date,
    count(distinct distinct_id) uv
FROM
    iceberg_zjyprc_hadoop.dw.dwd_ot_event_di_31000000297
WHERE
    date=${date-1}
    and event_name='page_expose'
    and properties ['page']='reward_center'
GROUP BY
    1;
```

### 3. 激励页面时长
**指标定义**: 激励中心页面的总停留时长（分钟）
**数据源**: `iceberg_zjyprc_hadoop.dw.dwd_ot_event_di_31000000297`
**事件类型**: `page_view`
**页面标识**: `reward_center`
**时长单位**: 毫秒转换为分钟（除以60000）

```sql
--激励页面时长
SELECT
    sum(properties ['duration'])/60000
FROM
    iceberg_zjyprc_hadoop.dw.dwd_ot_event_di_31000000297
WHERE
    date=${date-1}
    and event_name='page_view'
    and properties ['page']='reward_center'
;
```

## 使用说明
1. 所有查询中的 `${date-1}` 表示前一天的日期
2. 时长相关指标需要除以60000转换为分钟
3. 用户去重使用 `distinct_id` 字段
4. 事件属性通过 `properties['key']` 方式访问

## 注意事项
- 查询结果需要按日期分组
- 注意数据过滤条件，确保数据准确性
- 时长计算需要考虑边界值（如0和86400000毫秒）