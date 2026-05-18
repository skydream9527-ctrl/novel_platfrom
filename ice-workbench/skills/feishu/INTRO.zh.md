# 飞书全套资源管控

通过 `feishu` CLI 操作飞书的文档、知识库、云盘、多维表格、表格、权限、日历、任务待办。

**触发场景**：消息里出现 `*.feishu.cn` 链接；提到飞书文档/知识库/云盘/多维表格/日历/任务；要求读取、创建、修改飞书资源。
**主要功能**：`feishu fetch <url>` 一键抓取任意资源、`feishu search` 搜文档、`feishu docx create` 创建文档；模块包含 docx/wiki/drive/bitable/sheet/perm/calendar/task。
**注意**：飞书链接只能用本技能读，禁止 WebFetch（无鉴权）。
