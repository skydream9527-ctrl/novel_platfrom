"""WebSocket /ws/conversations/{cid} — streaming chat + tool calling 5-round loop.

Auth: dual — 米盾 (Aegis) `X-Proxy-UserDetail` header, OR bearer JWT via
subprotocol `["bearer", "<token>"]` / legacy `?token=`. Either is sufficient.
"""
from __future__ import annotations

import asyncio
import json
import logging
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect

from ...core.config import get_settings
from ...core.deps import resolve_user
from ...core.errors import APIError, ErrorCode
from ...core.storage import append_jsonl, get_paths
from ...services import (
    agents_svc,
    experience_card_svc,
    llm_gateway,
    task_svc,
    tool_runner,
    usage_svc,
)

router = APIRouter()
log = logging.getLogger("ws")


def _now() -> str:
    return datetime.now(tz=timezone.utc).isoformat()


def _new_id() -> str:
    return uuid.uuid4().hex


@router.websocket("/ws/conversations/{conversation_id}")
async def ws_chat(
    websocket: WebSocket,
    conversation_id: str,
    task_id: str = Query(...),
    token: str | None = Query(default=None),
):
    """Auth — try Aegis header first, then bearer (subprotocol or `?token=`).

    For the subprotocol path: client requests `["bearer", "<access_token>"]`;
    server picks `"bearer"` so the upgrade succeeds with that subprotocol.
    """
    offered = (websocket.headers.get("sec-websocket-protocol") or "").split(",")
    offered = [p.strip() for p in offered if p.strip()]
    chosen_proto: str | None = None
    sub_token: str | None = None
    if "bearer" in offered:
        chosen_proto = "bearer"
        for p in offered:
            if p != "bearer":
                sub_token = p
                break
    bearer = sub_token or token
    auth_header = f"Bearer {bearer}" if bearer else None

    try:
        user = await resolve_user(websocket.headers.get("x-proxy-userdetail"), auth_header)
    except APIError:
        await websocket.close(code=4401)
        return

    try:
        await task_svc.get_task(task_id, user["id"])
    except APIError:
        await websocket.close(code=4403)
        return

    if chosen_proto:
        await websocket.accept(subprotocol=chosen_proto)
    else:
        await websocket.accept()
    paths = get_paths()
    conv_path = paths.task_conversation(task_id, conversation_id)
    tool_path = paths.task_tool_calls(task_id, conversation_id)

    # 当前生成回合的取消事件 + 后台任务句柄。把生成放后台跑，主循环始终
    # 可接 `abort` 消息，否则生成期间客户端的暂停按钮无法被读到（D46 bug）。
    current_cancel: asyncio.Event | None = None
    current_task: asyncio.Task | None = None

    async def _run_turn(msg: dict, cancel: asyncio.Event) -> None:
        try:
            await _handle_user_message(
                websocket, msg, user, task_id, conversation_id, conv_path, tool_path, cancel
            )
        except Exception:
            log.exception("turn task crashed")

    try:
        while True:
            try:
                raw = await websocket.receive_text()
            except WebSocketDisconnect:
                break
            try:
                msg = json.loads(raw)
            except json.JSONDecodeError:
                await _send_error(websocket, "INVALID_JSON", "invalid JSON payload")
                continue
            mtype = msg.get("type")
            if mtype == "abort":
                if current_cancel is not None:
                    current_cancel.set()
                continue
            if mtype != "user_message":
                await _send_error(websocket, "UNKNOWN_TYPE", f"unknown type {mtype}")
                continue

            # 上一回合若仍在跑，先取消并等它收尾，避免两个回合并发写同一会话。
            if current_task is not None and not current_task.done():
                if current_cancel is not None:
                    current_cancel.set()
                try:
                    await asyncio.wait_for(current_task, timeout=5.0)
                except asyncio.TimeoutError:
                    current_task.cancel()
                    try:
                        await current_task
                    except (asyncio.CancelledError, Exception):
                        pass

            current_cancel = asyncio.Event()
            current_task = asyncio.create_task(_run_turn(msg, current_cancel))
    finally:
        if current_task is not None and not current_task.done():
            if current_cancel is not None:
                current_cancel.set()
            try:
                await asyncio.wait_for(current_task, timeout=2.0)
            except (asyncio.TimeoutError, Exception):
                current_task.cancel()
        try:
            await websocket.close()
        except Exception:
            pass


