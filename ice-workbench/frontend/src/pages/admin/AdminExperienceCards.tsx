import { useEffect, useMemo, useState } from "react";
import { adminApi, reviewApi } from "@/api/endpoints";
import type { AdminAgent, ExperienceCard } from "@/api/endpoints";
import { ConfirmModal } from "@/components/feedback/ConfirmModal";
import { Skeleton } from "@/components/feedback/Skeleton";
import { useUIStore } from "@/stores/uiStore";

export function AdminExperienceCards() {
  const pushToast = useUIStore((s) => s.pushToast);
  const [items, setItems] = useState<ExperienceCard[]>([]);
  const [agents, setAgents] = useState<AdminAgent[]>([]);
  const [agentFilter, setAgentFilter] = useState<string>("");
  const [statusFilter, setStatusFilter] = useState<string>("draft");
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [loading, setLoading] = useState(true);
  const [confirmReject, setConfirmReject] = useState<ExperienceCard | null>(null);
  const [batchAction, setBatchAction] = useState<"approve" | "reject" | null>(null);
  const [rejectReason, setRejectReason] = useState("");

  const reload = async () => {
    setLoading(true);
    try {
      const r = await reviewApi.listCards({
        status: statusFilter || undefined,
        agent_id: agentFilter || undefined,
      });
      setItems(r.items);
      setSelected(new Set());
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void reload();
    adminApi.listAgents().then((r) => setAgents(r.items)).catch(() => {});
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [statusFilter, agentFilter]);

  const agentName = useMemo(() => {
    const m: Record<string, string> = {};
    agents.forEach((a) => (m[a.id] = `${a.icon} ${a.name}`));
    return m;
  }, [agents]);

  const toggle = (id: string) => {
    const next = new Set(selected);
    if (next.has(id)) next.delete(id);
    else next.add(id);
    setSelected(next);
  };

  const toggleAll = () => {
    if (selected.size === items.length) setSelected(new Set());
    else setSelected(new Set(items.map((c) => c.id)));
  };

  const reviewOne = async (
    card: ExperienceCard,
    status: "approved" | "rejected",
    reason?: string,
  ) => {
    try {
      await reviewApi.reviewCard(card.id, status, reason);
      pushToast("success", status === "approved" ? "已批准并注入 Agent" : "已驳回");
      await reload();
    } catch (err) {
      pushToast("error", (err as Error).message);
    }
  };

  const doBatch = async () => {
    if (!batchAction || selected.size === 0) return;
    const reason = batchAction === "reject" ? rejectReason : undefined;
    try {
      await reviewApi.batchReviewCards(
        Array.from(selected),
        batchAction === "approve" ? "approved" : "rejected",
        reason,
      );
      pushToast("success", `已${batchAction === "approve" ? "批准" : "驳回"} ${selected.size} 条`);
      setBatchAction(null);
      setRejectReason("");
      await reload();
    } catch (err) {
      pushToast("error", (err as Error).message);
    }
  };

  return (
    <div>
      <div className="adm-page-head">
        <h1>💡 经验卡片</h1>
        <p>批准后自动注入对应 Agent 的 system prompt（cards.md）</p>
      </div>

      <div className="adm-toolbar">
        <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)}>
          <option value="draft">待审批</option>
          <option value="approved">已批准</option>
          <option value="rejected">已驳回</option>
          <option value="">全部</option>
        </select>
        <select value={agentFilter} onChange={(e) => setAgentFilter(e.target.value)}>
          <option value="">全部 Agent</option>
          {agents.map((a) => (
            <option key={a.id} value={a.id}>
              {a.icon} {a.name}
            </option>
          ))}
        </select>
        <div style={{ flex: 1 }} />
        {selected.size > 0 && statusFilter === "draft" && (
          <>
            <button className="btn-primary" onClick={() => setBatchAction("approve")}>
              ✅ 批准选中（{selected.size}）
            </button>
            <button className="btn-secondary" onClick={() => setBatchAction("reject")}>
              ✕ 驳回选中
            </button>
          </>
        )}
      </div>

      {loading ? (
        <Skeleton lines={6} />
      ) : items.length === 0 ? (
        <div className="adm-section" style={{ textAlign: "center", color: "var(--text-muted)" }}>
          {statusFilter === "draft" ? "🎉 没有待审批的经验卡片" : "暂无数据"}
        </div>
      ) : (
        <table className="adm-table">
          <thead>
            <tr>
              {statusFilter === "draft" && (
                <th style={{ width: 30 }}>
                  <input type="checkbox" checked={selected.size === items.length} onChange={toggleAll} />
                </th>
              )}
              <th>Agent</th>
              <th>标题</th>
              <th>规则</th>
              <th>作者</th>
              <th>提交时间</th>
              <th style={{ width: 200 }}>操作</th>
            </tr>
          </thead>
          <tbody>
            {items.map((c) => (
              <tr key={c.id}>
                {statusFilter === "draft" && (
                  <td>
                    <input type="checkbox" checked={selected.has(c.id)} onChange={() => toggle(c.id)} />
                  </td>
                )}
                <td style={{ fontSize: 12 }}>{c.agent_id ? agentName[c.agent_id] || c.agent_id : "-"}</td>
                <td>{c.title}</td>
                <td
                  style={{
                    maxWidth: 360,
                    overflow: "hidden",
                    textOverflow: "ellipsis",
                    whiteSpace: "nowrap",
                    color: "var(--text-dim)",
                    fontSize: 12,
                  }}
                  title={c.rule}
                >
                  {c.rule}
                </td>
                <td style={{ fontSize: 11, color: "var(--text-muted)" }}>{c.author_id.slice(0, 8)}</td>
                <td style={{ fontSize: 11, color: "var(--text-muted)" }}>
                  {new Date(c.created_at).toLocaleString()}
                </td>
                <td className="row-actions">
                  {c.status === "draft" ? (
                    <>
                      <button onClick={() => reviewOne(c, "approved")}>✅ 批准</button>
                      <button className="danger" onClick={() => setConfirmReject(c)}>
                        ✕ 驳回
                      </button>
                    </>
                  ) : (
                    <span
                      style={{
                        color: c.status === "approved" ? "var(--success)" : "var(--text-muted)",
                        fontSize: 11,
                      }}
                    >
                      {c.status === "approved" ? "已批准" : `已驳回${c.reject_reason ? `：${c.reject_reason}` : ""}`}
                    </span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      {/* single reject modal */}
      {confirmReject && (
        <RejectModal
          title={`驳回卡片「${confirmReject.title}」`}
          onClose={() => setConfirmReject(null)}
          onConfirm={async (reason) => {
            await reviewOne(confirmReject, "rejected", reason);
            setConfirmReject(null);
          }}
        />
      )}

      {/* batch */}
      <ConfirmModal
        open={batchAction === "approve"}
        title={`确认批准 ${selected.size} 条经验卡片？`}
        body="批准后会自动写入对应 Agent 的 cards.md，下次对话生效。"
        onConfirm={doBatch}
        onCancel={() => setBatchAction(null)}
      />
      {batchAction === "reject" && (
        <RejectModal
          title={`驳回 ${selected.size} 条卡片`}
          onClose={() => setBatchAction(null)}
          onConfirm={async (reason) => {
            setRejectReason(reason);
            // setRejectReason 异步，直接传
            await reviewApi.batchReviewCards(Array.from(selected), "rejected", reason);
            pushToast("success", `已驳回 ${selected.size} 条`);
            setBatchAction(null);
            await reload();
          }}
        />
      )}
    </div>
  );
}

function RejectModal({
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
            <span>驳回原因（必填）</span>
            <textarea
              rows={3}
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              placeholder="例如：与已有规则重复 / 表达不准确"
            />
          </label>
        </div>
        <div className="cm-actions">
          <button className="btn-secondary" onClick={onClose}>
            取消
          </button>
          <button
            className="cm-danger"
            disabled={!reason.trim()}
            onClick={() => onConfirm(reason.trim())}
          >
            确认驳回
          </button>
        </div>
      </div>
    </div>
  );
}
