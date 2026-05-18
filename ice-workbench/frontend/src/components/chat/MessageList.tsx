import { useEffect, useRef, useState } from "react";
import type { ChatMessage, ToolCall } from "@/types/api";
import { MarkdownRenderer } from "@/components/markdown/MarkdownRenderer";
import { ToolCallCard } from "./ToolCallCard";
import { useUIStore } from "@/stores/uiStore";
import type { PartialAssistant, StreamPhase } from "@/hooks/useChatSocket";
import "./MessageList.css";

interface Props {
  finalized: ChatMessage[];
  partial: PartialAssistant | null;
  phase: StreamPhase;
  onCrystallize?: (msg: ChatMessage) => void;
}

export function MessageList({ finalized, partial, phase, onCrystallize }: Props) {
  const ref = useRef<HTMLDivElement>(null);
  useEffect(() => {
    ref.current?.scrollTo({ top: ref.current.scrollHeight, behavior: "smooth" });
  }, [finalized.length, partial?.content, partial?.toolCalls.length, phase]);

  return (
    <div className="msg-list" ref={ref}>
      {finalized.map((m) =>
        m.role === "user" ? (
          <UserBubble key={m.id} content={m.content} />
        ) : (
          <AssistantBubble
            key={m.id}
            content={m.content}
            toolCalls={(m.tool_uses || []).map(
              (t): ToolCall => ({
                tool_call_id: t.id,
                tool_name: t.name,
                arguments: t.input as Record<string, unknown>,
                status: "done",
              }),
            )}
            onCrystallize={onCrystallize ? () => onCrystallize(m) : undefined}
          />
        ),
      )}
      {partial && <AssistantBubble content={partial.content} toolCalls={partial.toolCalls} streaming />}
      {phase === "typing" && !partial && <TypingDots />}
    </div>
  );
}

function UserBubble({ content }: { content: string }) {
  return (
    <div className="bubble-row user">
      <div className="bubble user-bubble">{content}</div>
    </div>
  );
}

function AssistantBubble({
  content,
  toolCalls,
  streaming,
  onCrystallize,
}: {
  content: string;
  toolCalls: ToolCall[];
  streaming?: boolean;
  onCrystallize?: () => void;
}) {
  const pushToast = useUIStore((s) => s.pushToast);
  const [copied, setCopied] = useState(false);

  const copy = async () => {
    try {
      if (navigator.clipboard?.writeText) {
        await navigator.clipboard.writeText(content);
      } else {
        // 老浏览器兜底
        const ta = document.createElement("textarea");
        ta.value = content;
        ta.style.position = "fixed";
        ta.style.opacity = "0";
        document.body.appendChild(ta);
        ta.select();
        document.execCommand("copy");
        document.body.removeChild(ta);
      }
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    } catch (err) {
      pushToast("error", `复制失败：${(err as Error).message}`);
    }
  };

  return (
    <div className="bubble-row assistant">
      <div className="agent-avatar">🤖</div>
      <div className="bubble assistant-bubble">
        {content && <MarkdownRenderer content={content} />}
        {streaming && content && <span className="cursor" />}
        {toolCalls.map((tc) => (
          <ToolCallCard key={tc.tool_call_id} call={tc} />
        ))}
        {!streaming && content && (
          <div className="msg-actions">
            <button
              className="msg-action-btn"
              onClick={copy}
              title="复制原文到剪贴板"
            >
              {copied ? "✅ 已复制" : "📋 复制"}
            </button>
            {onCrystallize && (
              <button
                className="msg-action-btn"
                onClick={onCrystallize}
                title="把这条洞察沉淀为 Agent 经验"
              >
                ✨ 沉淀经验
              </button>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

function TypingDots() {
  return (
    <div className="typing-dots">
      <span /> <span /> <span />
    </div>
  );
}
