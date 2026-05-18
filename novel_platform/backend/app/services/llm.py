import json
from collections.abc import AsyncGenerator

import httpx

from ..core.config import settings


async def chat_stream(messages: list[dict], model: str | None = None) -> AsyncGenerator[str, None]:
    """Stream chat completion via OpenAI-compatible API (text only)."""
    if not settings.llm_enabled:
        yield "AI 功能未配置，请在 .env 中设置 LLM_API_KEY。"
        return

    model = model or settings.llm_model
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
      {"type": "reasoning", "content": "..."}  — reasoning content (thinking mode)
    """
    if not settings.llm_enabled:
        yield {"type": "text", "content": "AI 功能未配置，请在 .env 中设置 LLM_API_KEY。"}
        return

    model = model or settings.llm_model
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

    # Accumulate tool calls from streaming deltas
    tool_calls: dict[int, dict] = {}  # index -> {id, name, arguments_buf}
    reasoning_content_buf = ""

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

                    # Reasoning content (thinking mode)
                    reasoning = delta.get("reasoning_content", "")
                    if reasoning:
                        reasoning_content_buf += reasoning
                        yield {"type": "reasoning", "content": reasoning}

                    # Text content
                    content = delta.get("content", "")
                    if content:
                        yield {"type": "text", "content": content}

                    # Tool calls (streamed as deltas)
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

    # Yield complete tool calls
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
            "reasoning_content": reasoning_content_buf if reasoning_content_buf else None,
        }
