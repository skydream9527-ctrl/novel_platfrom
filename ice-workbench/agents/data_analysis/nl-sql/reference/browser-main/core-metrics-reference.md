# 浏览器核心指标参考代码

## 概述
本文档包含浏览器业务的核心指标SQL查询代码，用于浏览器业务的分析和运营监控。

## 指标说明

### 1. 浏览器主启DAU
**指标定义**: 通过点击图标启动浏览器的日活跃用户数
**数据源**: `iceberg_zjyprc_hadoop.browser.dwm_browser_event_aggregation_label_di`
**启动方式**: 点击icon
**过滤条件**: `app_launch_way='点击icon'` 且 `app_open_cnt+app_duration_cnt>0`

```sql
--浏览器主启DAU
SELECT
    date,
    did
FROM
    iceberg_zjyprc_hadoop.browser.dwm_browser_event_aggregation_label_di
WHERE
    date=${date-1}
    and app_launch_way='点击icon'
    and app_open_cnt+app_duration_cnt>0
GROUP BY
    1,
    2
;
```

### 2. 浏览器有效DAU
**指标定义**: 浏览器的有效日活跃用户数
**数据源**: `iceberg_zjyprc_hadoop.browser.dwm_browser_event_aggregation_label_di`
**过滤条件**: `is_app_dau_2024=1` 且 `app_launch_way<>'第三方调起'` 且 `app_open_cnt>0`

```sql
--浏览器有效DAU
SELECT
    date,
    did
FROM
    iceberg_zjyprc_hadoop.browser.dwm_browser_event_aggregation_label_di
WHERE
    date=${date-1}
    and is_app_dau_2024=1
    and app_launch_way<>'第三方调起'
    and app_open_cnt>0
GROUP BY
    1,
    2
;
```

### 3. 浏览器消费UV
**指标定义**: 在浏览器中产生消费行为的用户数
**数据源**: `iceberg_zjyprc_hadoop.browser.dwm_browser_event_aggregation_label_di`
**过滤条件**: `consum_cnt_v2>0`

```sql
--浏览器消费UV
SELECT
    date,
    did
FROM
    iceberg_zjyprc_hadoop.browser.dwm_browser_event_aggregation_label_di
WHERE
    date=${date-1}
    and consum_cnt_v2>0
GROUP BY
    1,
    2
;
```

### 4. 浏览器一级页（列表页）vv
**指标定义**: 浏览器一级页面的浏览量
**数据源**: `iceberg_zjyprc_hadoop.browser.dwm_browser_event_aggregation_label_di`
**页面类型**: 一级页面（信息流、推荐等）
**计算逻辑**: 统计非置顶内容的曝光次数

```sql
--浏览器一级页（列表页）vv
SELECT
    date,
    sum(if (is_top=0, expos_cnt, 0)) vv
FROM
    iceberg_zjyprc_hadoop.browser.dwm_browser_event_aggregation_label_di
WHERE
    date=${date-1}
    and is_app_dau_2024=1
    and page in ('feed_info_topnews', 'feed_info_rec') -- v1口径
    and page in ('feed_info_','feed_info_333','feed_info_93yuebing','feed_info_car','feed_info_constellations','feed_info_culture','feed_info_currentPolitics','feed_info_dongmanduanju','feed_info_education','feed_info_emotion','feed_info_entertainment','feed_info_european_football','feed_info_fashion','feed_info_finance','feed_info_food','feed_info_game','feed_info_gaokao','feed_info_health','feed_info_history','feed_info_hotList','feed_info_hotlist','feed_info_household','feed_info_international','feed_info_jingdong','feed_info_lianghui','feed_info_location','feed_info_location_ChooseCity','feed_info_meione','feed_info_military','feed_info_newera','feed_info_novels','feed_info_olympic','feed_info_Olympic_2024','feed_info_parenting','feed_info_pneu','feed_info_Pressconference','feed_info_property','feed_info_rec','feed_info_science','feed_info_Shopping','feed_info_shortVideo','feed_info_skit','feed_info_smallGame','feed_info_society','feed_info_sport','feed_info_sport_cba','feed_info_sport_ChannelDetail','feed_info_sport_chinesefootball','feed_info_sport_dejia','feed_info_sport_fifa','feed_info_sport_nba','feed_info_sport_xijia','feed_info_sport_yijia','feed_info_sport_yingchao','feed_info_sport_zhongchao','feed_info_testIcon','feed_info_topnews','feed_info_tourism','feed_info_Travel','feed_info_videos','feed_info_xiaoshipin','feed_livestream_hot','feed_video_','feed_video_film','feed_video_food','feed_video_game','feed_video_immersion','feed_video_jokes','feed_video_military','feed_video_minivideo_exp','feed_video_rec','feed_video_shortv','feed_video_variety','feed_video_videos_exp')
GROUP BY
    1
;
```

