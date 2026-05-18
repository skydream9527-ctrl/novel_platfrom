# Browser Feed Core Metrics Tables & SQL Templates

## Table Schema

### Main Table: dwm_browser_event_aggregation_label_di

```sql
CREATE TABLE iceberg_zjyprc_hadoop.browser.dwm_browser_event_aggregation_label_di (
  date INT COMMENT '日期',
  did STRING COMMENT 'did',
  imei1 STRING COMMENT 'imei1',
  imei2 STRING COMMENT 'imei2',
  oaid STRING COMMENT 'oaid',
  device_id STRING COMMENT '设备id',
  android_id STRING COMMENT '安卓id',
  model STRING COMMENT '机型',
  miui STRING COMMENT 'MIUI版本号',
  build STRING COMMENT '版本类型',
  os_ver STRING COMMENT '系统版本',
  app_ver STRING COMMENT '客户端版本',
  version_code STRING COMMENT 'APP版本编号',
  toutiao_user_id STRING COMMENT '头条匿名id',
  session_id STRING COMMENT '会话ID（app退出重置）',
  net STRING COMMENT '网络（WIFI/5G/4G/3G/2G/ETHERNET/NONE/UNKNOWN）',
  country STRING COMMENT '国家',
  province STRING COMMENT '省份',
  city STRING COMMENT '城市',
  exp_id STRING COMMENT '实验id',
  ad_exp_id STRING COMMENT '广告实验id',
  app_launch_way STRING COMMENT '进入浏览器方式',
  feed_channel STRING COMMENT '频道',
  page STRING COMMENT '页面',
  from_page STRING COMMENT '操作上级页面',
  item_docid STRING COMMENT '内容id',
  item_title STRING COMMENT '内容标题',
  item_type STRING COMMENT '内容类型',
  item_author STRING COMMENT '作者',
  item_position STRING COMMENT '曝光位置',
  is_app_dau_2024 INT COMMENT '是否浏览器DAU用户',
  is_dau_feed_dapan_2024 INT COMMENT '是否浏览器信息流大盘DAU用户',
  is_new_2024 INT COMMENT '是否是浏览器新用户',
  is_top INT COMMENT '是否置顶',
  app_open_cnt BIGINT COMMENT '浏览器打开量',
  app_dura BIGINT COMMENT '停留总时长(毫秒)',
  expos_cnt BIGINT COMMENT '内容曝光量',
  click_cnt BIGINT COMMENT '内容点击量',
  view_cnt BIGINT COMMENT '内容浏览量',
  video_play_cnt BIGINT COMMENT '视频播放量',
  like_cnt BIGINT COMMENT '点赞量',
  share_cnt BIGINT COMMENT '分享量',
  collect_cnt BIGINT COMMENT '收藏量',
  feed_dura BIGINT COMMENT '信息流时长(毫秒)',
  consum_cnt_v2 BIGINT COMMENT '内容消费次数',
  consum_dura BIGINT COMMENT '内容消费时长(毫秒)',
  search_cnt BIGINT COMMENT '搜索次数',
  -- ... more fields
  PRIMARY KEY (date, did)
)
USING iceberg
PARTITIONED BY (date)
```

### Event Table: dwd_ot_event_di_31000000442

```sql
CREATE TABLE iceberg_zjyprc_hadoop.dw.dwd_ot_event_di_31000000442 (
  distinct_id STRING COMMENT 'distinct_id',
  event_name STRING COMMENT '事件名称',
  properties MAP<STRING, STRING> COMMENT '事件属性',
  date INT COMMENT '日期',
  -- ... more fields
)
USING iceberg
PARTITIONED BY (date, event_name)
```

---

## SQL Templates by Metric

### BM001: 浏览器主启DAU

**Definition**: 通过点击图标启动浏览器的日活跃用户数
**Filters**: `app_launch_way='点击icon'` AND `app_open_cnt+app_duration_cnt>0`

