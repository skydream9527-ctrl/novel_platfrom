import { useEffect, useState } from "react";
import { modelApi } from "@/api/endpoints";
import type { ModelOption } from "@/api/endpoints";

interface Props {
  value: string;
  onChange: (modelId: string) => void;
  compact?: boolean;
}

export function ModelSelector({ value, onChange, compact }: Props) {
  const [items, setItems] = useState<ModelOption[]>([]);
  useEffect(() => {
    modelApi
      .list()
      .then((r) => {
        setItems(r.items);
        if (!value && r.default) onChange(r.default);
      })
      .catch(() => {});
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <select
      value={value}
      onChange={(e) => onChange(e.target.value)}
      style={{
        background: compact ? "transparent" : "var(--surface-2)",
        border: compact ? "1px solid var(--border)" : "1px solid var(--border)",
        borderRadius: 6,
        color: "var(--text)",
        padding: compact ? "3px 8px" : "6px 10px",
        fontSize: compact ? 11 : 12,
        outline: "none",
        cursor: "pointer",
        fontFamily: "var(--font-mono)",
        maxWidth: compact ? 240 : "none",
      }}
      title="切换 LLM 模型"
    >
      {items.length === 0 && <option value="">加载中…</option>}
      {items.map((m) => (
        <option key={m.id} value={m.id}>
          {m.label} ({m.id})
        </option>
      ))}
    </select>
  );
}
