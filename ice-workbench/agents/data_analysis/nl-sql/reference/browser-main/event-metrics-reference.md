# 浏览器埋点指标参考代码

## 概述
本文档包含浏览器相关的埋点指标SQL查询代码，用于浏览器业务的数据分析和用户行为监控。

## 指标说明

### 1. 浏览器搜索SUG页uv
**指标定义**: 浏览器搜索建议页面的用户访问数
**数据源**: `iceberg_zjyprc_hadoop.dw.dwd_ot_event_di_31000000442`
**事件类型**: `search_sugpage_expose`
**指标用途**: 统计用户在浏览器搜索建议页面的曝光情况

```sql
--浏览器搜索SUG页uv
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

### 2. 浏览器开屏uv
**指标定义**: 浏览器开屏广告的用户曝光数
**数据源**: `iceberg_zjyprc_hadoop.dw.dwd_ot_event_di_31000000442`
**事件类型**: `ad_app_intercept_server_request`
**指标用途**: 统计开屏广告的用户触达情况

```sql
--浏览器开屏uv
SELECT
    date,
    distinct_id did
FROM
    iceberg_zjyprc_hadoop.dw.dwd_ot_event_di_31000000442
WHERE
    date=${date-1}
    and event_name='ad_app_intercept_server_request'
GROUP BY
    1,
    2
;
```

### 3. 浏览器长会话uv
**指标定义**: 浏览器长会话的用户数（包含短视频和小说）
**数据源**: `iceberg_zjyprc_hadoop.browser.dwm_browser_event_aggregation_label_di` + `iceberg_zjyprc_hadoop.dw.dwd_ot_event_di_31000000442`
**计算逻辑**: 使用FULL JOIN合并短视频和小说的用户
**会话类型**: 长会话（有视频播放或小说阅读行为）

```sql
--浏览器长会话uv
SELECT
    a.date,
    a.did
FROM
    (
        SELECT
            date,
            did
        FROM
            iceberg_zjyprc_hadoop.browser.dwm_browser_event_aggregation_label_di
        WHERE
            date=${date-1}
            and is_app_dau_2024=1
            and page='lightapp_skit_detail'
            and video_play_cnt>0
        GROUP BY
            1,
            2
    ) a
    full join (
        SELECT
            date,
            distinct_id did
        FROM
            iceberg_zjyprc_hadoop.dw.dwd_ot_event_di_31000000442
        WHERE
            date=${date-1}
            and event_name='book_read_quit_sdk'
            and properties ['book_type'] in ('store', 'pre_add_book', 'pirate', 'shortstory')
        GROUP BY
            1,
            2
    ) b on a.did=b.did
    and a.date=b.date
GROUP BY
    1,
    2
;
```

### 4. 浏览器二级页vv
**指标定义**: 浏览器二级页面的浏览量（包含短视频和小说）
**数据源**: `iceberg_zjyprc_hadoop.browser.dwm_browser_event_aggregation_label_di` + `iceberg_zjyprc_hadoop.dw.dwd_ot_event_di_31000000442`
**计算逻辑**: 使用INNER JOIN合并短视频和小说的用户
**页面类型**: 二级页面（详情页、短视频、小说等）

```sql
--浏览器二级页vv
SELECT
    a.date,
    count(distinct a.did)
FROM
    (
        SELECT
            date,
            did
        FROM
            iceberg_zjyprc_hadoop.browser.dwm_browser_event_aggregation_label_di
        WHERE
            date=${date-1}
            and is_app_dau_2024=1
            and page in (
                'feed_content_detail',
                'feed_minivideo_continuously_root',
                'feed_minivideo_continuously',
                'feed_shortvideo_immerse_root',
                'feed_shortvideo_immerse',
                'lightapp_skit_detail'
            )
            and (
                view_cnt>0
                or video_play_cnt>0
            )
        GROUP BY
            1,
            2
    ) a
    join (
        SELECT
            date,
            distinct_id did
        FROM
            iceberg_zjyprc_hadoop.dw.dwd_ot_event_di_31000000442
        WHERE
            date=${date-1}
            and event_name='book_read_quit_sdk'
            and properties ['book_type'] in ('store', 'pre_add_book', 'pirate', 'shortstory')
        GROUP BY
            1,
            2
    ) b on a.did=b.did
    and a.date=b.date
GROUP BY
    1
;
```

## 使用说明
1. 所有查询中的 `${date-1}` 表示前一天的日期
2. 用户去重使用 `distinct_id` 或 `did` 字段
3. 浏览器相关指标主要使用聚合表 `dwm_browser_event_aggregation_label_di`
4. 小说相关指标使用事件表 `dwd_ot_event_di_31000000442`

## 注意事项
- 查询结果需要按日期分组
- 注意数据过滤条件，确保数据准确性
- 长会话和二级页指标需要合并多个数据源
- 使用FULL JOIN确保不遗漏任何用户
- 使用INNER JOIN确保用户同时有短视频和小说行为
- 页面类型需要根据业务需求进行筛选