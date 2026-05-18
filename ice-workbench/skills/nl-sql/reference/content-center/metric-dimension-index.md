# Content Center - Metric Dimension Index

Common dimensions for metric queries.

## Dimension Mapping

| Metric ID | Metric Name | Dimensions |
|-----------|-------------|------------|
| CC001 | 内容中心DAU/日活 | (no group, aggregate) |
| CC002 | 内容中心分新老用户DAU/日活 | date, is_new_2024 |
| CC003 | 内容中心深度DAU/日活 | date |
| CC004 | 内容中心有效DAU/日活 | (no group, aggregate) |
| CC005 | 内容中心MAU | (no group, aggregate) |
| CC006 | 内容中心时长 | (no group, aggregate) |
| CC007 | 内容中心人均时长 | (no group, aggregate) |
| CC008 | 内容中心消费DAU | (no group, aggregate) |
| CC009 | 内容中心消费UV | (no group, aggregate) |
| CC010 | 内容中心VV | (no group, aggregate) |
| CC011 | 内容中心人均VV | (no group, aggregate) |
| CC012 | 内容中心消费时长 | (no group, aggregate) |
| CC013 | 内容中心人均消费时长 | (no group, aggregate) |
| CC014 | 内容中心分体裁消费UV | item_type |
| CC015 | 内容中心分体裁VV | item_type |
| CC016 | 内容中心分体裁消费时长 | item_type |
| CC017 | 内容中心分频道消费UV | feed_channel |
| CC018 | 内容中心分频道VV | feed_channel |
| CC019 | 内容中心分频道消费时长 | feed_channel |

---

## Dimension Fields

| Dimension | Field | Description |
|-----------|-------|-------------|
| Date | date | Partition field, format YYYYMMDD |
| Device ID | did | Device unique ID for deduplication |
| User ID | distinct_id | Tracking system user ID |
| New User | is_new_2024 | 1=new user, 0=old user |
| Content Type | item_type | Content type: news, video, minivideo |
| Channel | feed_channel | Feed channel |
| Duration | app_dura | Usage duration in milliseconds |
| Consumption Count | consum_cnt | Content consumption count |
| Consumption Duration | consum_dura | Content consumption duration in milliseconds |

---

## Dimension Mapping Table

| User Query | Mapped Dimension | SQL Field |
|------------|------------------|-----------|
| "按日期" | Date | date |
| "按体裁" | Content Type | item_type |
| "按频道" | Channel | feed_channel |
| "按新老用户" | New User | is_new_2024 |
