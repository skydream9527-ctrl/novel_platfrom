"""Unified LLM gateway. Routes by model-id prefix to provider-specific
endpoints exposed by the mify gateway:

- ppio/pa/claude-*   → Anthropic native protocol  at /anthropic/v1/messages
- azure_openai/*     → OpenAI Responses API       at /v1/responses
- vertex_ai/*        → OpenAI Chat-Completions    at /v1/chat/completions  (best-effort)
- xiaomi/*           → OpenAI Chat-Completions    at /v1/chat/completions  (best-effort)
- (default no slash) → Anthropic legacy via ANTHROPIC_API_KEY

Internal event protocol (consumer in api/v1/ws.py and scheduler_svc):
- {"type": "text", "delta": "..."}                — token chunk
- {"type": "tool_use_delta", "index": int, "id"?, "name"?, "args_chunk": str}
- {"type": "message_done", "stop_reason": ..., "content": [...], "usage": {...}}
"""
from __future__ import annotations

import asyncio
import json
import logging
from typing import Any, AsyncIterator

from ..core.config import get_settings
from ..core.errors import APIError, ErrorCode

log = logging.getLogger("llm_gateway")

MAX_TOOL_ROUNDS = 5
TOOL_TIMEOUT_SEC = 30


def assert_configured() -> None:
    s = get_settings()
    if not s.llm_enabled:
        raise APIError(503, ErrorCode.LLM_KEY_MISSING, "LLM 未配置")


def resolve_model(requested: str | None) -> str:
    s = get_settings()
    if requested:
        return requested
    if s.gateway_enabled:
        return s.MIFY_DEFAULT_MODEL
    return s.ANTHROPIC_MODEL


def _route(model: str) -> str:
    """Return one of: anthropic_native | openai_responses | openai_chat | legacy_anthropic."""
    s = get_settings()
    if model.startswith("ppio/pa/claude-") or model.startswith("ppio/pa/"):
        return "anthropic_native"
    if model.startswith("azure_openai/"):
        return "openai_responses"
    if "/" in model and s.gateway_enabled:
        return "openai_chat"
    return "legacy_anthropic"


# ============================================================
# Anthropic native (claude on mify) — preferred path for Claude
# ============================================================


def _mify_anthropic_client():
    from anthropic import AsyncAnthropic

    s = get_settings()
    base = (s.MIFY_GATEWAY_BASE_URL or "").rstrip("/")
    if base.endswith("/v1"):
        base = base[:-3]  # strip /v1
    base = (base or "http://model.mify.ai.srv") + "/anthropic"
    return AsyncAnthropic(api_key=s.MIFY_GATEWAY_API_KEY, base_url=base, timeout=120.0)


def _legacy_anthropic_client():
    from anthropic import AsyncAnthropic

    s = get_settings()
    kwargs: dict[str, Any] = {"api_key": s.ANTHROPIC_API_KEY, "timeout": 120.0}
    if s.ANTHROPIC_BASE_URL:
        kwargs["base_url"] = s.ANTHROPIC_BASE_URL
    return AsyncAnthropic(**kwargs)


async def _stream_anthropic(
    *,
    client,
    system_prompt: str,
    messages: list[dict],
    tools: list[dict] | None,
    model: str,
) -> AsyncIterator[dict]:
    async with client.messages.stream(
        model=model,
        max_tokens=4096,
        system=system_prompt,
        messages=messages,
        tools=tools or None,
    ) as stream:
        async for event in stream:
            etype = getattr(event, "type", None)
            if etype == "content_block_delta":
                d = getattr(event, "delta", None)
                if d and getattr(d, "type", None) == "text_delta":
                    yield {"type": "text", "delta": d.text}
                elif d and getattr(d, "type", None) == "input_json_delta":
                    # tool_use input streamed as JSON deltas
                    idx = getattr(event, "index", 0)
                    yield {
                        "type": "tool_use_delta",
                        "index": idx,
                        "args_chunk": d.partial_json,
                    }
            elif etype == "content_block_start":
                block = getattr(event, "content_block", None)
                if block and getattr(block, "type", None) == "tool_use":
                    yield {
                        "type": "tool_use_delta",
                        "index": getattr(event, "index", 0),
                        "id": block.id,
                        "name": block.name,
                        "args_chunk": "",
                    }
            elif etype == "message_stop":
                final = await stream.get_final_message()
                yield {
                    "type": "message_done",
                    "stop_reason": final.stop_reason,
                    # exclude_none drops bedrock-extension `caller: null` that
                    # the upstream re-rejects on the next round (round 2+ of D38).
                    "content": [b.model_dump(exclude_none=True) for b in final.content],
                    "usage": (
                        {
                            "input_tokens": final.usage.input_tokens,
                            "output_tokens": final.usage.output_tokens,
                        }
                        if final.usage
                        else None
                    ),
                }


