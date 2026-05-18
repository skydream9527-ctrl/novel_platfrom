from __future__ import annotations

import json
import logging
from typing import AsyncGenerator

import httpx

logger = logging.getLogger(__name__)

DEFAULT_BASE_URL = "http://model.mify.ai.srv/v1"
DEFAULT_API_KEY = "sk-XitB8gnr2LxiqNM9AuyKSmksl1Wc1riTaFMLPobQtN6AenAA"
DEFAULT_MODEL = "ppio/pa/claude-sonnet-4-6"
DEFAULT_TIMEOUT = 120.0

NO_TEMPERATURE_MODELS = frozenset({"gpt-5.4-pro", "gpt-5.5", "o1", "o3", "o4-mini"})


class LLMClient:
    def __init__(
        self,
        base_url: str = DEFAULT_BASE_URL,
        api_key: str = DEFAULT_API_KEY,
        default_model: str = DEFAULT_MODEL,
        timeout: float = DEFAULT_TIMEOUT,
    ):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.default_model = default_model
        self.timeout = timeout

    def _split_model_id(self, model_id: str) -> tuple[str, str]:
        parts = model_id.split("/", 1)
        if len(parts) == 2:
            return parts[0], parts[1]
        return "", model_id

    def _build_headers(self, provider: str) -> dict[str, str]:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        if provider:
            headers["X-Model-Provider-Id"] = provider
        return headers

    async def stream_chat(
        self,
        messages: list[dict],
        model: str | None = None,
        tools: list[dict] | None = None,
        max_tokens: int = 4096,
    ) -> AsyncGenerator[dict, None]:
        """
        Yields events:
          {"type": "content", "text": "..."}
          {"type": "tool_calls", "calls": [{"id": ..., "name": ..., "arguments": {...}}]}
        """
        model = model or self.default_model
        provider, model_name = self._split_model_id(model)
        headers = self._build_headers(provider)

        body: dict = {
            "model": model_name,
            "messages": messages,
            "stream": True,
            "max_tokens": max_tokens,
        }
        if model_name not in NO_TEMPERATURE_MODELS:
            body["temperature"] = 0.7
        if tools:
            body["tools"] = [{"type": "function", "function": t} for t in tools]

        url = f"{self.base_url}/chat/completions"
        tool_calls_acc: dict[int, dict] = {}

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            async with client.stream("POST", url, headers=headers, json=body) as resp:
                if resp.status_code != 200:
                    error_body = await resp.aread()
                    error_text = error_body.decode()[:300]
                    logger.error("LLM API error %s: %s", resp.status_code, error_text)
                    raise RuntimeError(f"LLM API error {resp.status_code}: {error_text}")

                async for line in resp.aiter_lines():
                    if not line.startswith("data: "):
                        continue
                    data_str = line[6:].strip()
                    if data_str == "[DONE]":
                        break
                    try:
                        chunk = json.loads(data_str)
                    except json.JSONDecodeError:
                        continue

                    choices = chunk.get("choices", [])
                    if not choices:
                        continue
                    delta = choices[0].get("delta", {})
                    finish_reason = choices[0].get("finish_reason")

                    content = delta.get("content")
                    if content:
                        yield {"type": "content", "text": content}

                    for tc in delta.get("tool_calls", []):
                        idx = tc.get("index", 0)
                        if idx not in tool_calls_acc:
                            tool_calls_acc[idx] = {
                                "id": tc.get("id", ""),
                                "name": tc.get("function", {}).get("name", ""),
                                "arguments": "",
                            }
                        if tc.get("id"):
                            tool_calls_acc[idx]["id"] = tc["id"]
                        fn = tc.get("function", {})
                        if fn.get("name"):
                            tool_calls_acc[idx]["name"] = fn["name"]
                        if fn.get("arguments"):
                            tool_calls_acc[idx]["arguments"] += fn["arguments"]

                    if finish_reason in ("tool_calls", "stop") and tool_calls_acc:
                        break

        if tool_calls_acc:
            calls = []
            for idx in sorted(tool_calls_acc):
                tc = tool_calls_acc[idx]
                try:
                    parsed_args = json.loads(tc["arguments"]) if tc["arguments"] else {}
                except json.JSONDecodeError:
                    parsed_args = {"_raw": tc["arguments"]}
                calls.append({
                    "id": tc["id"],
                    "name": tc["name"],
                    "arguments": parsed_args,
                })
            yield {"type": "tool_calls", "calls": calls}