### 5. 浏览器短会话uv
**指标定义**: 浏览器短会话的用户数
**数据源**: `iceberg_zjyprc_hadoop.browser.dwm_browser_event_aggregation_label_di`
**会话类型**: 短会话（有浏览或视频播放行为）
**页面类型**: 详情页、短视频等

```sql
--浏览器短会话uv
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
        'feed_shortvideo_immerse'
    ) and (view_cnt>0 or video_play_cnt>0)
GROUP BY
    1,
    2
;
```

### 6. 图文详情页浏览量vv/时长
**指标定义**: 图文详情页的浏览量和停留时长
**数据源**: `iceberg_zjyprc_hadoop.browser.dwm_browser_event_aggregation_label_di`
**页面类型**: 图文详情页
**内容类型**: 新闻
**计算指标**:
- UV: 有浏览行为的用户数
- VV: 非置顶内容的消费次数
- 时长: 页面停留时长（分钟）

```sql
--图文详情页浏览量vv/时长
SELECT
    date,
    count(
        distinct case
            when view_cnt>0 then did
            else null
        end
    ) uv,
    sum(if (is_top=0, consum_cnt_v2, 0)) vv, --vv
    sum(feed_dura)/60000 dura --时长
FROM
    iceberg_zjyprc_hadoop.browser.dwm_browser_event_aggregation_label_di
WHERE
    date=${date-1}
    and is_app_dau_2024=1
    and page='feed_content_detail'
    and item_type='news'
GROUP BY
    1
;
```

### 7. 视频资讯(老)(视频详情页)浏览量vv/时长
**指标定义**: 视频详情页的浏览量和停留时长
**数据源**: `iceberg_zjyprc_hadoop.browser.dwm_browser_event_aggregation_label_di`
**页面类型**: 视频详情页
**内容类型**: 内联视频
**计算指标**:
- UV: 有视频播放行为的用户数
- VV: 非置顶内容的消费次数
- 时长: 页面停留时长（分钟）

```sql
--视频资讯(老)(视频详情页)浏览量vv/时长
SELECT
    date,
    count(
        distinct case
            when video_play_cnt>0 then did
            else null
        end
    ) uv,
    sum(if (is_top=0, consum_cnt_v2, 0)) vv, --vv
    sum(feed_dura)/60000 dura --时长
FROM
    iceberg_zjyprc_hadoop.browser.dwm_browser_event_aggregation_label_di
WHERE
    date=${date-1}
    and is_app_dau_2024=1
    and page='feed_content_detail'
    and item_type='inline_video'
```

## 使用说明
1. 所有查询中的 `${date-1}` 表示前一天的日期
2. 时长相关指标需要除以60000转换为分钟
3. 用户去重使用 `did` 字段
4. 浏览器相关指标主要使用聚合表 `dwm_browser_event_aggregation_label_di`

## 注意事项
- 查询结果需要按日期分组
- 注意数据过滤条件，确保数据准确性
- 一级页面包含多个频道，需要完整列出
- 短会话和长会话需要分别统计
- 图文和视频详情页需要按内容类型分别统计
- 时长计算需要考虑边界值
- DAU指标需要区分启动方式和有效性