# ============================================================
# OpenAI-compat: Chat Completions (vertex_ai / xiaomi best-effort)
# ============================================================


def _openai_chat_client():
    from openai import AsyncOpenAI

    s = get_settings()
    return AsyncOpenAI(
        api_key=s.MIFY_GATEWAY_API_KEY,
        base_url=s.MIFY_GATEWAY_BASE_URL.rstrip("/"),
        timeout=120.0,
        max_retries=2,
    )


def _anthropic_tools_to_openai(tools: list[dict] | None) -> list[dict] | None:
    if not tools:
        return None
    out: list[dict] = []
    for t in tools:
        if "function" in t and "type" in t:
            out.append(t)
            continue
        out.append(
            {
                "type": "function",
                "function": {
                    "name": t["name"],
                    "description": t.get("description", ""),
                    "parameters": t.get("input_schema") or {"type": "object", "properties": {}},
                },
            }
        )
    return out


def _messages_to_openai(messages: list[dict], system_prompt: str) -> list[dict]:
    """Convert internal Anthropic-shaped messages to OpenAI chat format."""
    out: list[dict] = [{"role": "system", "content": system_prompt}]
    for m in messages:
        role = m.get("role")
        content = m.get("content")
        if isinstance(content, str):
            out.append({"role": role, "content": content})
            continue
        if not isinstance(content, list):
            out.append({"role": role, "content": str(content) if content is not None else ""})
            continue
        if role == "assistant":
            text_parts: list[str] = []
            tool_calls: list[dict] = []
            for block in content:
                btype = block.get("type")
                if btype == "text":
                    text_parts.append(block.get("text", ""))
                elif btype == "tool_use":
                    tool_calls.append(
                        {
                            "id": block.get("id", ""),
                            "type": "function",
                            "function": {
                                "name": block.get("name", ""),
                                "arguments": json.dumps(block.get("input") or {}, ensure_ascii=False),
                            },
                        }
                    )
            entry: dict = {"role": "assistant", "content": "".join(text_parts) or None}
            if tool_calls:
                entry["tool_calls"] = tool_calls
            out.append(entry)
            continue
        if role == "user":
            text_parts2: list[str] = []
            for block in content:
                btype = block.get("type")
                if btype == "tool_result":
                    raw = block.get("content")
                    body = raw if isinstance(raw, str) else json.dumps(raw, ensure_ascii=False)
                    out.append(
                        {
                            "role": "tool",
                            "tool_call_id": block.get("tool_use_id", ""),
                            "content": body,
                        }
                    )
                elif btype == "text":
                    text_parts2.append(block.get("text", ""))
            if text_parts2:
                out.append({"role": role, "content": "".join(text_parts2)})
            continue
        out.append({"role": role, "content": json.dumps(content, ensure_ascii=False)})
    return out


def _normalize_stop_reason(openai_reason: str | None) -> str | None:
    if openai_reason == "tool_calls":
        return "tool_use"
    if openai_reason == "stop":
        return "end_turn"
    return openai_reason


