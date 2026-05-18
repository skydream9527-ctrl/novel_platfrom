# Content Center - Core Metrics Tables & SQL Templates

## Table Schema

### Main Table: dwm_newhome_event_aggregation_label_di

```sql
CREATE TABLE iceberg_zjyprc_hadoop.newhome.dwm_newhome_event_aggregation_label_di (
  date INT COMMENT '日期',
  did STRING COMMENT 'did',
  imei1 STRING COMMENT 'imei1',
  oaid STRING COMMENT 'oaid',
  device_id STRING COMMENT '设备id',
  android_id STRING COMMENT '安卓id',
  model STRING COMMENT '机型',
  miui STRING COMMENT 'MIUI版本号',
  build STRING COMMENT '版本类型',
  os_ver STRING COMMENT '系统版本',
  app_ver STRING COMMENT 'APP版本号',
  version_code STRING COMMENT 'APP版本编号',
  toutiao_user_id STRING COMMENT '头条匿名id',
  session_id STRING COMMENT '会话ID（app退出重置）',
  net STRING COMMENT '网络（WIFI/5G/4G/3G/2G/ETHERNET/NONE/UNKNOWN）',
  country STRING COMMENT '国家',
  province STRING COMMENT '省份',
  city STRING COMMENT '城市',
  eid STRING COMMENT '实验id',
  ad_exp_id STRING COMMENT '商业化广告实验ID',
  app_launch_way STRING COMMENT '进入内容中心方式',
  feed_channel STRING COMMENT '频道',
  item_docid STRING COMMENT '内容id',
  item_type STRING COMMENT '内容类型。图文：news 视频：video 小视频：minivideo',
  item_title STRING COMMENT '内容标题',
  item_author STRING COMMENT '作者',
  item_position STRING COMMENT '曝光位置',
  is_first_screen INT COMMENT '是否首屏内容',
  is_first_item INT COMMENT '是否首条内容',
  is_top INT COMMENT '是否置顶',
  is_new_2024 INT COMMENT '是否新用户',
  is_dau_2024 INT COMMENT '是否日活用户',
  app_open_cnt BIGINT COMMENT 'app打开次数',
  app_dura BIGINT COMMENT 'app停留时长ms',
  expos_cnt BIGINT COMMENT '内容曝光量',
  click_cnt BIGINT COMMENT '内容点击量',
  view_cnt BIGINT COMMENT '内容浏览量',
  video_play_cnt BIGINT COMMENT '视频播放量',
  like_cnt BIGINT COMMENT '点赞量',
  share_cnt BIGINT COMMENT '分享量',
  collect_cnt BIGINT COMMENT '收藏量',
  consum_cnt BIGINT COMMENT '消费次数',
  consum_dura BIGINT COMMENT '消费时长ms',
  -- ... more fields
  PRIMARY KEY (date, did)
)
USING iceberg
PARTITIONED BY (date)
```

### Event Table: dwd_ot_event_di_31000000297

```sql
-- Used for valid DAU metrics
CREATE TABLE iceberg_zjyprc_hadoop.dw.dwd_ot_event_di_31000000297 (
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

### CC001: 内容中心DAU/日活

**Definition**: 内容中心日活跃用户数
**Filters**: `is_dau_2024=1`

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

---

### CC002: 内容中心分新老用户DAU/日活

**Definition**: 按新老用户分组的内容中心日活跃用户数
**Filters**: `is_dau_2024=1`

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
ORDER BY
    date
;
```

---

### CC003: 内容中心深度DAU/日活

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
            iceberg_zjyprc_hadoop.newhome.dwm_newhome_event_aggregation_label_di
        WHERE
            date >= '${start_date}'
            AND date <= '${end_date}'
            AND is_dau_2024 = 1
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

### CC004: 内容中心有效DAU/日活

**Definition**: 有效日活跃用户数（有交互行为）
**Source**: Event table

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

---

### CC005: 内容中心MAU

**Definition**: 近30天内的月活跃用户数
**Filters**: `is_dau_2024=1`

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

---

### CC006: 内容中心时长

**Definition**: 用户总使用时长（分钟）
**Formula**: `sum(app_dura)/60000`

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

---

### CC007: 内容中心人均时长

**Definition**: 平均每用户使用时长（分钟）
**Formula**: `sum(app_dura)/60000/count(distinct did)`

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

---

### CC008: 内容中心消费DAU

**Definition**: 有内容消费行为的日活跃用户数
**Filters**: `is_dau_2024=1` AND `consum_cnt>0`

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

---

### CC009: 内容中心消费UV

**Definition**: 有内容消费行为的用户数
**Filters**: `is_dau_2024=1` AND `consum_cnt>0`

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

---

### CC010: 内容中心VV

**Definition**: 内容消费总次数（VV）
**Filters**: `is_dau_2024=1` AND `consum_cnt>0`

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

---

### CC011: 内容中心人均VV

**Definition**: 平均每用户内容消费次数
**Formula**: `sum(consum_cnt)/count(distinct did)`

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

---

### CC012: 内容中心消费时长

**Definition**: 内容消费总时长（分钟）
**Formula**: `sum(consum_dura)/60000`

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

---

### CC013: 内容中心人均消费时长

**Definition**: 平均每用户内容消费时长（分钟）
**Formula**: `sum(consum_dura)/60000/count(distinct did)`

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

---

### CC014: 内容中心分体裁消费UV

**Definition**: 按内容体裁分组的消费用户数
**Filters**: `is_dau_2024=1` AND `consum_cnt>0`

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
GROUP BY
    item_type
ORDER BY
    uv DESC
;
```

---

### CC015: 内容中心分体裁VV

**Definition**: 按内容体裁分组的消费次数
**Filters**: `is_dau_2024=1` AND `consum_cnt>0`

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
GROUP BY
    item_type
ORDER BY
    vv DESC
;
```

---

### CC016: 内容中心分体裁消费时长

**Definition**: 按内容体裁分组的消费时长
**Filters**: `is_dau_2024=1` AND `consum_dura>0`

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
GROUP BY
    item_type
ORDER BY
    duration_min DESC
;
```

---

### CC017: 内容中心分频道消费UV

**Definition**: 按频道分组的消费用户数
**Filters**: `is_dau_2024=1` AND `consum_cnt>0`

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
GROUP BY
    feed_channel
ORDER BY
    uv DESC
;
```

---

### CC018: 内容中心分频道VV

**Definition**: 按频道分组的消费次数
**Filters**: `is_dau_2024=1` AND `consum_cnt>0`

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
GROUP BY
    feed_channel
ORDER BY
    vv DESC
;
```

---

### CC019: 内容中心分频道消费时长

**Definition**: 按频道分组的消费时长
**Filters**: `is_dau_2024=1` AND `consum_dura>0`

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
GROUP BY
    feed_channel
ORDER BY
    duration_min DESC
;
```

---

## Usage Notes

1. **Date Format**: Always use `'YYYYMMDD'` format (e.g., `'20260330'`)
2. **Date Range**: Replace `${start_date}` and `${end_date}` with actual dates
3. **User Deduplication**: Use `COUNT(DISTINCT did)` for UV metrics
4. **Duration**: Divide by 60000 to convert milliseconds to minutes
5. **Partition Filter**: Always include `date` in WHERE clause