```sql
SELECT
    date,
    COUNT(DISTINCT did) AS uv
FROM
    iceberg_zjyprc_hadoop.browser.dwm_browser_event_aggregation_label_di
WHERE
    date >= '${start_date}'
    AND date <= '${end_date}'
    AND app_launch_way = '点击icon'
    AND app_open_cnt + app_duration_cnt > 0
GROUP BY
    date
ORDER BY
    date
;
```

---

### BM002: 浏览器有效DAU

**Definition**: 浏览器的有效日活跃用户数
**Filters**: `is_app_dau_2024=1` AND `app_launch_way<>'第三方调起'` AND `app_open_cnt>0`

```sql
SELECT
    date,
    COUNT(DISTINCT did) AS uv
FROM
    iceberg_zjyprc_hadoop.browser.dwm_browser_event_aggregation_label_di
WHERE
    date >= '${start_date}'
    AND date <= '${end_date}'
    AND is_app_dau_2024 = 1
    AND app_launch_way <> '第三方调起'
    AND app_open_cnt > 0
GROUP BY
    date
ORDER BY
    date
;
```

---

### BM003: 浏览器消费UV

**Definition**: 在浏览器中产生消费行为的用户数
**Filters**: `consum_cnt_v2 > 0`

```sql
SELECT
    date,
    COUNT(DISTINCT did) AS uv
FROM
    iceberg_zjyprc_hadoop.browser.dwm_browser_event_aggregation_label_di
WHERE
    date >= '${start_date}'
    AND date <= '${end_date}'
    AND consum_cnt_v2 > 0
GROUP BY
    date
ORDER BY
    date
;
```

---

### BF001: 浏览器一级页VV

**Definition**: 浏览器一级页面的浏览量
**Filters**: `is_app_dau_2024=1` AND `is_top=0`

```sql
SELECT
    date,
    SUM(IF(is_top = 0, expos_cnt, 0)) AS vv
FROM
    iceberg_zjyprc_hadoop.browser.dwm_browser_event_aggregation_label_di
WHERE
    date >= '${start_date}'
    AND date <= '${end_date}'
    AND is_app_dau_2024 = 1
    AND page IN (
        'feed_info_topnews', 'feed_info_rec', 'feed_info_car',
        'feed_info_finance', 'feed_info_entertainment', 'feed_info_sport',
        'feed_video_rec', 'feed_video_immersion'
        -- ... more pages
    )
GROUP BY
    date
ORDER BY
    date
;
```

---

### BF002: 浏览器短会话UV

**Definition**: 浏览器短会话的用户数
**Filters**: `is_app_dau_2024=1` AND `(view_cnt>0 OR video_play_cnt>0)`

```sql
SELECT
    date,
    COUNT(DISTINCT did) AS uv
FROM
    iceberg_zjyprc_hadoop.browser.dwm_browser_event_aggregation_label_di
WHERE
    date >= '${start_date}'
    AND date <= '${end_date}'
    AND is_app_dau_2024 = 1
    AND page IN (
        'feed_content_detail',
        'feed_minivideo_continuously_root',
        'feed_minivideo_continuously',
        'feed_shortvideo_immerse_root',
        'feed_shortvideo_immerse'
    )
    AND (view_cnt > 0 OR video_play_cnt > 0)
GROUP BY
    date
ORDER BY
    date
;
```

---

### BF003: 浏览器长会话UV

**Definition**: 浏览器长会话的用户数（短视频+小说）
**Source**: Multi-table JOIN