async def _stream_openai_chat(
    *,
    system_prompt: str,
    messages: list[dict],
    tools: list[dict] | None,
    model: str,
) -> AsyncIterator[dict]:
    client = _openai_chat_client()
    api_messages = _messages_to_openai(messages, system_prompt)
    api_tools = _anthropic_tools_to_openai(tools)
    tool_buf: dict[int, dict] = {}
    text_buf: list[str] = []
    finish_reason: str | None = None
    usage: dict | None = None
    kwargs: dict[str, Any] = {
        "model": model,
        "messages": api_messages,
        "stream": True,
        "stream_options": {"include_usage": True},
    }
    if api_tools:
        kwargs["tools"] = api_tools
    stream = await client.chat.completions.create(**kwargs)
    async for chunk in stream:
        if not chunk.choices:
            if getattr(chunk, "usage", None):
                u = chunk.usage
                usage = {
                    "input_tokens": getattr(u, "prompt_tokens", 0) or 0,
                    "output_tokens": getattr(u, "completion_tokens", 0) or 0,
                }
            continue
        choice = chunk.choices[0]
        delta = choice.delta
        if delta and getattr(delta, "content", None):
            text_buf.append(delta.content)
            yield {"type": "text", "delta": delta.content}
        if delta and getattr(delta, "tool_calls", None):
            for tc in delta.tool_calls:
                idx = tc.index
                slot = tool_buf.setdefault(idx, {"id": "", "name": "", "args": ""})
                if tc.id:
                    slot["id"] = tc.id
                if tc.function:
                    if tc.function.name:
                        slot["name"] = tc.function.name
                    if tc.function.arguments:
                        slot["args"] += tc.function.arguments
                yield {
                    "type": "tool_use_delta",
                    "index": idx,
                    "id": slot["id"] or None,
                    "name": slot["name"] or None,
                    "args_chunk": (tc.function.arguments if tc.function and tc.function.arguments else ""),
                }
        if choice.finish_reason:
            finish_reason = choice.finish_reason
    final_content: list[dict] = []
    if text_buf:
        final_content.append({"type": "text", "text": "".join(text_buf)})
    for idx in sorted(tool_buf.keys()):
        slot = tool_buf[idx]
        try:
            parsed = json.loads(slot["args"]) if slot["args"] else {}
        except json.JSONDecodeError:
            parsed = {"_raw": slot["args"]}
        final_content.append(
            {
                "type": "tool_use",
                "id": slot["id"] or f"call_{idx}",
                "name": slot["name"],
                "input": parsed,
            }
        )
    yield {
        "type": "message_done",
        "stop_reason": _normalize_stop_reason(finish_reason),
        "content": final_content,
        "usage": usage,
    }


# ============================================================
# OpenAI Responses API (azure_openai/* on mify)
# ============================================================


import httpx


async def _stream_openai_responses(
    *,
    system_prompt: str,
    messages: list[dict],
    tools: list[dict] | None,
    model: str,
) -> AsyncIterator[dict]:
    """Call /v1/responses streaming. Convert events to internal protocol.

    The Responses API uses Server-Sent Events. Events of interest:
    - response.output_text.delta : {"delta": "..."}
    - response.completed         : final, with usage + output items
    - response.function_call.arguments.delta : tool args delta
    """
    s = get_settings()
    base = s.MIFY_GATEWAY_BASE_URL.rstrip("/")
    url = f"{base}/responses"
    api_messages = _messages_to_openai(messages, system_prompt)
    # Responses API: use `input` (string or array) and `instructions` (system)
    payload: dict[str, Any] = {
        "model": model,
        "input": [
            {"role": m["role"], "content": m["content"]}
            for m in api_messages
            if m["role"] != "system"
        ],
        "instructions": system_prompt,
        "stream": True,
        "max_output_tokens": 4096,
    }
    if tools:
        payload["tools"] = [
            {
                "type": "function",
                "name": t["name"],
                "description": t.get("description", ""),
                "parameters": t.get("input_schema") or {"type": "object", "properties": {}},
            }
            for t in tools
        ]
    headers = {
        "Authorization": f"Bearer {s.MIFY_GATEWAY_API_KEY}",
        "Content-Type": "application/json",
        "Accept": "text/event-stream",
    }
    text_buf: list[str] = []
    tool_buf: dict[int, dict] = {}
    finish_reason: str | None = None
    usage: dict | None = None
    final_content: list[dict] = []
    async with httpx.AsyncClient(timeout=120.0) as cli:
        async with cli.stream("POST", url, headers=headers, json=payload) as resp:
            if resp.status_code != 200:
                body = await resp.aread()
                raise APIError(502, "GATEWAY_ERROR", f"responses API {resp.status_code}: {body.decode(errors='replace')[:300]}")
            current_event: str | None = None
            async for line in resp.aiter_lines():
                if not line:
                    continue
                if line.startswith("event:"):
                    current_event = line[6:].strip()
                    continue
                if not line.startswith("data:"):
                    continue
                data_str = line[5:].strip()
                if data_str == "[DONE]":
                    break
                try:
                    data = json.loads(data_str)
                except json.JSONDecodeError:
                    continue
                etype = data.get("type") or current_event or ""
                if etype == "response.output_text.delta":
                    delta = data.get("delta") or ""
                    if delta:
                        text_buf.append(delta)
                        yield {"type": "text", "delta": delta}
                elif etype == "response.function_call.arguments.delta":
                    idx = int(data.get("output_index") or 0)
                    slot = tool_buf.setdefault(idx, {"id": "", "name": "", "args": ""})
                    delta = data.get("delta") or ""
                    slot["args"] += delta
                    yield {
                        "type": "tool_use_delta",
                        "index": idx,
                        "id": slot["id"] or None,
                        "name": slot["name"] or None,
                        "args_chunk": delta,
                    }
                elif etype == "response.output_item.added":
                    item = data.get("item") or {}
                    if item.get("type") == "function_call":
                        idx = int(data.get("output_index") or 0)
                        slot = tool_buf.setdefault(idx, {"id": "", "name": "", "args": ""})
                        slot["id"] = item.get("call_id") or item.get("id") or ""
                        slot["name"] = item.get("name") or ""
                        yield {
                            "type": "tool_use_delta",
                            "index": idx,
                            "id": slot["id"],
                            "name": slot["name"],
                            "args_chunk": "",
                        }
                elif etype == "response.completed":
                    response = data.get("response") or {}
                    u = response.get("usage") or {}
                    if u:
                        usage = {
                            "input_tokens": int(u.get("input_tokens") or 0),
                            "output_tokens": int(u.get("output_tokens") or 0),
                        }
                    finish_reason = response.get("status") or "completed"
    if text_buf:
        final_content.append({"type": "text", "text": "".join(text_buf)})
    for idx in sorted(tool_buf.keys()):
        slot = tool_buf[idx]
        try:
            parsed = json.loads(slot["args"]) if slot["args"] else {}
        except json.JSONDecodeError:
            parsed = {"_raw": slot["args"]}
        final_content.append(
            {
                "type": "tool_use",
                "id": slot["id"] or f"call_{idx}",
                "name": slot["name"],
                "input": parsed,
            }
        )
    yield {
        "type": "message_done",
        "stop_reason": "tool_use" if any(c.get("type") == "tool_use" for c in final_content) else "end_turn",
        "content": final_content,
        "usage": usage,
    }


