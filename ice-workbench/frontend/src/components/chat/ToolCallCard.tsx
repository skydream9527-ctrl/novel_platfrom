import { useState } from "react";
import type { ToolCall } from "@/types/api";
import "./ToolCallCard.css";

const STATUS_META: Record<ToolCall["status"], { color: string; badge: string; label: string }> = {
  executing: { color: "warning", badge: "⏳", label: "执行中" },
  done: { color: "success", badge: "✅", label: "已完成" },
  error: { color: "error", badge: "❌", label: "失败" },
  timeout: { color: "info", badge: "⏱", label: "已超时" },
};

interface Props {
  call: ToolCall;
  onRetry?: (call: ToolCall) => void;
  onCopyError?: (call: ToolCall) => void;
}

export function ToolCallCard({ call, onRetry, onCopyError }: Props) {
  const meta = STATUS_META[call.status];
  const [showArgs, setShowArgs] = useState(false);
  return (
    <div className={`tool-card tool-${meta.color}`}>
      <div className="tool-head">
        <span>{meta.badge}</span>
        <span>
          {meta.label} · {call.display_name || call.tool_name}
        </span>
        <button className="tool-toggle" onClick={() => setShowArgs((v) => !v)}>
          {showArgs ? "收起参数" : "查看完整参数"}
        </button>
      </div>
      {showArgs && (
        <pre className="tool-args">{JSON.stringify(call.arguments, null, 2)}</pre>
      )}
      {call.status === "done" && call.result != null && (
        <div className="tool-result success">
          {summarizeResult(call.result)}
        </div>
      )}
      {(call.status === "error" || call.status === "timeout") && (
        <>
          <div className="tool-result fail">
            {call.error?.message || "执行失败"}
          </div>
          <div className="tool-error-code">error_code: {call.error?.code || "UNKNOWN"}</div>
          <div className="tool-fail-actions">
            {onRetry && (
              <button onClick={() => onRetry(call)} className="btn-mini">
                🔁 重试
              </button>
            )}
            {onCopyError && (
              <button onClick={() => onCopyError(call)} className="btn-mini">
                📋 复制错误
              </button>
            )}
          </div>
        </>
      )}
    </div>
  );
}

function summarizeResult(r: unknown): string {
  if (r == null) return "";
  if (typeof r === "string") return r.slice(0, 240);
  try {
    const s = JSON.stringify(r);
    if (s.length < 200) return s;
    return s.slice(0, 200) + "…";
  } catch {
    return String(r);
  }
}
