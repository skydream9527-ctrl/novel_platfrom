# Browser Main App - Metric Name Index

Quick lookup table for metric names.

## Metrics List

| Metric ID | Metric Name (CN) | Metric Name (EN) | Category |
|-----------|------------------|------------------|----------|
| BM001 | 浏览器DAU/日活 | browser_dau | User Scale |
| BM002 | 浏览器分新老用户DAU/日活 | browser_dau_by_new_user | User Scale |
| BM003 | 浏览器MAU/月活 | browser_mau | User Scale |
| BM004 | 浏览器主启DAU/日活 | browser_main_launch_dau | User Scale |
| BM005 | 浏览器主启MAU/月活 | browser_main_launch_mau | User Scale |
| BM006 | 浏览器有效DAU/日活 | browser_valid_dau | User Scale |
| BM007 | 浏览器PUSH DAU/日活 | browser_push_dau | User Scale |
| BM008 | 浏览器分启动方式DAU/日活 | browser_dau_by_launch_way | User Scale |
| BM009 | 浏览器内容中心调起DAU/日活 | browser_newhome_launch_dau | User Scale |
| BM010 | 浏览器三方调起DAU/日活 | browser_third_party_launch_dau | User Scale |
| BM011 | 浏览器三方调起分调起包名DAU/日活 | browser_third_party_launch_by_package_dau | User Scale |
| BM012 | 浏览器人均使用时长 | browser_avg_duration | Engagement |
| BM013 | 浏览器人均启动次数 | browser_avg_launch_count | Engagement |
| BM014 | 浏览器人均主动启动次数 | browser_avg_active_launch_count | Engagement |
| BM015 | 浏览器人均PUSH启动次数 | browser_avg_push_launch_count | Engagement |
| BM016 | 浏览器人均三方启动次数 | browser_avg_third_party_launch_count | Engagement |
| BM017 | 浏览器ARPU | browser_arpu | Revenue |
| BM018 | 浏览器分启动方式ARPU | browser_arpu_by_launch_way | Revenue |
| BM019 | 浏览器深度用户DAU | browser_deep_user_dau | User Segment |
| BM020 | 浏览器中度用户DAU | browser_medium_user_dau | User Segment |
| BM021 | 浏览器轻度用户DAU | browser_light_user_dau | User Segment |

---

## Usage

When user mentions a metric, map it to the corresponding Metric ID and look up the SQL template.

### Example Mapping

| User Input | Mapped Metric | Metric ID |
|------------|---------------|-----------|
| "浏览器DAU" | 浏览器DAU/日活 | BM001 |
| "主启DAU" | 浏览器主启DAU/日活 | BM004 |
| "人均时长" | 浏览器人均使用时长 | BM012 |
| "深度用户" | 浏览器深度用户DAU | BM019 |
| "ARPU" | 浏览器ARPU | BM017 |