# ============================================================
# Public façade
# ============================================================


async def stream_chat(
    *,
    system_prompt: str,
    messages: list[dict],
    tools: list[dict] | None = None,
    model: str | None = None,
) -> AsyncIterator[dict]:
    assert_configured()
    chosen = resolve_model(model)
    route = _route(chosen)
    log.info("stream_chat route=%s model=%s", route, chosen)
    if route == "anthropic_native":
        async for ev in _stream_anthropic(
            client=_mify_anthropic_client(),
            system_prompt=system_prompt,
            messages=messages,
            tools=tools,
            model=chosen,
        ):
            yield ev
    elif route == "openai_responses":
        async for ev in _stream_openai_responses(
            system_prompt=system_prompt, messages=messages, tools=tools, model=chosen
        ):
            yield ev
    elif route == "openai_chat":
        async for ev in _stream_openai_chat(
            system_prompt=system_prompt, messages=messages, tools=tools, model=chosen
        ):
            yield ev
    else:  # legacy_anthropic
        s = get_settings()
        if not s.ANTHROPIC_API_KEY:
            raise APIError(503, ErrorCode.LLM_KEY_MISSING, "LLM 未配置")
        bare = chosen.rsplit("/", 1)[-1] if "/" in chosen else chosen
        async for ev in _stream_anthropic(
            client=_legacy_anthropic_client(),
            system_prompt=system_prompt,
            messages=messages,
            tools=tools,
            model=bare,
        ):
            yield ev


