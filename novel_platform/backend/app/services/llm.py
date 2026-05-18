import json
from collections.abc import AsyncGenerator

import httpx

from ..core.config import settings


def _convert_messages_for_anthropic(messages: list[dict]) -> tuple[str, list[dict]]:
    """Convert OpenAI-style messages to Anthropic format.

    Returns (system_prompt, messages) where system is extracted separately.
    """
    system = ""
    anthropic_messages = []

    for msg in messages:
        if msg["role"] == "system":
            system = msg["content"]
        elif msg["role"] == "tool":
            # Tool results in Anthropic format
            anthropic_messages.append({
                "role": "user",
                "content": [{
                    "type": "tool_result",
                    "tool_use_id": msg["tool_call_id"],
                    "content": msg["content"],
                }],
            })
        elif msg["role"] == "assistant" and msg.get("tool_calls"):
            # Assistant message with tool calls
            content = []
            if msg.get("content"):
                content.append({"type": "text", "text": msg["content"]})
            for tc in msg["tool_calls"]:
                content.append({
                    "type": "tool_use",
                    "id": tc["id"],
                    "name": tc["function"]["name"],
                    "input": json.loads(tc["function"]["arguments"]) if isinstance(tc["function"]["arguments"], str) else tc["function"]["arguments"],
                })
            anthropic_messages.append({"role": "assistant", "content": content})
        else:
            anthropic_messages.append({
                "role": msg["role"],
                "content": msg["content"],
            })

    return system, anthropic_messages


def _convert_tools_for_anthropic(tools: list[dict]) -> list[dict]:
    """Convert OpenAI-style tools to Anthropic format."""
    anthropic_tools = []
    for tool in tools:
        func = tool.get("function", {})
        anthropic_tools.append({
            "name": func.get("name", ""),
            "description": func.get("description", ""),
            "input_schema": func.get("parameters", {}),
        })
    return anthropic_tools


async def chat_stream(messages: list[dict], model: str | None = None) -> AsyncGenerator[str, None]:
    """Stream chat completion via OpenAI-compatible API (text only)."""
    if not settings.llm_enabled:
        yield "AI 功能未配置，请在 .env 中设置 LLM_API_KEY。"
        return

    model = model or settings.llm_model

    if settings.llm_provider == "anthropic":
        async for chunk in _anthropic_stream(messages, model, tools=None):
            if chunk["type"] == "text":
                yield chunk["content"]
    else:
        async for chunk in _openai_stream(messages, model):
            yield chunk


async def chat_once(messages: list[dict], model: str | None = None) -> str:
    """Non-streaming chat completion."""
    chunks = []
    async for chunk in chat_stream(messages, model):
        chunks.append(chunk)
    return "".join(chunks)


async def chat_with_tools(
    messages: list[dict],
    tools: list[dict],
    model: str | None = None,
) -> AsyncGenerator[dict, None]:
    """Stream chat with function calling support.

    Yields dicts:
      {"type": "text", "content": "..."}       — text chunk
      {"type": "tool_call", "id": "...", "name": "...", "arguments": {...}}  — complete tool call
    """
    if not settings.llm_enabled:
        yield {"type": "text", "content": "AI 功能未配置，请在 .env 中设置 LLM_API_KEY。"}
        return

    model = model or settings.llm_model

    if settings.llm_provider == "anthropic":
        async for event in _anthropic_stream(messages, model, tools=tools):
            yield event
    else:
        async for event in _openai_stream_with_tools(messages, model, tools):
            yield event


async def _openai_stream(messages: list[dict], model: str) -> AsyncGenerator[str, None]:
    """OpenAI-compatible streaming."""
    headers = {
        "Authorization": f"Bearer {settings.llm_api_key}",
        "Content-Type": "application/json",
    }
    body = {
        "model": model,
        "messages": messages,
        "stream": True,
        "max_tokens": 4096,
    }

    async with httpx.AsyncClient(timeout=120.0) as client:
        async with client.stream(
            "POST",
            f"{settings.llm_base_url}/chat/completions",
            headers=headers,
            json=body,
        ) as resp:
            if resp.status_code != 200:
                error_body = ""
                async for chunk in resp.aiter_text():
                    error_body += chunk
                yield f"AI 调用失败 (HTTP {resp.status_code}): {error_body[:200]}"
                return

            async for line in resp.aiter_lines():
                if not line.startswith("data: "):
                    continue
                data = line[6:]
                if data.strip() == "[DONE]":
                    break
                try:
                    obj = json.loads(data)
                    delta = obj["choices"][0].get("delta", {})
                    content = delta.get("content", "")
                    if content:
                        yield content
                except (json.JSONDecodeError, KeyError, IndexError):
                    continue


