# Metric Dimension Index

Common dimensions for metric queries across all business lines.

## Time Dimensions

| Dimension | Format | Example | Description |
|-----------|--------|---------|-------------|
| date | YYYYMMDD | 20260330 | Partition field, required in WHERE |
| date_range | YYYYMMDD~YYYYMMDD | 20260301~20260330 | Date range query |
| relative_date | last_N_days | last_7_days | Relative date range |

## User Dimensions

| Dimension | Field | Type | Description |
|-----------|-------|------|-------------|
| User ID | did | STRING | Device ID, used for user deduplication |
| User Type | is_app_dau_2024 | INT | DAU flag (1=yes, 0=no) |
| User Type | is_new_2024 | INT | New user flag (1=yes, 0=no) |
| Launch Way | app_launch_way | STRING | App launch method (点击icon/第三方调起/push) |

## Content Dimensions

| Dimension | Field | Type | Values |
|-----------|-------|------|--------|
| Page | page | STRING | feed_info_topnews, feed_content_detail, etc. |
| Content Type | item_type | STRING | news, inline_video, vertical_video, mini_video |
| Content Position | item_position | STRING | Content exposure position |
| Is Top | is_top | INT | Pinned content (1=yes, 0=no) |

## Device Dimensions

| Dimension | Field | Type | Description |
|-----------|-------|------|-------------|
| Model | model | STRING | Device model |
| System Version | os_ver | STRING | OS version |
| App Version | app_ver | STRING | App version |
| Network | net | STRING | WIFI/5G/4G/3G/2G/UNKNOWN |

## Location Dimensions

| Dimension | Field | Type | Description |
|-----------|-------|------|-------------|
| Country | country | STRING | Country |
| Province | province | STRING | Province |
| City | city | STRING | City |

## Event Dimensions (埋点数据)

| Dimension | Field | Type | Description |
|-----------|-------|------|-------------|
| Event Name | event_name | STRING | Event identifier |
| Event Properties | properties | MAP | Event properties (key-value pairs) |

---

## Common Dimension Combinations

### User Scale Metrics
```sql
-- Required dimensions: date, did
-- Common filters: is_app_dau_2024, app_launch_way
SELECT date, COUNT(DISTINCT did) as uv
FROM ...
WHERE date = '20260330'
  AND is_app_dau_2024 = 1
GROUP BY date
```

### Page View Metrics
```sql
-- Required dimensions: date, page
-- Common filters: is_top, item_type
SELECT date, SUM(CASE WHEN is_top=0 THEN expos_cnt ELSE 0 END) as vv
FROM ...
WHERE date = '20260330'
  AND page IN ('feed_info_topnews', 'feed_info_rec')
GROUP BY date
```

### Event Metrics
```sql
-- Required dimensions: date, event_name, distinct_id
-- Common filters: properties['key']
SELECT date, COUNT(DISTINCT distinct_id) as uv
FROM ...
WHERE date = '20260330'
  AND event_name = 'search_sugpage_expose'
GROUP BY date
```

---

## Dimension Mapping Table

| User Query | Mapped Dimension | SQL Field |
|------------|------------------|-----------|
| "按日期" | Time | date |
| "按机型" | Device | model |
| "按版本" | App Version | app_ver |
| "按网络" | Network | net |
| "按省份" | Location | province |
| "按页面" | Page | page |
| "按内容类型" | Content Type | item_type |
| "按启动方式" | Launch Way | app_launch_way |
