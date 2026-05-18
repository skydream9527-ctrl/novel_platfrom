---
name: data_query
description: 执行数据查询、保存结果、生成可视化图表
triggers:
  - "查数据"
  - "图表"
  - "可视化"
  - "趋势图"
  - "导出"
  - "CSV"
allowed_tools:
  - execute_query
  - save_csv
  - generate_chart
constraints:
  - 图表类型根据数据特征自动选择
  - 时序数据优先使用折线图
  - 分类对比优先使用柱状图
  - 占比数据使用饼图
priority: 5
---

数据查询与可视化能力，负责执行 SQL、保存结果和生成图表。

图表选择规则：
- 时间序列 → 折线图 (line)
- 分类对比 → 柱状图 (bar)
- 占比分布 → 饼图 (pie)
- 多维对比 → 堆叠柱状图 (stacked_bar)
