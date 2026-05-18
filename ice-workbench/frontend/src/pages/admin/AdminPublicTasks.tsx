import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { reviewApi } from "@/api/endpoints";
import type { TaskSummary } from "@/types/api";
import { Skeleton } from "@/components/feedback/Skeleton";
import { ConfirmModal } from "@/components/feedback/ConfirmModal";
import { useUIStore } from "@/stores/uiStore";

const STATUS_TABS = [
  { k: "pending", label: "待审核" },
  { k: "published", label: "已发布" },
  { k: "rejected", label: "已驳回" },
] as const;

export function AdminPublicTasks() {
  const navigate = useNavigate();
  const pushToast = useUIStore((s) => s.pushToast);
  const [tab, setTab] = useState<(typeof STATUS_TABS)[number]["k"]>("pending");
  const [items, setItems] = useState<TaskSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [pendingApprove, setPendingApprove] = useState<TaskSummary | null>(null);
  const [pendingReject, setPendingReject] = useState<TaskSummary | null>(null);
  const [pendingDelist, setPendingDelist] = useState<TaskSummary | null>(null);

  const reload = async () => {
    setLoading(true);
    try {
      const r = await reviewApi.listPublicTasks(tab);
      setItems(r.items);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void reload();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [tab]);

  const decide = async (task: TaskSummary, decision: "approve" | "reject" | "delist", reason?: string) => {
    try {
      await reviewApi.reviewPublicTask(task.id, decision, reason);
      pushToast("success", decision === "approve" ? "已批准上架" : decision === "reject" ? "已驳回" : "已下架");
      await reload();
    } catch (err) {
      pushToast("error", (err as Error).message);
    }
  };

  return (
    <div>
      <div className="adm-page-head">
        <h1>🌐 公共任务</h1>
        <p>团队共享的任务（开关 enable_public_task_review 决定是否需要审核）</p>
      </div>

      <div style={{ display: "flex", gap: 4, borderBottom: "1px solid var(--border)", marginBottom: 18 }}>
        {STATUS_TABS.map((t) => (
          <button
            key={t.k}
            onClick={() => setTab(t.k)}
            style={{
              background: "transparent",
              border: "none",
              padding: "10px 18px",
              fontSize: 13,
              cursor: "pointer",
              color: tab === t.k ? "var(--primary)" : "var(--text-dim)",
              borderBottom: tab === t.k ? "2px solid var(--primary)" : "2px solid transparent",
            }}
          >
            {t.label}
          </button>
        ))}
      </div>

      {loading ? (
        <Skeleton lines={6} />
      ) : items.length === 0 ? (
        <div className="adm-section" style={{ textAlign: "center", color: "var(--text-muted)" }}>
          {tab === "pending" ? "🎉 没有待审核的公共任务" : "暂无数据"}
        </div>
      ) : (
        <table className="adm-table">
          <thead>
            <tr>
              <th>任务名</th>
              <th>范式</th>
              <th>所有者</th>
              <th>消息预览</th>
              <th>更新时间</th>
              <th style={{ width: 240 }}>操作</th>
            </tr>
          </thead>
          <tbody>
            {items.map((t) => (
              <tr key={t.id}>
                <td>
                  <a onClick={() => navigate(`/workspace/${t.id}`)} style={{ cursor: "pointer" }}>
                    {t.name}
                  </a>
                </td>
                <td>
                  <span className="role-badge role-user">{t.paradigm}</span>
                </td>
                <td style={{ fontFamily: "var(--font-mono)", fontSize: 11 }}>{t.owner_id.slice(0, 8)}</td>
                <td
                  style={{
                    maxWidth: 320,
                    overflow: "hidden",
                    textOverflow: "ellipsis",
                    whiteSpace: "nowrap",
                    color: "var(--text-dim)",
                    fontSize: 12,
                  }}
                  title={t.last_message_preview || ""}
                >
                  {t.last_message_preview || "-"}
                </td>
                <td style={{ fontSize: 11, color: "var(--text-muted)" }}>
                  {t.updated_at ? new Date(t.updated_at).toLocaleString() : "-"}
                </td>
                <td className="row-actions">
                  {tab === "pending" && (
                    <>
                      <button onClick={() => setPendingApprove(t)}>✅ 批准上架</button>
                      <button className="danger" onClick={() => setPendingReject(t)}>
                        ✕ 驳回
                      </button>
                    </>
                  )}
                  {tab === "published" && (
                    <button className="danger" onClick={() => setPendingDelist(t)}>
                      🚫 下架
                    </button>
                  )}
                  {tab === "rejected" && (
                    <span style={{ fontSize: 11, color: "var(--text-muted)" }}>
                      已驳回{(t as any).review_reason ? `：${(t as any).review_reason}` : ""}
                    </span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      <ConfirmModal
        open={!!pendingApprove}
        title={`确认批准上架「${pendingApprove?.name}」？`}
        body="批准后所有用户在公共区可见此任务。"
        onConfirm={async () => {
          if (pendingApprove) await decide(pendingApprove, "approve");
          setPendingApprove(null);
        }}
        onCancel={() => setPendingApprove(null)}
      />

      {pendingReject && (
        <RejectWithReason
          title={`驳回「${pendingReject.name}」`}
          onClose={() => setPendingReject(null)}
          onConfirm={async (reason) => {
            await decide(pendingReject, "reject", reason);
            setPendingReject(null);
          }}
        />
      )}
      {pendingDelist && (
        <RejectWithReason
          title={`下架「${pendingDelist.name}」`}
          onClose={() => setPendingDelist(null)}
          onConfirm={async (reason) => {
            await decide(pendingDelist, "delist", reason);
            setPendingDelist(null);
          }}
        />
      )}
    </div>
  );
}

function RejectWithReason({
  title,
  onClose,
  onConfirm,
}: {
  title: string;
  onClose: () => void;
  onConfirm: (reason: string) => void | Promise<void>;
}) {
  const [reason, setReason] = useState("");
  return (
    <div className="cm-overlay" onClick={onClose}>
      <div className="cm-card" style={{ minWidth: 460 }} onClick={(e) => e.stopPropagation()}>
        <h3>{title}</h3>
        <div className="cm-body">
          <label className="ct-field">
            <span>原因（必填）</span>
            <textarea
              rows={3}
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              placeholder="例如：包含敏感信息 / 内容不完整"
            />
          </label>
        </div>
        <div className="cm-actions">
          <button className="btn-secondary" onClick={onClose}>
            取消
          </button>
          <button className="cm-danger" disabled={!reason.trim()} onClick={() => onConfirm(reason.trim())}>
            确认
          </button>
        </div>
      </div>
    </div>
  );
}
