from __future__ import annotations

from fastapi import APIRouter, Depends

from ...core.deps import get_current_user
from ...core.errors import APIError, ErrorCode, ok
from ...core.storage import get_paths

router = APIRouter()

DEFAULT_GUIDE = """# ICE Data Workbench 使用指南

> 最后更新: 2026-05-07

## 快速开始

1. 在 **Dashboard** 选择一个范式范例（经营 / AB / 数据 / 波动 / 灰度）
2. 进入 **Workspace** 与 Agent 对话
3. 上传文件后通过 `@filename` 引用到对话中

## 五种工作范式

### 经营分析（biz）
经营数据拆解归因与趋势洞察

### AB 实验（ab）
分流验证 + 显著性结论 + 报告

### 数据分析（data）
NL→SQL → 可视化 → 导出

### 波动分析（wave）
多维下钻 + 根因 + 影响评估

### 版本灰度（gray）
灰度版本对比 + 放量决策建议

## 文件管理

- 单文件 ≤ 50MB
- 支持类型：md / txt / csv / json / sql / py / png / pdf
- 公共文件：仅 admin 可上传/编辑

## 协作

- 任意任务 → `🔗 分享` → 通过邮箱/姓名/工号搜索协作者
- 创建者保留所有权，协作者可读写

## 常见问题

**Q: 飞书登录失败？**
A: 联系 @gongyunhe 配置白名单。

**Q: LLM 报错 LLM_KEY_MISSING？**
A: `.env` 缺少 ANTHROPIC_API_KEY，重启后端生效。
"""


@router.get("/guide")
async def get_guide(_: dict = Depends(get_current_user)):
    paths = get_paths()
    p = paths.files / "使用指南.md"
    if p.exists():
        try:
            return ok({"content": p.read_text(encoding="utf-8"), "path": str(p.relative_to(paths.root))})
        except OSError as e:
            raise APIError(500, ErrorCode.INTERNAL_ERROR, str(e))
    return ok({"content": DEFAULT_GUIDE, "path": None})