async def _openai_stream_with_tools(
    messages: list[dict],
    model: str,
    tools: list[dict],
) -> AsyncGenerator[dict, None]:
    """OpenAI-compatible streaming with tools."""
    headers = {
        "Authorization": f"Bearer {settings.llm_api_key}",
        "Content-Type": "application/json",
    }
    body = {
        "model": model,
        "messages": messages,
        "tools": tools,
        "stream": True,
        "max_tokens": 4096,
    }

    tool_calls: dict[int, dict] = {}

    async with httpx.AsyncClient(timeout=120.0) as client:
        async with client.stream(
            "POST",
            f"{settings.llm_base_url}/chat/completions",
            headers=headers,
            json=body,
        ) as resp:
            if resp.status_code != 200:
                error_body = ""
                async for chunk in resp.aiter_text():
                    error_body += chunk
                yield {"type": "text", "content": f"AI 调用失败 (HTTP {resp.status_code}): {error_body[:200]}"}
                return

            async for line in resp.aiter_lines():
                if not line.startswith("data: "):
                    continue
                data = line[6:]
                if data.strip() == "[DONE]":
                    break
                try:
                    obj = json.loads(data)
                    choice = obj["choices"][0]
                    delta = choice.get("delta", {})

                    content = delta.get("content", "")
                    if content:
                        yield {"type": "text", "content": content}

                    for tc_delta in (delta.get("tool_calls") or []):
                        idx = tc_delta.get("index", 0)
                        if idx not in tool_calls:
                            tool_calls[idx] = {"id": "", "name": "", "arguments_buf": ""}
                        tc = tool_calls[idx]
                        if "id" in tc_delta:
                            tc["id"] = tc_delta["id"]
                        func = tc_delta.get("function", {})
                        if "name" in func:
                            tc["name"] = func["name"]
                        if "arguments" in func:
                            tc["arguments_buf"] += func["arguments"]

                except (json.JSONDecodeError, KeyError, IndexError):
                    continue

    for idx in sorted(tool_calls.keys()):
        tc = tool_calls[idx]
        try:
            args = json.loads(tc["arguments_buf"]) if tc["arguments_buf"] else {}
        except json.JSONDecodeError:
            args = {}
        yield {
            "type": "tool_call",
            "id": tc["id"],
            "name": tc["name"],
            "arguments": args,
        }


async def _anthropic_stream(
    messages: list[dict],
    model: str,
    tools: list[dict] | None = None,
) -> AsyncGenerator[dict, None]:
    """Anthropic streaming with optional tools."""
    system, anthropic_messages = _convert_messages_for_anthropic(messages)

    headers = {
        "x-api-key": settings.llm_api_key,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }

    body: dict = {
        "model": model,
        "messages": anthropic_messages,
        "max_tokens": 4096,
        "stream": True,
    }

    if system:
        body["system"] = system

    if tools:
        body["tools"] = _convert_tools_for_anthropic(tools)

    async with httpx.AsyncClient(timeout=120.0) as client:
        async with client.stream(
            "POST",
            f"{settings.llm_base_url}/messages",
            headers=headers,
            json=body,
        ) as resp:
            if resp.status_code != 200:
                error_body = ""
                async for chunk in resp.aiter_text():
                    error_body += chunk
                yield {"type": "text", "content": f"AI 调用失败 (HTTP {resp.status_code}): {error_body[:200]}"}
                return

            # Accumulate tool use blocks
            current_tool: dict | None = None
            tool_input_buf = ""

            async for line in resp.aiter_lines():
                if not line.startswith("data: "):
                    continue
                data = line[6:]
                try:
                    obj = json.loads(data)
                    event_type = obj.get("type", "")

                    if event_type == "content_block_start":
                        block = obj.get("content_block", {})
                        if block.get("type") == "tool_use":
                            current_tool = {
                                "id": block.get("id", ""),
                                "name": block.get("name", ""),
                            }
                            tool_input_buf = ""
                        elif block.get("type") == "text":
                            pass  # Text will come in deltas

                    elif event_type == "content_block_delta":
                        delta = obj.get("delta", {})
                        if delta.get("type") == "text_delta":
                            text = delta.get("text", "")
                            if text:
                                yield {"type": "text", "content": text}
                        elif delta.get("type") == "input_json_delta":
                            tool_input_buf += delta.get("partial_json", "")

                    elif event_type == "content_block_stop":
                        if current_tool:
                            try:
                                args = json.loads(tool_input_buf) if tool_input_buf else {}
                            except json.JSONDecodeError:
                                args = {}
                            yield {
                                "type": "tool_call",
                                "id": current_tool["id"],
                                "name": current_tool["name"],
                                "arguments": args,
                            }
                            current_tool = None
                            tool_input_buf = ""

                    elif event_type == "message_stop":
                        break

                except (json.JSONDecodeError, KeyError):
                    continue
