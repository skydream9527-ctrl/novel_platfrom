# Browser Main App - Metric Dimension Index

Common dimensions for metric queries.

## Dimension Mapping

| Metric ID | Metric Name | Dimensions |
|-----------|-------------|------------|
| BM001 | 浏览器DAU/日活 | date |
| BM002 | 浏览器分新老用户DAU/日活 | date, is_new_2024 |
| BM003 | 浏览器MAU/月活 | (no group, aggregate) |
| BM004 | 浏览器主启DAU/日活 | date |
| BM005 | 浏览器主启MAU/月活 | (no group, aggregate) |
| BM006 | 浏览器有效DAU/日活 | date |
| BM007 | 浏览器PUSH DAU/日活 | (no group, aggregate) |
| BM008 | 浏览器分启动方式DAU/日活 | date, app_launch_way |
| BM009 | 浏览器内容中心调起DAU/日活 | date |
| BM010 | 浏览器三方调起DAU/日活 | date |
| BM011 | 浏览器三方调起分调起包名DAU/日活 | date, third_packagename |
| BM012 | 浏览器人均使用时长 | (no group, aggregate) |
| BM013 | 浏览器人均启动次数 | (no group, aggregate) |
| BM014 | 浏览器人均主动启动次数 | (no group, aggregate) |
| BM015 | 浏览器人均PUSH启动次数 | (no group, aggregate) |
| BM016 | 浏览器人均三方启动次数 | (no group, aggregate) |
| BM017 | 浏览器ARPU | date |
| BM018 | 浏览器分启动方式ARPU | date, app_launch_way |
| BM019 | 浏览器深度用户DAU | date |
| BM020 | 浏览器中度用户DAU | date |
| BM021 | 浏览器轻度用户DAU | date |

---

## Dimension Fields

| Dimension | Field | Description |
|-----------|-------|-------------|
| Date | date | Partition field, format YYYYMMDD |
| Device ID | did | Device unique ID for deduplication |
| User ID | distinct_id | Tracking system user ID |
| Launch Way | app_launch_way | App launch source: 点击icon, 第三方调起, push, etc. |
| New User | is_new_2024 | 1=new user, 0=old user |
| Package Name | third_packagename | Third-party app package name |
| Duration | app_dura | Usage duration in milliseconds |
| Launch Count | app_open_cnt | App open count |

---

## User Segment Definition

| Segment | Duration Range |
|---------|---------------|
| Deep User (深度用户) | >= 20 minutes |
| Medium User (中度用户) | 13-20 minutes |
| Light User (轻度用户) | < 13 minutes |

---

## Dimension Mapping Table

| User Query | Mapped Dimension | SQL Field |
|------------|------------------|-----------|
| "按日期" | Date | date |
| "按启动方式" | Launch Way | app_launch_way |
| "按新老用户" | New User | is_new_2024 |
| "按调起包名" | Package Name | third_packagename |