async def complete_once(
    *,
    system_prompt: str,
    messages: list[dict],
    model: str | None = None,
    max_tokens: int = 2048,
) -> dict:
    """Non-streaming single completion. Routes the same way."""
    assert_configured()
    chosen = resolve_model(model)
    route = _route(chosen)
    if route == "anthropic_native":
        client = _mify_anthropic_client()
        resp = await client.messages.create(
            model=chosen, max_tokens=max_tokens, system=system_prompt, messages=messages
        )
        text = "".join(b.text for b in resp.content if getattr(b, "type", None) == "text")
        return {
            "text": text,
            "usage": (
                {"input_tokens": resp.usage.input_tokens, "output_tokens": resp.usage.output_tokens}
                if resp.usage
                else None
            ),
            "model": chosen,
        }
    if route == "openai_responses":
        s = get_settings()
        url = f"{s.MIFY_GATEWAY_BASE_URL.rstrip('/')}/responses"
        api_messages = _messages_to_openai(messages, system_prompt)
        payload: dict[str, Any] = {
            "model": chosen,
            "input": [
                {"role": m["role"], "content": m["content"]}
                for m in api_messages
                if m["role"] != "system"
            ],
            "instructions": system_prompt,
            "max_output_tokens": max_tokens,
        }
        async with httpx.AsyncClient(timeout=120.0) as cli:
            r = await cli.post(
                url,
                headers={"Authorization": f"Bearer {s.MIFY_GATEWAY_API_KEY}"},
                json=payload,
            )
            if r.status_code != 200:
                raise APIError(502, "GATEWAY_ERROR", f"responses API {r.status_code}: {r.text[:300]}")
            data = r.json()
        text_parts: list[str] = []
        for item in data.get("output") or []:
            for c in item.get("content") or []:
                if c.get("type") == "output_text":
                    text_parts.append(c.get("text") or "")
        u = data.get("usage") or {}
        return {
            "text": "".join(text_parts),
            "usage": (
                {
                    "input_tokens": int(u.get("input_tokens") or 0),
                    "output_tokens": int(u.get("output_tokens") or 0),
                }
                if u
                else None
            ),
            "model": data.get("model") or chosen,
        }
    if route == "openai_chat":
        client = _openai_chat_client()
        resp = await client.chat.completions.create(
            model=chosen,
            messages=_messages_to_openai(messages, system_prompt),
            max_tokens=max_tokens,
        )
        choice = resp.choices[0] if resp.choices else None
        text = (choice.message.content if choice and choice.message else "") or ""
        return {
            "text": text,
            "usage": (
                {
                    "input_tokens": getattr(resp.usage, "prompt_tokens", 0) or 0,
                    "output_tokens": getattr(resp.usage, "completion_tokens", 0) or 0,
                }
                if resp.usage
                else None
            ),
            "model": resp.model or chosen,
        }
    # legacy
    s = get_settings()
    if not s.ANTHROPIC_API_KEY:
        raise APIError(503, ErrorCode.LLM_KEY_MISSING, "LLM 未配置")
    bare = chosen.rsplit("/", 1)[-1] if "/" in chosen else chosen
    client = _legacy_anthropic_client()
    resp = await client.messages.create(
        model=bare, max_tokens=max_tokens, system=system_prompt, messages=messages
    )
    text = "".join(b.text for b in resp.content if getattr(b, "type", None) == "text")
    return {
        "text": text,
        "usage": (
            {"input_tokens": resp.usage.input_tokens, "output_tokens": resp.usage.output_tokens}
            if resp.usage
            else None
        ),
        "model": bare,
    }


async def run_tool_with_timeout(coro_factory, *, timeout: int = TOOL_TIMEOUT_SEC) -> dict:
    try:
        result = await asyncio.wait_for(coro_factory(), timeout=timeout)
        return {"success": True, "result": result, "status": "done"}
    except asyncio.TimeoutError:
        return {
            "success": False,
            "error": {"code": ErrorCode.TOOL_TIMEOUT, "message": "tool execution timeout"},
            "status": "timeout",
        }
    except Exception as e:
        return {
            "success": False,
            "error": {"code": "TOOL_ERROR", "message": str(e)},
            "status": "error",
        }


# Now that we know the gateway expects owner/* prefixes, restore them in PRESETS.
PRESET_MODELS = [
    {"id": "ppio/pa/claude-opus-4-7", "label": "Claude Opus 4.7", "input_unit_price": 15.0, "output_unit_price": 75.0},
    {"id": "ppio/pa/claude-opus-4-6", "label": "Claude Opus 4.6", "input_unit_price": 15.0, "output_unit_price": 75.0},
    {"id": "ppio/pa/claude-sonnet-4-6", "label": "Claude Sonnet 4.6", "input_unit_price": 3.0, "output_unit_price": 15.0},
    {"id": "azure_openai/gpt-5.4", "label": "GPT-5.4", "input_unit_price": 5.0, "output_unit_price": 25.0},
    {"id": "azure_openai/gpt-5.3-codex", "label": "GPT-5.3 Codex", "input_unit_price": 5.0, "output_unit_price": 25.0},
    {"id": "vertex_ai/gemini-3.1-pro-preview", "label": "Gemini 3.1 Pro", "input_unit_price": 2.5, "output_unit_price": 12.5},
    {"id": "xiaomi/glm-5", "label": "GLM-5 (Xiaomi)", "input_unit_price": 1.0, "output_unit_price": 4.0},
    {"id": "xiaomi/mimo-v2.5-pro", "label": "MiMo v2.5 Pro", "input_unit_price": 1.0, "output_unit_price": 4.0},
]
