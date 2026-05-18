# 内容中心核心指标参考代码

## 概述
本文档包含内容中心的核心业务指标SQL查询代码，用于业务分析和运营监控。

## 指标说明

### 1. 内容中心DAU
**指标定义**: 内容中心的日活跃用户数
**数据源**: `iceberg_zjyprc_hadoop.newhome.dwm_newhome_event_aggregation_label_di`
**过滤条件**: `is_dau_2024=1`

```sql
--内容中心DAU
SELECT
    date,
    did
FROM
    iceberg_zjyprc_hadoop.newhome.dwm_newhome_event_aggregation_label_di
WHERE
    date=${date-1}
    and is_dau_2024=1
GROUP BY
    1,
    2
;
```

### 2. 内容中心消费UV
**指标定义**: 在内容中心产生消费行为的用户数
**数据源**: `iceberg_zjyprc_hadoop.newhome.dwm_newhome_event_aggregation_label_di`
**过滤条件**: `consum_cnt>0`

```sql
--内容中心消费UV
SELECT
    date,
    did
FROM
    iceberg_zjyprc_hadoop.newhome.dwm_newhome_event_aggregation_label_di
WHERE
    date=${date-1}
    and consum_cnt>0
GROUP BY
    1,
    2
;
```

### 3. 总VV
**指标定义**: 内容中心的总浏览量（排除置顶内容）
**数据源**: `iceberg_zjyprc_hadoop.newhome.dwm_newhome_event_aggregation_label_di`
**计算逻辑**: 统计非置顶内容的消费次数

```sql
--总VV
SELECT
    date,
    sum(if (is_top=0, consum_cnt, 0)) vv
FROM
    iceberg_zjyprc_hadoop.newhome.dwm_newhome_event_aggregation_label_di
WHERE
    date=${date-1}
    and is_dau_2024=1
GROUP BY
    1
;
```

### 4. 内容中心总时长
**指标定义**: 内容中心的总使用时长（分钟）
**数据源**: `iceberg_zjyprc_hadoop.newhome.dwm_newhome_event_aggregation_label_di`
**时长单位**: 毫秒转换为分钟（除以60000）

```sql
--内容中心总时长
SELECT
    date,
    sum(app_dura)/60000 dau_dura
FROM
    iceberg_zjyprc_hadoop.newhome.dwm_newhome_event_aggregation_label_di
WHERE
    date between 20260201 and 20260228
    and is_dau_2024=1
GROUP BY
    1
;
```

### 5. 内容中心有效用户DAU&总时长
**指标定义**: 内容中心有效用户的活跃度和时长分析
**数据源**: `iceberg_zjyprc_hadoop.newhome.dwm_newhome_event_aggregation_label_di`
**有效用户定义**: 有浏览或消费行为的用户
**计算指标**:
- 活跃UV
- 总有效时长（分钟）
- 人均有效时长（分钟）

```sql
--内容中心有效用户DAU&总时长
SELECT  date,
        count(distinct if(vv+expos_cnt>0,did,null)) active_uv, --活跃UV
        sum(if(vv+expos_cnt>0,list_page_dura+consum_dura,0)) valid_feed_dura, --总有效时长(分钟)
        sum(if(vv+expos_cnt>0,list_page_dura+consum_dura,0))/count(distinct if(vv+expos_cnt>0,did,null)) avg_valid_feed_dura --人均有效时长(分钟)
FROM
(
    SELECT  date, did,
            sum(consum_cnt) vv,
            sum(case when (item_position>=4 or ad_position > 4) then ad_expose_cnt + expos_cnt else null end) expos_cnt,
            sum(feed_dura)/60000 list_page_dura,
            sum(consum_dura)/60000 consum_dura
    FROM    iceberg_zjyprc_hadoop.newhome.dwm_newhome_event_aggregation_label_di
    WHERE   date=${date-1}
            and is_dau_2024 =1
            and is_top=0
            and coalesce(ad_expose_cnt, 0)+coalesce(expos_cnt, 0)+coalesce(consum_cnt, 0)+coalesce(feed_dura, 0)+coalesce(consum_dura, 0)+coalesce(click_cnt,0)>0
    GROUP BY date, did
)
GROUP BY date
;
```

### 6. 内容中心有效DAU7日留存
**指标定义**: 内容中心有效用户的7日留存率
**数据源**: `iceberg_zjyprc_hadoop.newhome.dwm_newhome_event_aggregation_label_di`
**有效用户定义**: 有消费或浏览行为的用户
**计算逻辑**: 使用CTE和自连接计算7日留存

```sql
--内容中心有效DAU7日留存
with vaild_dau as
(
    SELECT  date, did
    FROM
    (
        SELECT  date, did,
                sum(case when (item_position>=4 or ad_position > 4)  then ad_expose_cnt + expos_cnt else 0 end) as expos_cnt,
                sum(consum_cnt) as consum_cnt_v2
        FROM    iceberg_zjyprc_hadoop.newhome.dwm_newhome_event_aggregation_label_di
        WHERE   date between 20260201 and 20260308
                and is_dau_2024 = 1
                and is_top=0
        GROUP BY date, did
    )
    WHERE consum_cnt_v2>0 or expos_cnt>0
    GROUP BY date, did
)
SELECT  a.date,
        count(distinct a.did) as uv,
        count(distinct b.did) as uv_retent
FROM
(
    SELECT  date, did
    FROM    vaild_dau
) a
left join
(
    SELECT  date, did
    FROM    vaild_dau
) b
on a.did = b.did
   and datediff(from_unixtime(unix_timestamp(cast(b.date AS string),'yyyyMMdd'),'yyyy-MM-dd'), from_unixtime(unix_timestamp(cast(a.date AS string),'yyyyMMdd'),'yyyy-MM-dd'))=7
GROUP BY a.date
;
```

## 使用说明
1. 所有查询中的 `${date-1}` 表示前一天的日期
2. 时长相关指标需要除以60000转换为分钟
3. 用户去重使用 `did` 字段
4. 有效用户判断需要考虑多个条件组合

## 注意事项
- 查询结果需要按日期分组
- 注意数据过滤条件，确保数据准确性
- 留存计算需要处理日期格式转换
- 有效用户判断需要考虑浏览和消费行为