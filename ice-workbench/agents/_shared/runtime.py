from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, AsyncGenerator

from .llm_client import LLMClient
from .memory import SessionStore
from .prompt_builder import PromptBuilder
from .route_decider import RouteDecider, RunMode
from .skill_engine import SkillEngine
from .tool_registry import ToolRegistry, ToolDef
from .trace import TraceCollector, TraceRecord

logger = logging.getLogger(__name__)

MAX_TOOL_ROUNDS = 8


@dataclass
class AgentDefinition:
    name: str
    prompt_dir: Path
    skills_dir: Path
    tools: list[ToolDef] = field(default_factory=list)
    config: dict[str, Any] = field(default_factory=dict)


class RuntimeFacade:
    def __init__(
        self,
        agent: AgentDefinition,
        llm_client: LLMClient | None = None,
        session_store: SessionStore | None = None,
        trace_dir: Path | None = None,
    ):
        self.agent = agent
        self.llm = llm_client or LLMClient()
        self.session_store = session_store or SessionStore()
        self.tool_registry = ToolRegistry()
        self.skill_engine = SkillEngine()
        self.prompt_builder = PromptBuilder(agent.prompt_dir)
        self.route_decider = RouteDecider()
        self.trace_collector = TraceCollector(log_dir=trace_dir)

        self.tool_registry.register_many(agent.tools)
        self.skill_engine.scan_directory(agent.skills_dir)

    async def handle_message(
        self,
        message: str,
        session_id: str,
        model: str | None = None,
    ) -> AsyncGenerator[dict, None]:
        model = model or self.llm.default_model
        trace = self.trace_collector.new_trace(model=model)

        try:
            # Step 1: Match skills
            matched_skills = self.skill_engine.match(message)
            trace.matched_skills = [s.name for s in matched_skills]

            # Step 2: Determine tool allowlist
            skill_tools = self.skill_engine.get_allowed_tools(matched_skills)
            has_tools = bool(self.tool_registry.list_names())
            tool_names = skill_tools if skill_tools else self.tool_registry.list_names()

            # Step 3: Route decision
            run_mode = self.route_decider.decide(matched_skills, has_tools, message)
            trace.run_mode = run_mode.value

            # Step 4: Build prompt
            memory_summary = self.session_store.get_recent_memory(session_id)
            skill_context = self.skill_engine.build_skill_context(matched_skills)
            skills_snapshot = self.skill_engine.skills_snapshot()

            system_prompt = self.prompt_builder.build(
                memory_summary=memory_summary,
                skills_snapshot=skills_snapshot,
                skill_context=skill_context,
                tool_names=tool_names if run_mode == RunMode.TOOL_CALL else None,
            )

            # Step 5: Build messages
            history = self.session_store.get_messages(session_id)
            messages = [{"role": "system", "content": system_prompt}]
            messages.extend(history)
            messages.append({"role": "user", "content": message})

            # Step 6: Execute
            if run_mode == RunMode.TOOL_CALL:
                async for event in self._tool_call_loop(messages, tool_names, model, trace):
                    yield event
            else:
                async for event in self._simple_chat(messages, model, trace):
                    yield event

            # Step 7: Store message
            self.session_store.add_message(session_id, "user", message)
            # Assistant content is accumulated in the loop above

        except Exception as e:
            trace.error = str(e)
            yield {"type": "error", "message": str(e)}
        finally:
            self.trace_collector.finalize(trace)
            yield {"type": "done", "trace": trace.to_dict()}

    async def _simple_chat(
        self,
        messages: list[dict],
        model: str,
        trace: TraceRecord,
    ) -> AsyncGenerator[dict, None]:
        full_text = ""
        async for event in self.llm.stream_chat(messages=messages, model=model):
            if event["type"] == "content":
                full_text += event["text"]
                yield event
        # Store assistant response in trace
        if full_text:
            trace.tool_results.append({"final_response_length": len(full_text)})

    async def _tool_call_loop(
        self,
        messages: list[dict],
        tool_names: list[str],
        model: str,
        trace: TraceRecord,
    ) -> AsyncGenerator[dict, None]:
        tools_schema = self.tool_registry.filter_by_names(tool_names) or self.tool_registry.list_schemas()

        for _round in range(MAX_TOOL_ROUNDS):
            tool_calls_this_round: list[dict] = []
            content_text = ""

            async for event in self.llm.stream_chat(
                messages=messages, model=model, tools=tools_schema
            ):
                if event["type"] == "content":
                    content_text += event["text"]
                    yield event
                elif event["type"] == "tool_calls":
                    tool_calls_this_round = event["calls"]

            if not tool_calls_this_round:
                break

            # Build assistant message with tool_calls
            openai_tool_calls = [
                {
                    "id": tc["id"],
                    "type": "function",
                    "function": {
                        "name": tc["name"],
                        "arguments": json.dumps(tc["arguments"], ensure_ascii=False),
                    },
                }
                for tc in tool_calls_this_round
            ]
            messages.append({"role": "assistant", "content": content_text or None, "tool_calls": openai_tool_calls})

            # Execute tools
            for tc in tool_calls_this_round:
                trace.used_tools.append(tc["name"])
                yield {"type": "tool_call", "name": tc["name"], "args": tc["arguments"]}

                result = await self.tool_registry.execute(tc["name"], tc["arguments"])
                result_str = json.dumps(result, ensure_ascii=False, default=str)

                trace.tool_results.append({
                    "tool": tc["name"],
                    "success": result.get("success", False),
                })

                yield {"type": "tool_result", "name": tc["name"], "result": result}

                messages.append({
                    "role": "tool",
                    "tool_call_id": tc["id"],
                    "content": result_str,
                })
