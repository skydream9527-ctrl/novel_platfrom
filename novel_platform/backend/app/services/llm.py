import json
from collections.abc import AsyncGenerator

import httpx

from ..core.config import settings


async def chat_stream(messages: list[dict], model: str | None = None) -> AsyncGenerator[str, None]:
    """Stream chat completion via OpenAI-compatible API."""
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
