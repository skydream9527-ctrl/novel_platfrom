# Content Center - Metric Name Index

Quick lookup table for metric names.

## Metrics List

| Metric ID | Metric Name (CN) | Metric Name (EN) | Category |
|-----------|------------------|------------------|----------|
| CC001 | 内容中心DAU/日活 | content_center_dau | User Scale |
| CC002 | 内容中心分新老用户DAU/日活 | content_center_dau_by_new_user | User Scale |
| CC003 | 内容中心深度DAU/日活 | content_center_deep_dau | User Scale |
| CC004 | 内容中心有效DAU/日活 | content_center_valid_dau | User Scale |
| CC005 | 内容中心MAU | content_center_mau | User Scale |
| CC006 | 内容中心时长 | content_center_duration | Engagement |
| CC007 | 内容中心人均时长 | content_center_avg_duration | Engagement |
| CC008 | 内容中心消费DAU | content_center_consumption_dau | Consumption |
| CC009 | 内容中心消费UV | content_center_consumption_uv | Consumption |
| CC010 | 内容中心VV | content_center_vv | Consumption |
| CC011 | 内容中心人均VV | content_center_avg_vv | Consumption |
| CC012 | 内容中心消费时长 | content_center_consumption_duration | Consumption |
| CC013 | 内容中心人均消费时长 | content_center_avg_consumption_duration | Consumption |
| CC014 | 内容中心分体裁消费UV | content_center_consumption_uv_by_type | Consumption |
| CC015 | 内容中心分体裁VV | content_center_vv_by_type | Consumption |
| CC016 | 内容中心分体裁消费时长 | content_center_consumption_duration_by_type | Consumption |
| CC017 | 内容中心分频道消费UV | content_center_consumption_uv_by_channel | Consumption |
| CC018 | 内容中心分频道VV | content_center_vv_by_channel | Consumption |
| CC019 | 内容中心分频道消费时长 | content_center_consumption_duration_by_channel | Consumption |

---

## Usage

When user mentions a metric, map it to the corresponding Metric ID and look up the SQL template.

### Example Mapping

| User Input | Mapped Metric | Metric ID |
|------------|---------------|-----------|
| "内容中心DAU" | 内容中心DAU/日活 | CC001 |
| "消费UV" | 内容中心消费UV | CC009 |
| "人均时长" | 内容中心人均时长 | CC007 |
| "分体裁VV" | 内容中心分体裁VV | CC015 |
