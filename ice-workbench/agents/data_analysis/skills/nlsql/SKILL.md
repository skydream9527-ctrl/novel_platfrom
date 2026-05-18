---
name: nlsql
description: 通过 NL-SQL 三要素模型将自然语言转换为 SQL 查询语句
triggers:
  - "SQL"
  - "查询"
  - "sql"
  - "数据"
  - "指标"
  - "DAU"
  - "留存"
  - "转化"
allowed_tools:
  - generate_sql_via_nlsql
  - save_sql_file
  - execute_query
constraints:
  - 禁止直接手写 SQL，必须先通过 generate_sql_via_nlsql 获取参考文件
  - 日期格式必须为 YYYYMMDD
  - 表名必须使用三段式前缀
  - 必须包含分区过滤条件
priority: 10
---

NL-SQL 是将自然语言转换为 SQL 的核心能力。

工作流程：
1. 确定业务线和数据类型
2. 调用 generate_sql_via_nlsql 获取该业务线的参考文件
3. 根据参考文件中的表结构和字段信息生成 SQL
4. 执行自检清单后输出最终 SQL
