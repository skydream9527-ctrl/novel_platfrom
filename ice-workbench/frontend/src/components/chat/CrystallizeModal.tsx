import { useEffect, useState } from "react";
import { experienceApi } from "@/api/endpoints";
import { useUIStore } from "@/stores/uiStore";
import "./CrystallizeModal.css";

interface Props {
  open: boolean;
  taskId: string;
  sourceMessage: { id: string; content: string } | null;
  onClose: () => void;
  onCreated?: () => void;
}

export function CrystallizeModal({ open, taskId, sourceMessage, onClose, onCreated }: Props) {
  const pushToast = useUIStore((s) => s.pushToast);
  const [title, setTitle] = useState("");
  const [rule, setRule] = useState("");
  const [reason, setReason] = useState("");
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (open && sourceMessage) {
      const firstLine = (sourceMessage.content || "").split("\n").map((s) => s.trim()).filter(Boolean)[0] || "";
      setTitle(firstLine.slice(0, 24));
      setRule(sourceMessage.content.slice(0, 600));
      setReason("");
    }
  }, [open, sourceMessage]);

  // ESC 关闭
  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open, onClose]);

  // 弹窗打开时锁住主页面滚动
  useEffect(() => {
    if (!open) return;
    const prev = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      document.body.style.overflow = prev;
    };
  }, [open]);

  if (!open) return null;

  const submit = async () => {
    if (!title.trim() || !rule.trim()) {
      pushToast("warning", "请填写标题与规则");
      return;
    }
    setSaving(true);
    try {
      await experienceApi.createForTask(taskId, {
        title: title.trim(),
        rule: rule.trim(),
        reason: reason.trim() || undefined,
        source_message_id: sourceMessage?.id,
      });
      pushToast("success", "已沉淀，待 admin 审批后注入 Agent");
      onCreated?.();
      onClose();
    } catch (err) {
      pushToast("error", (err as Error).message);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="crystallize-overlay" onClick={onClose} role="dialog" aria-modal="true">
      <div className="crystallize-card" onClick={(e) => e.stopPropagation()}>
        <div className="crystallize-head">
          <h3>✨ 沉淀经验</h3>
          <p className="crystallize-hint">
            提炼为简短规则（一句话 + 依据），admin 审批后会自动注入到此 Agent 的 system prompt，下次对话生效。
          </p>
        </div>
        <div className="crystallize-body">
          <label className="crystallize-field">
            <span>标题（一句话）</span>
            <input
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              maxLength={120}
              placeholder="例如：渠道归因优先看自然流量与推荐版本"
              autoFocus
            />
          </label>
          <label className="crystallize-field">
            <span>规则内容</span>
            <textarea
              rows={6}
              value={rule}
              onChange={(e) => setRule(e.target.value)}
              placeholder="把这条洞察写成对未来对话有用的 1-3 句规则"
            />
          </label>
          <label className="crystallize-field">
            <span>依据 / 上下文（可选）</span>
            <textarea
              rows={3}
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              placeholder="为什么这条规则成立？引用对话证据"
            />
          </label>
        </div>
        <div className="crystallize-actions">
          <button className="btn-secondary" type="button" onClick={onClose}>
            取消
          </button>
          <button className="btn-primary" type="button" disabled={saving} onClick={submit}>
            {saving ? "提交中…" : "提交审批"}
          </button>
        </div>
      </div>
    </div>
  );
}
