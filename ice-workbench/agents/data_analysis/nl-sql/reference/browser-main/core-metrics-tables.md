# Browser Main App - Core Metrics Tables & SQL Templates

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
  third_packagename STRING COMMENT '第三方调起包名',
  -- ... more fields
  PRIMARY KEY (date, did)
)
USING iceberg
PARTITIONED BY (date)
```

### Ad Event Table: dwm_browser_ad_event_aggregation_di

```sql
-- Used for ARPU metrics
CREATE TABLE iceberg_zjyprc_hadoop.browser.dwm_browser_ad_event_aggregation_di (
  date INT,
  did STRING,
  fee_amt BIGINT COMMENT '广告收入(分)',
  -- ... more fields
)
USING iceberg
PARTITIONED BY (date)
```

### Event Table: dwd_ot_event_di_31000000442

```sql
-- Used for third-party package name metrics
CREATE TABLE iceberg_zjyprc_hadoop.dw.dwd_ot_event_di_31000000442 (
  distinct_id STRING,
  event_name STRING,
  properties MAP<STRING, STRING>,
  date INT,
  -- ... more fields
)
USING iceberg
PARTITIONED BY (date, event_name)
```

---

## SQL Templates by Metric

### BM001: 浏览器DAU/日活

**Definition**: 日活跃用户数
**Filters**: `is_app_dau_2024=1`

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
GROUP BY
    date
ORDER BY
    date
;
```

---

### BM002: 浏览器分新老用户DAU/日活

**Definition**: 按新老用户分组的日活跃用户数
**Filters**: `is_app_dau_2024=1`

```sql
SELECT
    date,
    CASE WHEN is_new_2024 = 1 THEN 'new'
         WHEN is_new_2024 = 0 THEN 'old'
    END AS is_new_user,
    COUNT(DISTINCT did) AS uv
FROM
    iceberg_zjyprc_hadoop.browser.dwm_browser_event_aggregation_label_di
WHERE
    date >= '${start_date}'
    AND date <= '${end_date}'
    AND is_app_dau_2024 = 1
GROUP BY
    date,
    CASE WHEN is_new_2024 = 1 THEN 'new'
         WHEN is_new_2024 = 0 THEN 'old'
    END
ORDER BY
    date
;
```

---

### BM003: 浏览器MAU/月活

**Definition**: 近30天内的月活跃用户数
**Filters**: `is_app_dau_2024=1`

```sql
SELECT
    COUNT(DISTINCT did) AS mau
FROM
    iceberg_zjyprc_hadoop.browser.dwm_browser_event_aggregation_label_di
WHERE
    date >= '${start_date}'
    AND date <= '${end_date}'
    AND is_app_dau_2024 = 1
;
```

---

### BM004: 浏览器主启DAU/日活

**Definition**: 通过点击图标启动的日活跃用户数
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

### BM006: 浏览器有效DAU/日活

**Definition**: 有效日活跃用户数（排除第三方调起）
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

### BM007: 浏览器PUSH DAU/日活

**Definition**: 通过PUSH启动的日活跃用户数
**Filters**: `is_app_dau_2024=1` AND `app_launch_way LIKE '%push%'`

```sql
SELECT
    COUNT(DISTINCT did) AS uv
FROM
    iceberg_zjyprc_hadoop.browser.dwm_browser_event_aggregation_label_di
WHERE
    date >= '${start_date}'
    AND date <= '${end_date}'
    AND is_app_dau_2024 = 1
    AND app_launch_way LIKE '%push%'
;
```

---

### BM008: 浏览器分启动方式DAU/日活

**Definition**: 按启动方式分组的日活跃用户数
**Filters**: `is_app_dau_2024=1`

```sql
SELECT
    date,
    app_launch_way,
    COUNT(DISTINCT did) AS uv
FROM
    iceberg_zjyprc_hadoop.browser.dwm_browser_event_aggregation_label_di
WHERE
    date >= '${start_date}'
    AND date <= '${end_date}'
    AND is_app_dau_2024 = 1
GROUP BY
    date,
    app_launch_way
ORDER BY
    date
;
```

---

### BM009: 浏览器内容中心调起DAU/日活

**Definition**: 通过内容中心调起的日活跃用户数
**Filters**: `app_launch_way LIKE '%newhome%'`

```sql
SELECT
    date,
    COUNT(DISTINCT did) AS uv
FROM
    iceberg_zjyprc_hadoop.browser.dwm_browser_event_aggregation_label_di
WHERE
    date >= '${start_date}'
    AND date <= '${end_date}'
    AND app_launch_way LIKE '%newhome%'
GROUP BY
    date
ORDER BY
    date
;
```

---

### BM010: 浏览器三方调起DAU/日活

**Definition**: 通过第三方调起的日活跃用户数
**Filters**: `is_app_dau_2024=1` AND `app_launch_way='第三方调起'` AND `app_open_cnt>0`

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
    AND app_launch_way = '第三方调起'
    AND app_open_cnt > 0