async def _send(ws: WebSocket, payload: dict) -> None:
    try:
        await ws.send_text(json.dumps(payload, ensure_ascii=False))
    except Exception:
        pass


async def _send_error(ws: WebSocket, code: str, message: str) -> None:
    await _send(ws, {"type": "error", "error_code": code, "message": message})


async def _handle_user_message(
    ws: WebSocket,
    msg: dict,
    user: dict,
    task_id: str,
    conversation_id: str,
    conv_path,
    tool_path,
    cancel_event: asyncio.Event,
):
    s = get_settings()
    user_msg_id = _new_id()
    content = (msg.get("content") or "").strip()
    if not content:
        await _send_error(ws, ErrorCode.VALIDATION_ERROR, "empty message")
        return

    user_record = {
        "id": user_msg_id,
        "role": "user",
        "content": content,
        "user_id": user["id"],
        "created_at": _now(),
    }
    append_jsonl(conv_path, user_record)
    await _send(ws, {"type": "user_message_ack", "message_id": user_msg_id})
    await task_svc.touch_task(task_id, last_message_preview=content)

    if not s.llm_enabled:
        await _send(
            ws,
            {
                "type": "error",
                "error_code": ErrorCode.LLM_KEY_MISSING,
                "message": "LLM API Key 未配置，请联系 @gongyunhe",
            },
        )
        return

    history = task_svc.load_conversation_messages(task_id, conversation_id)
    api_messages = _to_api_messages(history, task_id=task_id, conversation_id=conversation_id)
    task = await task_svc.get_task(task_id, user["id"])
    agent_id = task.get("agent_id") or "biz-insight"
    system_prompt = experience_card_svc.merged_system_prompt(agent_id)
    tools = tool_runner.get_anthropic_tools()
    # Per-message > task workspace > settings default
    model_id = (
        msg.get("model")
        or (task.get("workspace") or {}).get("model")
        or llm_gateway.resolve_model(None)
    )

    await _send(ws, {"type": "agent_typing", "status": "start"})

    final_text = ""
    files_created: list[dict] = []
    try:
        for round_idx in range(llm_gateway.MAX_TOOL_ROUNDS + 1):
            if cancel_event.is_set():
                await _send(ws, {"type": "agent_typing", "status": "stop"})
                await _send(ws, {"type": "agent_message_done", "files_created": files_created, "aborted": True})
                return
            assistant_msg_id = _new_id()
            text_buf = []
            tool_uses: list[dict] = []
            done_event = None
            try:
                async for ev in llm_gateway.stream_chat(
                    system_prompt=system_prompt,
                    messages=api_messages,
                    tools=tools,
                    model=model_id,
                ):
                    if cancel_event.is_set():
                        break
                    if ev["type"] == "text":
                        text_buf.append(ev["delta"])
                        await _send(
                            ws,
                            {
                                "type": "agent_message",
                                "message_id": assistant_msg_id,
                                "content": ev["delta"],
                            },
                        )
                    elif ev["type"] == "tool_use_delta":
                        # OpenAI streams tool calls incrementally; surface for
                        # frontend to show "正在准备参数…" before tool_call_start.
                        await _send(
                            ws,
                            {
                                "type": "tool_call_preview",
                                "message_id": assistant_msg_id,
                                "index": ev.get("index"),
                                "id": ev.get("id"),
                                "name": ev.get("name"),
                                "args_chunk": ev.get("args_chunk", ""),
                            },
                        )
                    elif ev["type"] == "message_done":
                        done_event = ev
                        for block in ev.get("content") or []:
                            if block.get("type") == "tool_use":
                                tool_uses.append(block)
            except Exception as e:
                log.exception("gateway stream failed")
                from ...core.errors import APIError as _APIError
                if isinstance(e, _APIError):
                    raise
                raise _APIError(502, "GATEWAY_ERROR", str(e)[:500]) from e
            if cancel_event.is_set():
                # 保留已经生成的部分到对话历史，便于用户接着追问。
                partial_text = "".join(text_buf)
                if partial_text or tool_uses:
                    append_jsonl(
                        conv_path,
                        {
                            "id": assistant_msg_id,
                            "role": "assistant",
                            "content": partial_text,
                            "tool_uses": tool_uses,
                            "agent_id": agent_id,
                            "stop_reason": "user_aborted",
                            "usage": (done_event or {}).get("usage") or {},
                            "created_at": _now(),
                        },
                    )
                    final_text = partial_text or final_text
                await _send(ws, {"type": "agent_typing", "status": "stop"})
                await _send(ws, {"type": "agent_message_done", "files_created": files_created, "aborted": True})
                return
            assistant_text = "".join(text_buf)
            usage = (done_event or {}).get("usage") or {}
            assistant_record = {
                "id": assistant_msg_id,
                "role": "assistant",
                "content": assistant_text,
                "tool_uses": tool_uses,
                "agent_id": agent_id,
                "stop_reason": (done_event or {}).get("stop_reason"),
                "usage": usage,
                "created_at": _now(),
            }
            append_jsonl(conv_path, assistant_record)
            try:
                await usage_svc.record_usage(
                    user_id=user["id"],
                    agent_id=agent_id,
                    task_id=task_id,
                    conversation_id=conversation_id,
                    model=model_id,
                    input_tokens=int(usage.get("input_tokens") or 0),
                    output_tokens=int(usage.get("output_tokens") or 0),
                    success=True,
                )
            except Exception as exc:
                log.warning("record_usage failed: %s", exc)
            api_messages.append(
                {
                    "role": "assistant",
                    "content": _rebuild_content_blocks(assistant_text, tool_uses),
                }
            )
            final_text = assistant_text or final_text

            if not tool_uses or round_idx == llm_gateway.MAX_TOOL_ROUNDS:
                break

            tool_results = []
            for tu in tool_uses:
                tu_id = tu.get("id")
                tu_name = tu.get("name")
                tu_input = tu.get("input") or {}
                await _send(
                    ws,
                    {
                        "type": "tool_call_start",
                        "tool_call_id": tu_id,
                        "tool_name": tu_name,
                        "display_name": tool_runner.get_display_name(tu_name),
                        "arguments": tu_input,
                    },
                )
                started = _now()

                async def _runner():
                    return await tool_runner.execute_tool(
                        tu_name,
                        tu_input,
                        ctx={
                            "user_id": user["id"],
                            "agent_id": agent_id,
                            "task_id": task_id,
                            "conversation_id": conversation_id,
                        },
                    )

                outcome = await llm_gateway.run_tool_with_timeout(_runner)
                done_payload = {
                    "type": "tool_call_done",
                    "tool_call_id": tu_id,
                    "tool_name": tu_name,
                    "status": outcome["status"],
                    "success": outcome["success"],
                    "result": outcome.get("result"),
                    "error": outcome.get("error"),
                }
                await _send(ws, done_payload)

                # If a file landed in the workspace, push a file_created event so
                # the left-side panel can refresh without waiting for end-of-turn.
                if (
                    tu_name == "write_file"
                    and outcome.get("success")
                    and isinstance(outcome.get("result"), dict)
                    and outcome["result"].get("file_id")
                ):
                    res = outcome["result"]
                    file_meta = {
                        "id": res["file_id"],
                        "name": res.get("name"),
                        "size_bytes": res.get("size_bytes"),
                        "scope": res.get("scope", "output"),
                        "path": res.get("path"),
                    }
                    files_created.append(file_meta)
                    await _send(ws, {"type": "file_created", "file": file_meta})
                append_jsonl(
                    tool_path,
                    {
                        "id": tu_id,
                        "tool_name": tu_name,
                        "arguments": tu_input,
                        "status": outcome["status"],
                        "success": outcome["success"],
                        "result": outcome.get("result"),
                        "error": outcome.get("error"),
                        "started_at": started,
                        "ended_at": _now(),
                    },
                )
                tool_results.append(
                    {
                        "type": "tool_result",
                        "tool_use_id": tu_id,
                        "content": json.dumps(outcome.get("result") or outcome.get("error") or {}, ensure_ascii=False),
                        "is_error": not outcome["success"],
                    }
                )
            api_messages.append({"role": "user", "content": tool_results})

        await _send(ws, {"type": "agent_message_done", "files_created": files_created})
    except APIError as e:
        await _send(ws, {"type": "error", "error_code": e.error_code, "message": e.message})
    except Exception as e:
        log.exception("ws stream error")
        await _send(ws, {"type": "error", "error_code": "INTERNAL_ERROR", "message": str(e)})
    finally:
        await _send(ws, {"type": "agent_typing", "status": "stop"})
        if final_text:
            await task_svc.touch_task(task_id, last_message_preview=final_text)


