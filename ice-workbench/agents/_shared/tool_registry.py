from __future__ import annotations

import asyncio
import json
import logging
from dataclasses import dataclass, field
from typing import Any, Callable, Awaitable, Union

logger = logging.getLogger(__name__)

ToolHandler = Callable[[dict[str, Any]], Union[str, dict, Awaitable[Union[str, dict]]]]


@dataclass
class ToolDef:
    name: str
    description: str
    parameters: dict
    handler: ToolHandler
    timeout_ms: int = 30000

    def to_schema(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters,
        }


class ToolRegistry:
    def __init__(self):
        self._tools: dict[str, ToolDef] = {}

    def register(self, tool: ToolDef) -> None:
        if tool.name in self._tools:
            logger.warning("Tool %s already registered, overwriting", tool.name)
        self._tools[tool.name] = tool

    def register_many(self, tools: list[ToolDef]) -> None:
        for tool in tools:
            self.register(tool)

    def get(self, name: str) -> ToolDef | None:
        return self._tools.get(name)

    def list_schemas(self) -> list[dict]:
        return [t.to_schema() for t in self._tools.values()]

    def list_names(self) -> list[str]:
        return list(self._tools.keys())

    async def execute(self, name: str, arguments: dict[str, Any]) -> dict:
        tool = self._tools.get(name)
        if not tool:
            return {"success": False, "error": f"Unknown tool: {name}"}

        try:
            result = tool.handler(arguments)
            if asyncio.iscoroutine(result):
                result = await asyncio.wait_for(
                    result, timeout=tool.timeout_ms / 1000
                )

            if isinstance(result, str):
                try:
                    return {"success": True, "result": json.loads(result)}
                except json.JSONDecodeError:
                    return {"success": True, "result": result}
            elif isinstance(result, dict):
                if "success" not in result:
                    return {"success": True, "result": result}
                return result
            else:
                return {"success": True, "result": str(result)}

        except asyncio.TimeoutError:
            logger.error("Tool %s timed out after %dms", name, tool.timeout_ms)
            return {"success": False, "error": f"Tool {name} timed out"}
        except Exception as e:
            logger.exception("Tool %s execution failed", name)
            return {"success": False, "error": str(e)}

    def filter_by_names(self, allowed: list[str]) -> list[dict]:
        return [
            self._tools[n].to_schema()
            for n in allowed
            if n in self._tools
        ]