GROUP BY
    date
ORDER BY
    date
;
```

---

### BM011: 浏览器三方调起分调起包名DAU/日活

**Definition**: 按调起包名分组的三方调起DAU
**Source**: Event table

```sql
SELECT
    date,
    properties['third_packagename'] AS third_packagename,
    COUNT(DISTINCT distinct_id) AS uv
FROM
    iceberg_zjyprc_hadoop.dw.dwd_ot_event_di_31000000442
WHERE
    date >= '${start_date}'
    AND date <= '${end_date}'
    AND event_name = 'app_open'
GROUP BY
    date,
    properties['third_packagename']
ORDER BY
    date
;
```

---

### BM012: 浏览器人均使用时长

**Definition**: 平均每用户使用时长（分钟）
**Formula**: `sum(app_dura)/60000/count(distinct did)`

```sql
SELECT
    SUM(app_dura) / 60000 / COUNT(DISTINCT did) AS avg_duration_min
FROM
    iceberg_zjyprc_hadoop.browser.dwm_browser_event_aggregation_label_di
WHERE
    date >= '${start_date}'
    AND date <= '${end_date}'
    AND is_app_dau_2024 = 1
;
```

---

### BM013: 浏览器人均启动次数

**Definition**: 平均每用户启动次数
**Formula**: `sum(app_open_cnt)/count(distinct did)`

```sql
SELECT
    SUM(app_open_cnt) / COUNT(DISTINCT did) AS avg_launch_count
FROM
    iceberg_zjyprc_hadoop.browser.dwm_browser_event_aggregation_label_di
WHERE
    date >= '${start_date}'
    AND date <= '${end_date}'
    AND is_app_dau_2024 = 1
;
```

---

### BM017: 浏览器ARPU

**Definition**: 活跃用户平均广告收入（元）
**Source**: Multi-table JOIN

```sql
SELECT
    a.date,
    SUM(fee) / COUNT(DISTINCT a.did) AS arpu
FROM
    (
        SELECT date, did
        FROM iceberg_zjyprc_hadoop.browser.dwm_browser_event_aggregation_label_di
        WHERE date >= '${start_date}' AND date <= '${end_date}'
          AND is_app_dau_2024 = 1
        GROUP BY date, did
    ) a
JOIN
    (
        SELECT date, did, SUM(fee_amt) / 100000 AS fee
        FROM iceberg_zjyprc_hadoop.browser.dwm_browser_ad_event_aggregation_di
        WHERE date >= '${start_date}' AND date <= '${end_date}'
        GROUP BY date, did
    ) b
ON a.date = b.date AND a.did = b.did
GROUP BY a.date
ORDER BY a.date
;
```

---

### BM019: 浏览器深度用户DAU

**Definition**: 使用时长 >= 20分钟的深度活跃用户数

```sql
SELECT
    date,
    COUNT(DISTINCT did) AS uv
FROM
    (
        SELECT
            date,
            did,
            SUM(app_dura) / 60000 AS app_dura_min
        FROM
            iceberg_zjyprc_hadoop.browser.dwm_browser_event_aggregation_label_di
        WHERE
            date >= '${start_date}'
            AND date <= '${end_date}'
            AND is_app_dau_2024 = 1
        GROUP BY date, did
    ) a
WHERE
    app_dura_min >= 20
GROUP BY
    date
ORDER BY
    date
;
```

---

### BM020: 浏览器中度用户DAU

**Definition**: 使用时长在 13~20 分钟之间的中度活跃用户数

```sql
SELECT
    date,
    COUNT(DISTINCT did) AS uv
FROM
    (
        SELECT
            date,
            did,
            SUM(app_dura) / 60000 AS app_dura_min
        FROM
            iceberg_zjyprc_hadoop.browser.dwm_browser_event_aggregation_label_di
        WHERE
            date >= '${start_date}'
            AND date <= '${end_date}'
            AND is_app_dau_2024 = 1
        GROUP BY date, did
    ) a
WHERE
    app_dura_min >= 13 AND app_dura_min < 20
GROUP BY
    date
ORDER BY
    date
;
```

---

### BM021: 浏览器轻度用户DAU

**Definition**: 使用时长 < 13分钟的轻度活跃用户数

```sql
SELECT
    date,
    COUNT(DISTINCT did) AS uv
FROM
    (
        SELECT
            date,
            did,
            SUM(app_dura) / 60000 AS app_dura_min
        FROM
            iceberg_zjyprc_hadoop.browser.dwm_browser_event_aggregation_label_di
        WHERE
            date >= '${start_date}'
            AND date <= '${end_date}'
            AND is_app_dau_2024 = 1
        GROUP BY date, did
    ) a
WHERE
    app_dura_min >= 0 AND app_dura_min < 13
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
5. **Partition Filter**: Always include `date` in WHERE clause
