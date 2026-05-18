# Kyuubi SQL 网关

通过 `kyuubi-cli` 在小米内部 Iceberg/Spark/Presto 数据湖跑 SQL。

**触发场景**：用户说"查一下"、"帮我查"、"执行 SQL"、"跑查询"、"kyuubi"。
**主要功能**：执行 SELECT 查询、UPDATE / DELETE 操作；查看表元数据；workspace 验证；底层等价于 `kyuubi sql query/update/delete`。
**注意**：连接上下文（region / workspace / catalog / engine）已在服务端预置；本平台直接使用 `kyuubi_query` 工具更便捷，无需手写 CLI 命令。
