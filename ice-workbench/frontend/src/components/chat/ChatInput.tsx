import { KeyboardEvent, useState } from "react";
import "./ChatInput.css";

interface Props {
  paradigm?: string;
  disabled?: boolean;
  isStreaming?: boolean;
  onSend: (text: string) => void;
  onAbort?: () => void;
}

const PARADIGM_PLACEHOLDER: Record<string, string> = {
  biz: "描述你的经营分析问题，比如：上周 DAU 下滑的原因…",
  ab: "描述你的实验，比如：v2.3 新版的留存影响…",
  wave: "描述指标异常，比如：周末转化率突然下降…",
  data: "用自然语言描述查询，比如：本月各渠道的 ARPU…",
  gray: "描述灰度版本对比，比如：v1.5 vs v1.4 的留存差异…",
};

export function ChatInput({ paradigm = "biz", disabled, isStreaming, onSend, onAbort }: Props) {
  const [value, setValue] = useState("");
  const handleKey = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      submit();
    }
  };
  const submit = () => {
    const text = value.trim();
    if (!text) return;
    onSend(text);
    setValue("");
  };
  return (
    <div className="chat-input">
      <textarea
        value={value}
        onChange={(e) => setValue(e.target.value)}
        onKeyDown={handleKey}
        placeholder={PARADIGM_PLACEHOLDER[paradigm] || "和 Agent 对话…"}
        disabled={disabled}
        rows={3}
      />
      <div className="chat-input-actions">
        <span className="chat-hint">Enter 发送 · Shift+Enter 换行</span>
        {isStreaming ? (
          <button className="btn-secondary" onClick={onAbort}>
            ⏸ 暂停生成
          </button>
        ) : (
          <button className="btn-primary" onClick={submit} disabled={disabled || !value.trim()}>
            发送 ↵
          </button>
        )}
      </div>
    </div>
  );
}
