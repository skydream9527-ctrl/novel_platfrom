import { useCallback, useEffect, useRef, useState } from "react";
import type { ChatMessage, ToolCall } from "@/types/api";

export type StreamPhase = "idle" | "typing" | "streaming" | "tool" | "done" | "error";

export interface PartialAssistant {
  id: string;
  content: string;
  toolCalls: ToolCall[];
}

interface UseChatSocketOpts {
  taskId: string;
  conversationId: string | null;
  onError?: (errorCode: string, message: string) => void;
  onFileCreated?: (file: { id: string; name: string }) => void;
}

interface SocketState {
  status: "idle" | "connecting" | "open" | "closed";
  phase: StreamPhase;
  partial: PartialAssistant | null;
  finalized: ChatMessage[];
  send: (content: string, opts?: { model?: string }) => void;
  abort: () => void;
  clearError: () => void;
  errorCode: string | null;
}

export function useChatSocket({ taskId, conversationId, onError, onFileCreated }: UseChatSocketOpts): SocketState {
  const [status, setStatus] = useState<SocketState["status"]>("idle");
  const [phase, setPhase] = useState<StreamPhase>("idle");
  const [partial, setPartial] = useState<PartialAssistant | null>(null);
  const [finalized, setFinalized] = useState<ChatMessage[]>([]);
  const [errorCode, setErrorCode] = useState<string | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const retryRef = useRef<number>(0);
  const retryTimerRef = useRef<number | null>(null);

  // 镜像 partial 到 ref，让事件处理器读到的是最新值。
  // 不能在 setPartial 的 updater 里嵌套调 setFinalized——React 18 StrictMode 在
  // dev 模式会双调 updater 验证纯函数性,导致 finalize 一条消息追加两遍。
  const partialRef = useRef<PartialAssistant | null>(null);
  useEffect(() => {
    partialRef.current = partial;
  }, [partial]);

  const connect = useCallback(() => {
    if (!conversationId) return;
    setStatus("connecting");
    const proto = location.protocol === "https:" ? "wss" : "ws";
    const url = `${proto}://${location.host}/api/v1/ws/conversations/${conversationId}?task_id=${encodeURIComponent(taskId)}`;
    // 米盾 (Aegis) 接入后鉴权由代理注入的 cookie/header 完成，WS 握手不带
    // subprotocol；本地 dev 用 AEGIS_DEV_BYPASS_EMAIL 放行。
    const ws = new WebSocket(url);
    wsRef.current = ws;

    ws.onopen = () => {
      setStatus("open");
      retryRef.current = 0;
    };
    ws.onmessage = (ev) => {
      try {
        const data = JSON.parse(ev.data);
        handleEvent(data);
      } catch {
        /* ignore */
      }
    };
    ws.onclose = () => {
      setStatus("closed");
      // exponential backoff: 1,2,4,8,16,30 max
      const delays = [1000, 2000, 4000, 8000, 16000, 30000];
      const delay = delays[Math.min(retryRef.current, delays.length - 1)];
      retryRef.current += 1;
      retryTimerRef.current = window.setTimeout(connect, delay);
    };
    ws.onerror = () => {
      // close handler will trigger reconnect
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [conversationId, taskId]);

  const handleEvent = (ev: any) => {
    switch (ev.type) {
      case "user_message_ack":
        // user message already pushed locally on send; nothing to do
        break;
      case "agent_typing":
        setPhase(ev.status === "start" ? "typing" : "idle");
        break;
      case "agent_message":
        setPhase("streaming");
        setPartial((cur) => {
          if (!cur) {
            return {
              id: ev.message_id,
              content: ev.content,
              toolCalls: [],
            };
          }
          if (cur.id !== ev.message_id) {
            // new round; flush previous
            return {
              id: ev.message_id,
              content: ev.content,
              toolCalls: cur.toolCalls,
            };
          }
          return { ...cur, content: cur.content + ev.content };
        });
        break;
      case "tool_call_start":
        setPhase("tool");
        setPartial((cur) => {
          const base = cur ?? { id: "tmp", content: "", toolCalls: [] };
          return {
            ...base,
            toolCalls: [
              ...base.toolCalls,
              {
                tool_call_id: ev.tool_call_id,
                tool_name: ev.tool_name,
                display_name: ev.display_name,
                arguments: ev.arguments || {},
                status: "executing",
              },
            ],
          };
        });
        break;
      case "tool_call_done":
        setPartial((cur) => {
          if (!cur) return cur;
          return {
            ...cur,
            toolCalls: cur.toolCalls.map((tc) =>
              tc.tool_call_id === ev.tool_call_id
                ? {
                    ...tc,
                    status: ev.status,
                    result: ev.result,
                    error: ev.error,
                  }
                : tc,
            ),
          };
        });
        break;
      case "agent_message_done": {
        const cur = partialRef.current;
        if (cur) {
          setFinalized((arr) => {
            // 防御性去重：万一同一 message_id 已落库，不再追加。
            if (arr.some((m) => m.id === cur.id)) return arr;
            return [
              ...arr,
              {
                id: cur.id,
                role: "assistant",
                content: cur.content,
                tool_uses: cur.toolCalls.map((t) => ({
                  id: t.tool_call_id,
                  name: t.tool_name,
                  input: t.arguments,
                })),
                created_at: new Date().toISOString(),
              },
            ];
          });
        }
        setPartial(null);
        setPhase("done");
        break;
      }
      case "file_created":
        if (ev.file?.id && ev.file?.name) {
          onFileCreated?.({ id: ev.file.id, name: ev.file.name });
        }
        break;
      case "error":
        setErrorCode(ev.error_code || "ERROR");
        setPhase("error");
        onError?.(ev.error_code || "ERROR", ev.message || "");
        break;
    }
  };

  useEffect(() => {
    connect();
    return () => {
      if (retryTimerRef.current) window.clearTimeout(retryTimerRef.current);
      wsRef.current?.close();
    };
  }, [connect]);

  const send = (content: string, opts?: { model?: string }) => {
    setErrorCode(null);
    setFinalized((arr) => [
      ...arr,
      {
        id: `local-${Date.now()}`,
        role: "user",
        content,
        created_at: new Date().toISOString(),
      },
    ]);
    setPhase("typing");
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      const payload: Record<string, unknown> = { type: "user_message", content };
      if (opts?.model) payload.model = opts.model;
      wsRef.current.send(JSON.stringify(payload));
    } else {
      setErrorCode("WS_DISCONNECTED");
      setPhase("error");
    }
  };

  const abort = () => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: "abort" }));
    }
  };

  return {
    status,
    phase,
    partial,
    finalized,
    send,
    abort,
    errorCode,
    clearError: () => setErrorCode(null),
  };
}