def _to_api_messages(
    history: list[dict],
    *,
    task_id: str | None = None,
    conversation_id: str | None = None,
) -> list[dict]:
    """Rebuild Anthropic-shaped message list from persisted JSONL history.

    Critical invariant for the upstream model: every `tool_use` block in an
    assistant message MUST be followed by matching `tool_result` blocks in the
    next user message. We read the tool_calls jsonl for the conversation and
    splice synthetic `tool_result` user-messages in between assistant turns.

    Without this fix, recent history (e.g. after page refresh or multi-tool
    rounds) sends the model orphan tool_use ids → 400 GATEWAY_ERROR.
    """
    # Index tool outcomes by tool_call_id so we can answer every tool_use.
    tool_results_by_id: dict[str, dict] = {}
    if task_id and conversation_id:
        from ...core.storage import get_paths, read_jsonl

        path = get_paths().task_tool_calls(task_id, conversation_id)
        for rec in read_jsonl(path):
            tid = rec.get("id")
            if tid:
                tool_results_by_id[tid] = rec

    # Walk history in chronological order; truncate from the start while keeping
    # turn-pairs intact so we never split an assistant→tool_result pair.
    raw = history[-20:] if len(history) > 20 else list(history)
    # If the slice happens to start with a tool_result-only user message,
    # drop it (orphan from the prior turn).
    while raw and raw[0].get("role") == "user" and not (raw[0].get("content") or "").strip() and not raw[0].get("tool_uses"):
        raw = raw[1:]

    out: list[dict] = []
    for h in raw:
        role = h.get("role")
        if role == "user":
            out.append({"role": "user", "content": h.get("content", "")})
            continue
        if role != "assistant":
            continue

        content = h.get("content", "")
        tool_uses = h.get("tool_uses") or []

        if tool_uses:
            # Build assistant message with text + tool_use blocks.
            blocks: list[dict] = []
            if content:
                blocks.append({"type": "text", "text": content})
            for tu in tool_uses:
                # Strip nullable upstream-extension fields (e.g. `caller`) so
                # the message survives Bedrock validation on round-trip.
                blocks.append({k: v for k, v in tu.items() if v is not None})
            out.append({"role": "assistant", "content": blocks})

            # Follow with synthetic user{tool_result} message — every tool_use
            # MUST be answered or the model rejects the conversation.
            results: list[dict] = []
            for tu in tool_uses:
                tid = tu.get("id")
                rec = tool_results_by_id.get(tid)
                if rec:
                    payload = rec.get("result") if rec.get("success") else rec.get("error")
                    body = (
                        payload
                        if isinstance(payload, str)
                        else __import__("json").dumps(payload or {}, ensure_ascii=False)
                    )
                    results.append(
                        {
                            "type": "tool_result",
                            "tool_use_id": tid,
                            "content": body,
                            **({"is_error": True} if not rec.get("success") else {}),
                        }
                    )
                else:
                    # No record found — emit a stub so the pairing constraint
                    # holds; mark as error so the model knows it's incomplete.
                    results.append(
                        {
                            "type": "tool_result",
                            "tool_use_id": tid,
                            "content": "(tool_result unavailable in history)",
                            "is_error": True,
                        }
                    )
            out.append({"role": "user", "content": results})
        else:
            out.append({"role": "assistant", "content": content})

    return out


def _rebuild_content_blocks(text: str, tool_uses: list[dict]) -> list[dict] | str:
    if not tool_uses:
        return text
    blocks: list[dict] = []
    if text:
        blocks.append({"type": "text", "text": text})
    blocks.extend(tool_uses)
    return blocks
