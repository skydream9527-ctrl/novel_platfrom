import { ReactNode, useEffect } from "react";
import "./ConfirmModal.css";

interface Props {
  open: boolean;
  title: string;
  body?: ReactNode;
  confirmText?: string;
  cancelText?: string;
  danger?: boolean;
  onConfirm: () => void;
  onCancel: () => void;
}

export function ConfirmModal({
  open,
  title,
  body,
  confirmText = "确定",
  cancelText = "取消",
  danger,
  onConfirm,
  onCancel,
}: Props) {
  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onCancel();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open, onCancel]);
  if (!open) return null;
  return (
    <div className="cm-overlay" onClick={onCancel}>
      <div className="cm-card" onClick={(e) => e.stopPropagation()}>
        <h3>{title}</h3>
        {body && <div className="cm-body">{body}</div>}
        <div className="cm-actions">
          <button className="btn-secondary" onClick={onCancel}>
            {cancelText}
          </button>
          <button
            className={danger ? "cm-danger" : "btn-primary"}
            onClick={onConfirm}
          >
            {confirmText}
          </button>
        </div>
      </div>
    </div>
  );
}
