import { useEffect, useState } from "react";
import { adminKBApi } from "@/api/endpoints";
import type { KBRecord, KBSyncLog } from "@/api/endpoints";
import { ConfirmModal } from "@/components/feedback/ConfirmModal";
import { Skeleton } from "@/components/feedback/Skeleton";
import { useUIStore } from "@/stores/uiStore";

export function AdminKnowledgeBases() {
  const pushToast = useUIStore((s) => s.pushToast);
  const [items, setItems] = useState<KBRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [editing, setEditing] = useState<KBRecord | null>(null);
  const [creating, setCreating] = useState(false);
  const [confirmDelete, setConfirmDelete] = useState<KBRecord | null>(null);
  const [logsFor, setLogsFor] = useState<KBRecord | null>(null);

  const reload = async () => {
    setLoading(true);
    try {
      const r = await adminKBApi.list();
      setItems(r.items);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void reload();
  }, []);

  const sync = async (kb: KBRecord) => {
    pushToast("info", `正在同步 ${kb.name}…`);
    try {
      const log = await adminKBApi.sync(kb.id);
      pushToast(
        log.status === "success" ? "success" : "error",
        log.status === "success"
          ? `同步成功：+${log.added} / ~${log.updated}`
          : `同步失败：${log.error?.message || "未知"}`,
      );
      await reload();
    } catch (err) {
      pushToast("error", (err as Error).message);
    }
  };

  const test = async (kb: KBRecord) => {
    try {
      const r = await adminKBApi.testConnection(kb.id);
      pushToast(r.ok ? "success" : "error", r.message || (r.ok ? "连接成功" : "连接失败"));
    } catch (err) {
      pushToast("error", (err as Error).message);
    }
  };

  const remove = async (kb: KBRecord) => {
    try {
      await adminKBApi.remove(kb.id);
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
      <div className="adm-page-head" style={{ display: "flex", justifyContent: "space-between" }}>
        <div>
          <h1>📚 知识库</h1>
          <p>飞书 Wiki / Mify RAG 数据源，按频率自动同步</p>
        </div>
        <button className="btn-primary" onClick={() => setCreating(true)}>
          + 新建知识库
        </button>
      </div>

      {loading ? (
        <Skeleton lines={6} />
      ) : items.length === 0 ? (
        <div className="adm-section" style={{ textAlign: "center", color: "var(--text-muted)" }}>
          还没有知识库。点击右上角新建。
        </div>
      ) : (
        <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
          {items.map((kb) => (
            <div key={kb.id} className="adm-section" style={{ padding: 16 }}>
              <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
                <span style={{ fontSize: 22 }}>{kb.source_type === "feishu_wiki" ? "🪶" : "📚"}</span>
                <div style={{ flex: 1 }}>
                  <div style={{ fontFamily: "var(--font-head)", fontSize: 14, fontWeight: 600 }}>
                    {kb.name}
                    <span style={{ fontSize: 10, color: "var(--text-muted)", marginLeft: 8 }}>
                      {kb.source_type}
                    </span>
                  </div>
                  <div style={{ fontSize: 12, color: "var(--text-dim)" }}>
                    {kb.description || "(无描述)"}
                  </div>
                </div>
                <span
                  style={{
                    fontSize: 11,
                    padding: "2px 8px",
                    borderRadius: 4,
                    background: kb.enabled ? "var(--success-dim)" : "var(--surface-3)",
                    color: kb.enabled ? "var(--success)" : "var(--text-muted)",
                  }}
                >
                  {kb.enabled ? "已启用" : "已停用"}
                </span>
              </div>
              <div
                style={{
                  display: "grid",
                  gridTemplateColumns: "repeat(auto-fit, minmax(160px, 1fr))",
                  gap: 12,
                  marginTop: 12,
                  fontSize: 12,
                }}
              >
                <KV label="频率" v={kb.sync_frequency} />
                <KV label="文档数" v={kb.doc_count} />
                <KV label="上次同步" v={kb.last_sync_at ? new Date(kb.last_sync_at).toLocaleString() : "从未"} />
                <KV
                  label="上次结果"
                  v={
                    kb.last_sync_summary ? (
                      <span
                        style={{
                          color:
                            kb.last_sync_summary.status === "success"
                              ? "var(--success)"
                              : "var(--error)",
                        }}
                      >
                        {kb.last_sync_summary.status} · +{kb.last_sync_summary.added}
                      </span>
                    ) : (
                      "-"
                    )
                  }
                />
              </div>
              <div style={{ display: "flex", gap: 8, marginTop: 12, justifyContent: "flex-end" }}>
                <button className="btn-ghost" onClick={() => test(kb)}>
                  🔌 测试连接
                </button>
                <button className="btn-ghost" onClick={() => setLogsFor(kb)}>
                  📜 同步日志
                </button>
                <button className="btn-secondary" onClick={() => setEditing(kb)}>
                  ✏ 编辑
                </button>
                <button className="btn-secondary" onClick={() => sync(kb)}>
                  🔄 立即同步
                </button>
                <button
                  className="btn-secondary"
                  onClick={() => setConfirmDelete(kb)}
                  style={{ color: "var(--error)", borderColor: "var(--error)" }}
                >
                  🗑 删除
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {(creating || editing) && (
        <KBModal
          existing={editing}
          onClose={() => {
            setCreating(false);
            setEditing(null);
          }}
          onSaved={async () => {
            setCreating(false);
            setEditing(null);
            await reload();
          }}
        />
      )}
      {logsFor && <SyncLogsModal kb={logsFor} onClose={() => setLogsFor(null)} />}
      <ConfirmModal
        open={!!confirmDelete}
        title={`确认删除知识库「${confirmDelete?.name}」？`}
        body="同步日志会保留在文件系统中。"
        danger
        onConfirm={() => confirmDelete && remove(confirmDelete)}
        onCancel={() => setConfirmDelete(null)}
      />
    </div>
  );
}

function KV({ label, v }: { label: string; v: React.ReactNode }) {
  return (
    <div>
      <span style={{ display: "block", color: "var(--text-muted)", fontSize: 10, textTransform: "uppercase", letterSpacing: 1, marginBottom: 2 }}>
        {label}
      </span>
      <span>{v}</span>
    </div>
  );
}

function KBModal({
  existing,
  onClose,
  onSaved,
}: {
  existing: KBRecord | null;
  onClose: () => void;
  onSaved: () => void | Promise<void>;
}) {
  const pushToast = useUIStore((s) => s.pushToast);
  const [form, setForm] = useState({
    name: existing?.name || "",
    description: existing?.description || "",
    source_type: (existing?.source_type || "feishu_wiki") as KBRecord["source_type"],
    config: JSON.stringify(existing?.config || { space_id: "" }, null, 2),
    sync_frequency: existing?.sync_frequency || "daily",
    visibility: existing?.visibility || "all",
    enabled: existing?.enabled ?? true,
  });
  const [saving, setSaving] = useState(false);

  const save = async () => {
    if (!form.name.trim()) return pushToast("warning", "请填写名称");
    let cfg: Record<string, unknown>;
    try {
      cfg = JSON.parse(form.config);
    } catch (e) {
      return pushToast("error", `config JSON 解析失败：${(e as Error).message}`);
    }
    setSaving(true);
    try {
      if (existing) {
        await adminKBApi.update(existing.id, {
          name: form.name,
          description: form.description,
          config: cfg as any,
          sync_frequency: form.sync_frequency,
          visibility: form.visibility,
          enabled: form.enabled,
        });
      } else {
        await adminKBApi.create({
          name: form.name,
          description: form.description,
          source_type: form.source_type,
          config: cfg as any,
          sync_frequency: form.sync_frequency,
          visibility: form.visibility,
          enabled: form.enabled,
        });
      }
      pushToast("success", "已保存");
      await onSaved();
    } catch (err) {
      pushToast("error", (err as Error).message);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="cm-overlay" onClick={onClose}>
      <div className="cm-card" style={{ minWidth: 560 }} onClick={(e) => e.stopPropagation()}>
        <h3>{existing ? "编辑知识库" : "新建知识库"}</h3>
        <div className="cm-body" style={{ display: "flex", flexDirection: "column", gap: 10 }}>
          <label className="ct-field">
            <span>名称</span>
            <input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
          </label>
          <label className="ct-field">
            <span>描述</span>
            <input
              value={form.description}
              onChange={(e) => setForm({ ...form, description: e.target.value })}
            />
          </label>
          <div className="adm-form-grid">
            <label>
              数据源
              <select
                value={form.source_type}
                onChange={(e) => setForm({ ...form, source_type: e.target.value as any })}
                disabled={!!existing}
              >
                <option value="feishu_wiki">飞书 Wiki</option>
                <option value="mify_rag">Mify RAG</option>
              </select>
            </label>
            <label>
              同步频率
              <select
                value={form.sync_frequency}
                onChange={(e) => setForm({ ...form, sync_frequency: e.target.value as any })}
              >
                <option value="manual">手动</option>
                <option value="hourly">每小时</option>
                <option value="daily">每日</option>
                <option value="weekly">每周</option>
              </select>
            </label>
          </div>
          <label className="ct-field">
            <span>config (JSON)</span>
            <textarea
              rows={5}
              value={form.config}
              onChange={(e) => setForm({ ...form, config: e.target.value })}
              style={{ fontFamily: "var(--font-mono)" }}
              placeholder={form.source_type === "feishu_wiki" ? '{"space_id":"xxx"}' : '{"dataset_id":"xxx"}'}
            />
          </label>
          <label className="ct-toggle">
            <input
              type="checkbox"
              checked={form.enabled}
              onChange={(e) => setForm({ ...form, enabled: e.target.checked })}
            />
            启用
          </label>
        </div>
        <div className="cm-actions">
          <button className="btn-secondary" onClick={onClose}>
            取消
          </button>
          <button className="btn-primary" disabled={saving} onClick={save}>
            {saving ? "保存中…" : "保存"}
          </button>
        </div>
      </div>
    </div>
  );
}

function SyncLogsModal({ kb, onClose }: { kb: KBRecord; onClose: () => void }) {
  const [logs, setLogs] = useState<KBSyncLog[] | null>(null);
  useEffect(() => {
    adminKBApi.syncLogs(kb.id).then((r) => setLogs(r.items));
  }, [kb.id]);
  return (
    <div className="cm-overlay" onClick={onClose}>
      <div className="cm-card" style={{ minWidth: 640, maxWidth: "80vw" }} onClick={(e) => e.stopPropagation()}>
        <h3>📜 同步日志：{kb.name}</h3>
        <div className="cm-body">
          {logs === null ? (
            <Skeleton lines={5} />
          ) : logs.length === 0 ? (
            <div style={{ color: "var(--text-muted)", textAlign: "center", padding: 20 }}>暂无日志</div>
          ) : (
            <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
              {logs.map((l) => (
                <details
                  key={l.id}
                  style={{
                    background: "var(--surface-2)",
                    border: "1px solid var(--border)",
                    borderRadius: 6,
                  }}
                >
                  <summary style={{ padding: "8px 12px", cursor: "pointer", fontSize: 12, display: "flex", gap: 10 }}>
                    <span
                      style={{
                        color:
                          l.status === "success"
                            ? "var(--success)"
                            : l.status === "running"
                              ? "var(--warning)"
                              : "var(--error)",
                      }}
                    >
                      {l.status}
                    </span>
                    <span style={{ fontFamily: "var(--font-mono)", color: "var(--text-muted)" }}>
                      {new Date(l.started_at).toLocaleString()}
                    </span>
                    <span style={{ marginLeft: "auto" }}>
                      +{l.added} ~{l.updated} {l.failed > 0 && `失败 ${l.failed}`}
                    </span>
                    <span style={{ color: "var(--text-muted)" }}>{l.trigger}</span>
                  </summary>
                  {l.error && (
                    <div style={{ padding: 10, fontSize: 11, color: "var(--error)" }}>
                      [{l.error.code}] {l.error.message}
                    </div>
                  )}
                </details>
              ))}
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
