from __future__ import annotations

from enum import Enum

from .skill_engine import SkillDef


class RunMode(Enum):
    SIMPLE_CHAT = "simple_chat"
    TOOL_CALL = "tool_call"
    FALLBACK = "fallback"


class RouteDecider:
    def decide(
        self,
        matched_skills: list[SkillDef],
        has_tools: bool,
        message: str,
    ) -> RunMode:
        if matched_skills and has_tools:
            return RunMode.TOOL_CALL

        if has_tools and self._looks_like_tool_request(message):
            return RunMode.TOOL_CALL

        return RunMode.SIMPLE_CHAT

    def _looks_like_tool_request(self, message: str) -> bool:
        action_keywords = [
            "查询", "查一下", "帮我查", "执行", "生成", "创建",
            "分析", "对比", "搜索", "发布", "导出", "画图",
            "query", "search", "create", "generate", "analyze",
        ]
        msg_lower = message.lower()
        return any(kw in msg_lower for kw in action_keywords)
