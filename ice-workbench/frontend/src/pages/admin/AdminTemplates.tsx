import { useEffect, useState } from "react";
import { adminTemplateApi } from "@/api/endpoints";
import type { TemplateRecord } from "@/api/endpoints";
import { ConfirmModal } from "@/components/feedback/ConfirmModal";
import { Skeleton } from "@/components/feedback/Skeleton";
import { useUIStore } from "@/stores/uiStore";

const STATUS_TABS = [
  { k: "draft", label: "待审核" },
  { k: "approved", label: "已批准" },
  { k: "rejected", label: "已驳回" },
  { k: "all", label: "全部" },
] as const;

export function AdminTemplates() {
  const pushToast = useUIStore((s) => s.pushToast);
  const [tab, setTab] = useState<(typeof STATUS_TABS)[number]["k"]>("draft");
  const [items, setItems] = useState<TemplateRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [pendingReject, setPendingReject] = useState<TemplateRecord | null>(null);
  const [confirmDelete, setConfirmDelete] = useState<TemplateRecord | null>(null);
  const [active, setActive] = useState<TemplateRecord | null>(null);
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [confirmBatchApprove, setConfirmBatchApprove] = useState(false);
  const [batchRunning, setBatchRunning] = useState(false);

  const reload = async () => {
    setLoading(true);
    try {
      const r = await adminTemplateApi.list(tab === "all" ? undefined : tab, "public");
      setItems(r.items);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void reload();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [tab]);

  const review = async (
    t: TemplateRecord,
    status: "approved" | "rejected",
    reason?: string,
  ) => {
    try {
      await adminTemplateApi.review(t.id, status, reason);
      pushToast("success", status === "approved" ? "已批准" : "已驳回");
      await reload();
    } catch (err) {
      pushToast("error", (err as Error).message);
    }
  };

  // tab 切换时清空选择
  useEffect(() => {
    setSelected(new Set());
  }, [tab]);

  const toggle = (id: string) => {
    const next = new Set(selected);
    if (next.has(id)) next.delete(id);
    else next.add(id);
    setSelected(next);
  };

  const draftItems = items.filter((t) => t.status === "draft");

  const toggleAll = () => {
    if (selected.size === draftItems.length) setSelected(new Set());
    else setSelected(new Set(draftItems.map((t) => t.id)));
  };

  const batchApprove = async () => {
    if (selected.size === 0) return;
    setBatchRunning(true);
    const ids = Array.from(selected);
    const results = await Promise.allSettled(
      ids.map((id) => adminTemplateApi.review(id, "approved")),
    );
    const ok = results.filter((r) => r.status === "fulfilled").length;
    const fail = ids.length - ok;
    setBatchRunning(false);
    setConfirmBatchApprove(false);
    setSelected(new Set());
    pushToast(
      fail === 0 ? "success" : "warning",
      fail === 0 ? `已批准 ${ok} 条` : `批准 ${ok} 条，${fail} 条失败`,
    );
    await reload();
  };

  const remove = async (t: TemplateRecord) => {
    try {
      await adminTemplateApi.remove(t.id);
      pushToast("success", "已删除");
      await reload();
    } catch (err) {
      pushToast("error", (err as Error).message);
    } finally {
      setConfirmDelete(null);
    }
  };

  return (
    <div>
      <div className="adm-page-head">
        <h1>📋 任务模板</h1>
        <p>用户提交的公共模板（visibility=public 的部分需审核）</p>
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

      {tab === "draft" && selected.size > 0 && (
        <div style={{ display: "flex", gap: 8, alignItems: "center", marginBottom: 12 }}>
          <span style={{ color: "var(--text-dim)", fontSize: 13 }}>
            已选 {selected.size} 条
          </span>
          <button
            className="btn-primary"
            disabled={batchRunning}
            onClick={() => setConfirmBatchApprove(true)}
          >
            ✅ 批量批准（{selected.size}）
          </button>
          <button className="btn-ghost" onClick={() => setSelected(new Set())}>
            取消选择
          </button>
        </div>
      )}

      {loading ? (
        <Skeleton lines={6} />
      ) : items.length === 0 ? (
        <div className="adm-section" style={{ textAlign: "center", color: "var(--text-muted)" }}>
          {tab === "draft" ? "🎉 没有待审核的模板" : "暂无数据"}
        </div>
      ) : (
        <table className="adm-table">
          <thead>
            <tr>
              {tab === "draft" && (
                <th style={{ width: 32 }}>
                  <input
                    type="checkbox"
                    checked={draftItems.length > 0 && selected.size === draftItems.length}
                    onChange={toggleAll}
                    title="全选待审核"
                  />
                </th>
              )}
              <th>名称</th>
              <th>范式</th>
              <th>Agent</th>
              <th>定时</th>
              <th>状态</th>
              <th>更新时间</th>
              <th style={{ width: 220 }}>操作</th>
            </tr>
          </thead>
          <tbody>
            {items.map((t) => (
              <tr key={t.id}>
                {tab === "draft" && (
                  <td>
                    {t.status === "draft" && (
                      <input
                        type="checkbox"
                        checked={selected.has(t.id)}
                        onChange={() => toggle(t.id)}
                      />
                    )}
                  </td>
                )}
                <td>
                  <a onClick={() => setActive(t)} style={{ cursor: "pointer" }}>
                    {t.name}
                  </a>
                </td>
                <td>
                  <span className="role-badge role-user">{t.paradigm}</span>
                </td>
                <td style={{ fontSize: 12 }}>{t.agent_id || "-"}</td>
                <td>{t.has_schedule ? "⏱" : "—"}</td>
                <td
                  style={{
                    color:
                      t.status === "approved"
                        ? "var(--success)"
                        : t.status === "rejected"
                          ? "var(--error)"
                          : "var(--warning)",
                    fontSize: 11,
                  }}
                >
                  {t.status}
                  {t.reject_reason ? ` · ${t.reject_reason}` : ""}
                </td>
                <td style={{ fontSize: 11, color: "var(--text-muted)" }}>
                  {new Date(t.updated_at).toLocaleString()}
                </td>
                <td className="row-actions">
                  {t.status === "draft" && (
                    <>
                      <button onClick={() => review(t, "approved")}>✅ 批准</button>
                      <button className="danger" onClick={() => setPendingReject(t)}>
                        ✕ 驳回
                      </button>
                    </>
                  )}
                  <button onClick={() => setActive(t)}>👁 详情</button>
                  <button className="danger" onClick={() => setConfirmDelete(t)}>
                    🗑
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      <ConfirmModal
        open={confirmBatchApprove}
        title={`批量批准 ${selected.size} 条模板？`}
        body={<>将同时发布 {selected.size} 条模板到公共区。此操作可在列表中逐条驳回。</>}
        confirmText={batchRunning ? "处理中…" : "批量批准"}
        onConfirm={batchApprove}
        onCancel={() => setConfirmBatchApprove(false)}
      />

      {active && <TemplateDetailModal template={active} onClose={() => setActive(null)} />}
      {pendingReject && (
        <RejectModal
          title={`驳回「${pendingReject.name}」`}
          onClose={() => setPendingReject(null)}
          onConfirm={async (reason) => {
            await review(pendingReject, "rejected", reason);
            setPendingReject(null);
          }}
        />
      )}
      <ConfirmModal
        open={!!confirmDelete}
        title={`确认删除模板「${confirmDelete?.name}」？`}
        danger
        onConfirm={() => confirmDelete && remove(confirmDelete)}
        onCancel={() => setConfirmDelete(null)}
      />
    </div>
  );
}

function TemplateDetailModal({
  template,
  onClose,
}: {
  template: TemplateRecord;
  onClose: () => void;
}) {
  return (
    <div className="cm-overlay" onClick={onClose}>
      <div className="cm-card" style={{ minWidth: 560, maxWidth: "70vw" }} onClick={(e) => e.stopPropagation()}>
        <h3>{template.name}</h3>
        <div className="cm-body" style={{ display: "flex", flexDirection: "column", gap: 12 }}>
          <KV label="范式" v={template.paradigm} />
          <KV label="可见性" v={template.visibility} />
          <KV label="Agent" v={template.agent_id || "-"} />
          <KV label="Skills" v={template.skill_ids.join(", ") || "-"} />
          <KV label="定时" v={template.has_schedule ? JSON.stringify(template.schedule_config) : "无"} />
          {template.description && <KV label="描述" v={template.description} />}
          {template.initial_prompt && (
            <div>
              <div style={{ fontSize: 12, color: "var(--text-muted)", marginBottom: 4 }}>初始 Prompt</div>
              <pre
                style={{
                  background: "var(--surface-2)",
                  border: "1px solid var(--border)",
                  borderRadius: 6,
                  padding: 10,
                  fontSize: 12,
                  whiteSpace: "pre-wrap",
                  margin: 0,
                }}
              >
                {template.initial_prompt}
              </pre>
            </div>
          )}
        </div>
        <div className="cm-actions">
          <button className="btn-primary" onClick={onClose}>
            关闭
          </button>
        </div>
      </div>
    </div>
  );
}

function KV({ label, v }: { label: string; v: React.ReactNode }) {
  return (
    <div style={{ display: "flex", gap: 12, fontSize: 13 }}>
      <span style={{ minWidth: 80, color: "var(--text-muted)" }}>{label}</span>
      <span>{v}</span>
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
            <textarea rows={3} value={reason} onChange={(e) => setReason(e.target.value)} />
          </label>
        </div>
        <div className="cm-actions">
          <button className="btn-secondary" onClick={onClose}>
            取消
          </button>
          <button className="cm-danger" disabled={!reason.trim()} onClick={() => onConfirm(reason.trim())}>
            确认驳回
          </button>
        </div>
      </div>
    </div>
  );
}