```sql
SELECT
    COALESCE(a.date, b.date) AS date,
    COUNT(DISTINCT COALESCE(a.did, b.did)) AS uv
FROM
    (
        SELECT date, did
        FROM iceberg_zjyprc_hadoop.browser.dwm_browser_event_aggregation_label_di
        WHERE date >= '${start_date}' AND date <= '${end_date}'
          AND is_app_dau_2024 = 1
          AND page = 'lightapp_skit_detail'
          AND video_play_cnt > 0
        GROUP BY date, did
    ) a
FULL OUTER JOIN
    (
        SELECT date, distinct_id AS did
        FROM iceberg_zjyprc_hadoop.dw.dwd_ot_event_di_31000000442
        WHERE date >= '${start_date}' AND date <= '${end_date}'
          AND event_name = 'book_read_quit_sdk'
          AND properties['book_type'] IN ('store', 'pre_add_book', 'pirate', 'shortstory')
        GROUP BY date, distinct_id
    ) b ON a.date = b.date AND a.did = b.did
GROUP BY
    COALESCE(a.date, b.date)
ORDER BY
    date
;
```

---

### BF005: 图文详情页VV/时长

**Definition**: 图文详情页的浏览量和停留时长
**Filters**: `page='feed_content_detail'` AND `item_type='news'`

```sql
SELECT
    date,
    COUNT(DISTINCT CASE WHEN view_cnt > 0 THEN did END) AS uv,
    SUM(IF(is_top = 0, consum_cnt_v2, 0)) AS vv,
    SUM(feed_dura) / 60000 AS duration_min
FROM
    iceberg_zjyprc_hadoop.browser.dwm_browser_event_aggregation_label_di
WHERE
    date >= '${start_date}'
    AND date <= '${end_date}'
    AND is_app_dau_2024 = 1
    AND page = 'feed_content_detail'
    AND item_type = 'news'
GROUP BY
    date
ORDER BY
    date
;
```

---

### BF006: 视频详情页VV/时长

**Definition**: 视频详情页的浏览量和停留时长
**Filters**: `page='feed_content_detail'` AND `item_type='inline_video'`

```sql
SELECT
    date,
    COUNT(DISTINCT CASE WHEN video_play_cnt > 0 THEN did END) AS uv,
    SUM(IF(is_top = 0, consum_cnt_v2, 0)) AS vv,
    SUM(feed_dura) / 60000 AS duration_min
FROM
    iceberg_zjyprc_hadoop.browser.dwm_browser_event_aggregation_label_di
WHERE
    date >= '${start_date}'
    AND date <= '${end_date}'
    AND is_app_dau_2024 = 1
    AND page = 'feed_content_detail'
    AND item_type = 'inline_video'
GROUP BY
    date
ORDER BY
    date
;
```

---

### BF007: 浏览器搜索SUG页UV

**Definition**: 浏览器搜索建议页面的用户访问数
**Event**: `search_sugpage_expose`

```sql
SELECT
    date,
    COUNT(DISTINCT distinct_id) AS uv
FROM
    iceberg_zjyprc_hadoop.dw.dwd_ot_event_di_31000000442
WHERE
    date >= '${start_date}'
    AND date <= '${end_date}'
    AND event_name = 'search_sugpage_expose'
GROUP BY
    date
ORDER BY
    date
;
```

---

### BF008: 浏览器开屏UV

**Definition**: 浏览器开屏广告的用户曝光数
**Event**: `ad_app_intercept_server_request`

```sql
SELECT
    date,
    COUNT(DISTINCT distinct_id) AS uv
FROM
    iceberg_zjyprc_hadoop.dw.dwd_ot_event_di_31000000442
WHERE
    date >= '${start_date}'
    AND date <= '${end_date}'
    AND event_name = 'ad_app_intercept_server_request'
GROUP BY
    date
ORDER BY
    date
;
```

---

## Usage Notes

1. **Date Format**: Always use `'YYYYMMDD'` format (e.g., `'20260330'`)
2. **Date Range**: Replace `${start_date}` and `${end_date}` with actual dates
3. **User Deduplication**: Use `COUNT(DISTINCT did)` for UV metrics
4. **Duration**: Divide by 60000 to convert milliseconds to minutes
5. **Partition Filter**: Always include `date` in WHERE clause to avoid full table scan
