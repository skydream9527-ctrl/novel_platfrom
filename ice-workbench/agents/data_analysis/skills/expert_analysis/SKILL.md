---
name: expert_analysis
description: 多专家辩论分析：SQL工程师、数据分析师、业务顾问三方独立分析后交叉辩论
triggers:
  - "深度分析"
  - "专家分析"
  - "辩论"
  - "归因"
  - "异常"
  - "下钻"
  - "预测"
allowed_tools:
  - anomaly_detect
  - event_correlate
  - trend_forecast
  - period_compare
  - auto_drilldown
  - publish_to_feishu
constraints:
  - 辩论最多进行 3 轮
  - 仲裁者判断收敛后停止
  - 最终报告必须包含共识结论和分歧说明
priority: 8
---

多专家辩论分析系统：

1. Round 1: SQL工程师、数据分析师、业务顾问各自独立分析
2. Round 2: 交叉质疑（每位专家对其他两位的分析提出问题）
3. Round 3: 回应与修正
4. 仲裁裁决：判断是否收敛，输出共识/分歧/最终建议

补充分析工具可在辩论前自动执行：
- period_compare: 环比/同比
- auto_drilldown: 维度下钻
- anomaly_detect: 异常检测
- trend_forecast: 趋势预测
- event_correlate: 事件关联
