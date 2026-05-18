import { useEffect, useState } from "react";
import { fileApi } from "@/api/endpoints";
import { useUIStore } from "@/stores/uiStore";
import type { FileMeta } from "@/types/api";
import "./ImportLinkDialog.css";

export interface ImportLinkDialogProps {
  open: boolean;
  taskId: string;
  onClose: () => void;
  onImported: (file: FileMeta) => void;
}

const ERROR_CODE_MESSAGES: Record<string, string> = {
  IMPORT_DUPLICATE: "该链接已导入",
  IMPORT_SOURCE_NOT_SUPPORTED: "仅支持飞书文档链接",
  FEISHU_DISABLED: "飞书集成未启用",
};

function ImportLinkDialog({ open, taskId, onClose, onImported }: ImportLinkDialogProps) {
  const pushToast = useUIStore((s) => s.pushToast);
  const [url, setUrl] = useState("");
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (!open) {
      setUrl("");
      setSubmitting(false);
    }
  }, [open]);

  if (!open) return null;

  const handleSubmit = async () => {
    const trimmed = url.trim();
    if (!trimmed) {
      alert("请输入飞书文档链接");
      return;
    }
    setSubmitting(true);
    try {
      const file = await fileApi.import_(taskId, "feishu_doc", trimmed);
      pushToast("success", "已导入");
      onImported(file);
      onClose();
    } catch (err: unknown) {
      const e = err as {
        response?: { data?: { error_code?: string; message?: string } };
      };
      const code = e?.response?.data?.error_code;
      const friendly =
        (code && ERROR_CODE_MESSAGES[code]) ||
        e?.response?.data?.message ||
        "导入失败，请稍后重试";
      alert(friendly);
    } finally {
      setSubmitting(false);
    }
  };

  const handleBackdrop = (e: React.MouseEvent<HTMLDivElement>) => {
    if (e.target === e.currentTarget && !submitting) {
      onClose();
    }
  };

  return (
    <div
      className="import-link-backdrop"
      onClick={handleBackdrop}
      role="presentation"
    >
      <div
        className="import-link-dialog"
        role="dialog"
        aria-modal="true"
        aria-labelledby="import-link-title"
      >
        <div className="ild-head">
          <h3 className="ild-title" id="import-link-title">
            导入飞书文档
          </h3>
          <button
            type="button"
            className="ild-close"
            onClick={onClose}
            disabled={submitting}
            aria-label="关闭"
          >
            ×
          </button>
        </div>

        <div className="ild-body">
          <label className="ild-label" htmlFor="import-link-url">
            文档链接
          </label>
          <input
            id="import-link-url"
            type="url"
            className="ild-input"
            placeholder="粘贴飞书文档链接 (https://*.feishu.cn/docx/... 或 /wiki/...)"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            disabled={submitting}
            autoFocus
          />
          <div className="ild-hint">
            支持 docx 与 wiki 链接。导入后会保留最新同步时间。
          </div>
        </div>

        <div className="ild-actions">
          <button
            type="button"
            className="ild-btn-ghost"
            onClick={onClose}
            disabled={submitting}
          >
            取消
          </button>
          <button
            type="button"
            className="ild-btn-primary"
            onClick={handleSubmit}
            disabled={submitting || !url.trim()}
          >
            {submitting ? "导入中…" : "导入"}
          </button>
        </div>
      </div>
    </div>
  );
}

export default ImportLinkDialog;
