import { useEffect, useState } from "react";
import { joinRequestApi } from "@/api/endpoints";
import { useUIStore } from "@/stores/uiStore";
import type { JoinRequest } from "@/types/api";
import "./JoinRequestPanel.css";

export interface JoinRequestPanelProps {
  taskId: string;
  role: "viewer" | "editor" | "owner" | "admin";
  onJoined?: () => void;
}

const VIEWER_ERROR_CODE_MESSAGES: Record<string, string> = {
  JOIN_ALREADY_PENDING: "已有待处理的申请，请耐心等待",
  JOIN_ALREADY_MEMBER: "你已是协作成员",
};

function extractErrMsg(err: unknown, fallback: string): { code?: string; message: string } {
  const e = err as { response?: { data?: { error_code?: string; message?: string } } };
  return {
    code: e?.response?.data?.error_code,
    message: e?.response?.data?.message || fallback,
  };
}

function formatDateTime(iso?: string | null): string {
  if (!iso) return "";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return "";
  return d.toLocaleString();
}

function ViewerView({
  taskId,
  onJoined,
}: {
  taskId: string;
  onJoined?: () => void;
}) {
  const pushToast = useUIStore((s) => s.pushToast);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [message, setMessage] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState(false);

  const openDialog = () => {
    setMessage("");
    setDialogOpen(true);
  };
  const closeDialog = () => {
    if (submitting) return;
    setDialogOpen(false);
  };

  const handleSubmit = async () => {
    const trimmed = message.trim();
    if (!trimmed) {
      alert("请填写申请说明");
      return;
    }
    setSubmitting(true);
    try {
      await joinRequestApi.submit(taskId, trimmed);
      pushToast("success", "申请已提交，等待审核");
      setSubmitted(true);
      setDialogOpen(false);
      onJoined?.();
    } catch (err: unknown) {
      const { code, message: msg } = extractErrMsg(err, "提交失败，请稍后重试");
      const friendly = (code && VIEWER_ERROR_CODE_MESSAGES[code]) || msg;
      alert(friendly);
      if (code === "JOIN_ALREADY_PENDING" || code === "JOIN_ALREADY_MEMBER") {
        setSubmitted(true);
        setDialogOpen(false);
      }
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="jrp jrp-viewer">
      {submitted ? (
        <div className="jrp-viewer-submitted">
          申请已提交，等待管理员审核
        </div>
      ) : (
        <button type="button" className="jrp-submit-btn" onClick={openDialog}>
          申请加入共建
        </button>
      )}

      {dialogOpen && (
        <div
          className="jrp-backdrop"
          onClick={(e) => {
            if (e.target === e.currentTarget) closeDialog();
          }}
        >
          <div className="jrp-dialog" role="dialog" aria-modal="true">
            <div className="jrp-dialog-head">
              <h3 className="jrp-dialog-title">申请加入共建</h3>
              <button
                type="button"
                className="jrp-dialog-close"
                onClick={closeDialog}
                disabled={submitting}
                aria-label="关闭"
              >
                ×
              </button>
            </div>
            <div className="jrp-dialog-body">
              <label className="jrp-label" htmlFor="jrp-message">
                申请说明
              </label>
              <textarea
                id="jrp-message"
                className="jrp-textarea"
                rows={4}
                placeholder="简要说明加入目的，便于管理员审核"
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                disabled={submitting}
                autoFocus
              />
            </div>
            <div className="jrp-dialog-actions">
              <button
                type="button"
                className="jrp-btn-ghost"
                onClick={closeDialog}
                disabled={submitting}
              >
                取消
              </button>
              <button
                type="button"
                className="jrp-btn-primary"
                onClick={handleSubmit}
                disabled={submitting || !message.trim()}
              >
                {submitting ? "提交中…" : "提交申请"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function OwnerView({
  taskId,
  onJoined,
}: {
  taskId: string;
  onJoined?: () => void;
}) {
  const pushToast = useUIStore((s) => s.pushToast);
  const [items, setItems] = useState<JoinRequest[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [actingId, setActingId] = useState<string | null>(null);

  const load = async () => {
    if (!taskId) return;
    setLoading(true);
    setError(null);
    try {
      const res = await joinRequestApi.list(taskId, "pending");
      setItems(res.items);
    } catch (err: unknown) {
      setError(extractErrMsg(err, "加载申请失败").message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [taskId]);

  const review = async (req: JoinRequest, status: "approved" | "rejected") => {
    let reason: string | undefined;
    if (status === "rejected") {
      const input = window.prompt("填写拒绝原因（可留空）", "");
      if (input === null) return;
      reason = input.trim() || undefined;
    }
    setActingId(req.id);
    try {
      await joinRequestApi.review(taskId, req.id, status, reason);
      pushToast("success", status === "approved" ? "已通过申请" : "已拒绝申请");
      setItems((arr) => arr.filter((r) => r.id !== req.id));
      if (status === "approved") {
        onJoined?.();
      }
    } catch (err: unknown) {
      alert(extractErrMsg(err, "操作失败，请稍后重试").message);
    } finally {
      setActingId(null);
    }
  };

  return (
    <div className="jrp jrp-owner">
      <div className="jrp-head">
        <span className="jrp-title">待处理申请</span>
        <button
          type="button"
          className="jrp-refresh"
          onClick={load}
          disabled={loading}
          title="刷新"
        >
          ↻
        </button>
      </div>

      {loading && <div className="jrp-status">加载中…</div>}
      {error && <div className="jrp-status jrp-error">{error}</div>}
      {!loading && !error && items.length === 0 && (
        <div className="jrp-status">暂无待处理申请</div>
      )}

      <ul className="jrp-list">
        {items.map((req) => {
          const acting = actingId === req.id;
          return (
            <li key={req.id} className="jrp-item">
              <div className="jrp-item-main">
                <div className="jrp-item-user" title={req.user_id}>
                  {req.user_id}
                </div>
                <div className="jrp-item-msg">
                  {req.message || <span className="jrp-muted">（无说明）</span>}
                </div>
                <div className="jrp-item-meta">
                  {formatDateTime(req.created_at)}
                </div>
              </div>
              <div className="jrp-item-actions">
                <button
                  type="button"
                  className="jrp-btn-approve"
                  onClick={() => review(req, "approved")}
                  disabled={acting}
                >
                  通过
                </button>
                <button
                  type="button"
                  className="jrp-btn-reject"
                  onClick={() => review(req, "rejected")}
                  disabled={acting}
                >
                  拒绝
                </button>
              </div>
            </li>
          );
        })}
      </ul>
    </div>
  );
}

function JoinRequestPanel({ taskId, role, onJoined }: JoinRequestPanelProps) {
  if (role === "editor") return null;
  if (role === "viewer") {
    return <ViewerView taskId={taskId} onJoined={onJoined} />;
  }
  return <OwnerView taskId={taskId} onJoined={onJoined} />;
}

export default JoinRequestPanel;
