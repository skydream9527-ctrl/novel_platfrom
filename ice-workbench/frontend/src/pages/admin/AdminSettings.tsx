import { useEffect, useState } from "react";
import { settingsApi } from "@/api/endpoints";
import type {
  Announcement,
  LLMConfig,
  LLMModel,
  SystemParams,
  Toggles,
} from "@/api/endpoints";
import { ConfirmModal } from "@/components/feedback/ConfirmModal";
import { Skeleton } from "@/components/feedback/Skeleton";
import { useAuthStore } from "@/stores/authStore";
import { useUIStore } from "@/stores/uiStore";

interface TabDef {
  k: "toggles" | "llm" | "params" | "announcements";
  label: string;
  lock?: boolean;
}
const TABS: TabDef[] = [
  { k: "toggles", label: "全局开关", lock: true },
  { k: "llm", label: "LLM 模型" },
  { k: "params", label: "系统参数" },
  { k: "announcements", label: "公告管理" },
];
type Tab = TabDef["k"];

export function AdminSettings() {
  const me = useAuthStore((s) => s.user);
  const isSuper = me?.auth_role === "super_admin";
  const pushToast = useUIStore((s) => s.pushToast);

  const [tab, setTab] = useState<Tab>("toggles");
  const [toggles, setToggles] = useState<Toggles | null>(null);
  const [params, setParams] = useState<SystemParams | null>(null);
  const [llm, setLlm] = useState<LLMConfig | null>(null);
  const [announcements, setAnnouncements] = useState<Announcement[]>([]);

  const reload = async () => {
    const r = await settingsApi.read();
    setToggles(r.toggles);
    setParams(r.system_params);
    setLlm(r.llm);
    setAnnouncements(r.announcements);
  };

  useEffect(() => {
    void reload().catch((e) => pushToast("error", (e as Error).message));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <div>
      <div className="adm-page-head">
        <h1>⚙ 系统设置</h1>
        <p>
          全局开关与 LLM 预算需 <span style={{ color: "var(--agent)" }}>super_admin</span>；其他项 admin 可改。
        </p>
      </div>

      <div style={{ display: "flex", gap: 4, borderBottom: "1px solid var(--border)", marginBottom: 18 }}>
        {TABS.map((t) => (
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
            {t.label} {t.lock && !isSuper ? "🔒" : ""}
          </button>
        ))}
      </div>

      {tab === "toggles" && (
        toggles ? (
          <TogglesTab toggles={toggles} canEdit={isSuper} onSaved={reload} />
        ) : (
          <Skeleton lines={4} />
        )
      )}
      {tab === "llm" && (llm ? <LLMTab llm={llm} canEditBudget={isSuper} onSaved={reload} /> : <Skeleton lines={5} />)}
      {tab === "params" && (params ? <ParamsTab params={params} onSaved={reload} /> : <Skeleton lines={4} />)}
      {tab === "announcements" && <AnnouncementsTab items={announcements} onSaved={reload} />}
    </div>
  );
}

// ---- Toggles ----

function TogglesTab({
  toggles,
  canEdit,
  onSaved,
}: {
  toggles: Toggles;
  canEdit: boolean;
  onSaved: () => Promise<void>;
}) {
  const pushToast = useUIStore((s) => s.pushToast);
  const [pending, setPending] = useState<{ key: keyof Toggles; value: boolean } | null>(null);
  const labels: Record<keyof Toggles, { label: string; desc: string }> = {
    enable_open_register: {
      label: "开放注册",
      desc: "关闭后新用户必须由 admin 手工创建",
    },
    enable_public_task_review: {
      label: "公共任务审核制",
      desc: "开启后用户共享任务到公共区需 admin 审核",
    },
    enable_feishu_strict_whitelist: {
      label: "飞书严格白名单",
      desc: "开启后只有 users 表里已存在的邮箱可飞书登录（与下面自动注册互斥）",
    },
    enable_feishu_auto_register: {
      label: "飞书首次登录自动建号",
      desc: "默认开启：用户用飞书登录时若本地没账号，自动 auto_role=user 建一个；关闭则报 FEISHU_ACCOUNT_NOT_WHITELISTED",
    },
  };

  const apply = async () => {
    if (!pending) return;
    try {
      await settingsApi.updateToggles({ [pending.key]: pending.value });
      pushToast("success", "已保存");
      await onSaved();
    } catch (err) {
      pushToast("error", (err as Error).message);
    } finally {
      setPending(null);
    }
  };

  return (
    <div className="adm-section">
      <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
        {(Object.keys(labels) as (keyof Toggles)[]).map((k) => (
          <div
            key={k}
            style={{
              display: "flex",
              alignItems: "center",
              gap: 12,
              padding: "12px 14px",
              background: "var(--surface-2)",
              border: "1px solid var(--border)",
              borderRadius: 8,
            }}
          >
            <div style={{ flex: 1 }}>
              <div style={{ fontSize: 13, fontWeight: 500 }}>{labels[k].label}</div>
              <div style={{ fontSize: 11, color: "var(--text-muted)", marginTop: 2 }}>{labels[k].desc}</div>
              <code
                style={{
                  fontSize: 10,
                  color: "var(--text-muted)",
                  fontFamily: "var(--font-mono)",
                  marginTop: 4,
                  display: "block",
                }}
              >
                {k}
              </code>
            </div>
            <ToggleSwitch
              on={toggles[k]}
              disabled={!canEdit}
              onChange={(v) => setPending({ key: k, value: v })}
            />
          </div>
        ))}
      </div>
      {!canEdit && (
        <p style={{ fontSize: 11, color: "var(--text-muted)", marginTop: 14 }}>仅 super_admin 可修改全局开关</p>
      )}
      <ConfirmModal
        open={!!pending}
        title={`确认${pending?.value ? "开启" : "关闭"}「${pending && labels[pending.key].label}」？`}
        body="该开关会影响平台行为。"
        onConfirm={apply}
        onCancel={() => setPending(null)}
      />
    </div>
  );
}

function ToggleSwitch({
  on,
  disabled,
  onChange,
}: {
  on: boolean;
  disabled?: boolean;
  onChange: (v: boolean) => void;
}) {
  return (
    <button
      onClick={() => !disabled && onChange(!on)}
      disabled={disabled}
      style={{
        width: 38,
        height: 22,
        borderRadius: 11,
        background: on ? "var(--success)" : "var(--surface-3)",
        border: "1px solid var(--border)",
        position: "relative",
        cursor: disabled ? "not-allowed" : "pointer",
        opacity: disabled ? 0.6 : 1,
        transition: "background .15s",
      }}
      aria-label="toggle"
    >
      <span
        style={{
          position: "absolute",
          width: 16,
          height: 16,
          background: "#fff",
          borderRadius: "50%",
          top: 2,
          left: on ? 18 : 2,
          transition: "left .15s",
        }}
      />
    </button>
  );
}

// ---- LLM ----

function LLMTab({
  llm,
  canEditBudget,
  onSaved,
}: {
  llm: LLMConfig;
  canEditBudget: boolean;
  onSaved: () => Promise<void>;
}) {
  const pushToast = useUIStore((s) => s.pushToast);
  const [budget, setBudget] = useState(llm.budget_monthly_usd);
  const [threshold, setThreshold] = useState(llm.budget_alert_threshold);
  const [editing, setEditing] = useState<LLMModel | null>(null);

  const saveBudget = async () => {
    try {
      await settingsApi.updateBudget(budget, threshold);
      pushToast("success", "预算已更新");
      await onSaved();
    } catch (err) {
      pushToast("error", (err as Error).message);
    }
  };

  const saveModel = async (m: LLMModel) => {
    try {
      await settingsApi.updateModel(m.id, m);
      pushToast("success", "模型已保存");
      setEditing(null);
      await onSaved();
    } catch (err) {
      pushToast("error", (err as Error).message);
    }
  };

  return (
    <div className="adm-section">
      <h3 style={{ fontFamily: "var(--font-head)", fontSize: 14, marginTop: 0 }}>月度预算（USD）</h3>
      <div className="adm-form-grid">
        <label>
          预算上限
          <input
            type="number"
            step="1"
            value={budget}
            disabled={!canEditBudget}
            onChange={(e) => setBudget(Number(e.target.value))}
          />
        </label>
        <label>
          告警阈值（0-1）
          <input
            type="number"
            step="0.05"
            min="0.1"
            max="1"
            value={threshold}
            disabled={!canEditBudget}
            onChange={(e) => setThreshold(Number(e.target.value))}
          />
        </label>
      </div>
      {canEditBudget && (
        <div style={{ marginTop: 10, textAlign: "right" }}>
          <button className="btn-primary" onClick={saveBudget}>
            💾 保存预算
          </button>
        </div>
      )}

      <h3 style={{ fontFamily: "var(--font-head)", fontSize: 14, marginTop: 24 }}>模型与单价（USD / 1M tokens）</h3>
      <table className="adm-table">
        <thead>
          <tr>
            <th>ID</th>
            <th>显示名</th>
            <th style={{ textAlign: "right" }}>输入</th>
            <th style={{ textAlign: "right" }}>输出</th>
            <th>启用</th>
            <th style={{ width: 100 }}>操作</th>
          </tr>
        </thead>
        <tbody>
          {llm.models.map((m) => (
            <tr key={m.id}>
              <td style={{ fontFamily: "var(--font-mono)", fontSize: 12 }}>{m.id}</td>
              <td>{m.label}</td>
              <td style={{ textAlign: "right", fontFamily: "var(--font-mono)" }}>${m.input_unit_price.toFixed(2)}</td>
              <td style={{ textAlign: "right", fontFamily: "var(--font-mono)" }}>${m.output_unit_price.toFixed(2)}</td>
              <td>{m.enabled ? "✅" : "—"}</td>
              <td>
                <button className="btn-ghost" onClick={() => setEditing({ ...m })} style={{ fontSize: 11 }}>
                  编辑
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      {editing && (
        <ModelEditModal
          model={editing}
          onClose={() => setEditing(null)}
          onSave={saveModel}
        />
      )}
    </div>
  );
}

function ModelEditModal({
  model,
  onClose,
  onSave,
}: {
  model: LLMModel;
  onClose: () => void;
  onSave: (m: LLMModel) => void;
}) {
  const [m, setM] = useState(model);
  return (
    <div className="cm-overlay" onClick={onClose}>
      <div className="cm-card" style={{ minWidth: 480 }} onClick={(e) => e.stopPropagation()}>
        <h3>编辑 {model.id}</h3>
        <div className="cm-body">
          <div className="adm-form-grid">
            <label>
              显示名
              <input value={m.label} onChange={(e) => setM({ ...m, label: e.target.value })} />
            </label>
            <label>
              启用
              <select
                value={m.enabled ? "1" : "0"}
                onChange={(e) => setM({ ...m, enabled: e.target.value === "1" })}
              >
                <option value="1">启用</option>
                <option value="0">禁用</option>
              </select>
            </label>
            <label>
              输入单价 USD/1M
              <input
                type="number"
                step="0.01"
                value={m.input_unit_price}
                onChange={(e) => setM({ ...m, input_unit_price: Number(e.target.value) })}
              />
            </label>
            <label>
              输出单价 USD/1M
              <input
                type="number"
                step="0.01"
                value={m.output_unit_price}
                onChange={(e) => setM({ ...m, output_unit_price: Number(e.target.value) })}
              />
            </label>
          </div>
        </div>
        <div className="cm-actions">
          <button className="btn-secondary" onClick={onClose}>
            取消
          </button>
          <button className="btn-primary" onClick={() => onSave(m)}>
            保存
          </button>
        </div>
      </div>
    </div>
  );
}

// ---- Params ----

function ParamsTab({ params, onSaved }: { params: SystemParams; onSaved: () => Promise<void> }) {
  const pushToast = useUIStore((s) => s.pushToast);
  const [form, setForm] = useState(params);
  const [confirmReset, setConfirmReset] = useState(false);

  const save = async () => {
    try {
      await settingsApi.updateSystemParams(form);
      pushToast("success", "已保存");
      await onSaved();
    } catch (err) {
      pushToast("error", (err as Error).message);
    }
  };

  const reset = async () => {
    try {
      const r = await settingsApi.resetSystemParams();
      setForm(r);
      pushToast("success", "已恢复默认");
      await onSaved();
    } catch (err) {
      pushToast("error", (err as Error).message);
    } finally {
      setConfirmReset(false);
    }
  };

  return (
    <div className="adm-section">
      <div className="adm-form-grid">
        <NumField
          label="单文件上传上限 (MB)"
          val={form.upload_max_size_mb}
          onChange={(v) => setForm({ ...form, upload_max_size_mb: v })}
        />
        <NumField
          label="单文件硬上限 (MB)"
          val={form.upload_max_size_hard_cap_mb}
          onChange={(v) => setForm({ ...form, upload_max_size_hard_cap_mb: v })}
        />
        <NumField
          label="对话上下文条数"
          val={form.context_size}
          onChange={(v) => setForm({ ...form, context_size: v })}
        />
        <NumField
          label="Tool Calling 最大轮数"
          val={form.tool_call_max_rounds}
          onChange={(v) => setForm({ ...form, tool_call_max_rounds: v })}
        />
        <NumField
          label="Tool 超时 (秒)"
          val={form.tool_call_timeout_s}
          onChange={(v) => setForm({ ...form, tool_call_timeout_s: v })}
        />
      </div>
      <div style={{ display: "flex", gap: 10, justifyContent: "flex-end", marginTop: 16 }}>
        <button className="btn-secondary" onClick={() => setConfirmReset(true)}>
          ⟲ 恢复默认
        </button>
        <button className="btn-primary" onClick={save}>
          💾 保存
        </button>
      </div>
      <ConfirmModal
        open={confirmReset}
        title="确认恢复所有系统参数到默认值？"
        body="将覆盖你当前的所有自定义。"
        onConfirm={reset}
        onCancel={() => setConfirmReset(false)}
      />
    </div>
  );
}

function NumField({
  label,
  val,
  onChange,
}: {
  label: string;
  val: number;
  onChange: (v: number) => void;
}) {
  return (
    <label>
      {label}
      <input type="number" value={val} onChange={(e) => onChange(Number(e.target.value))} />
    </label>
  );
}

// ---- Announcements ----

function AnnouncementsTab({
  items,
  onSaved,
}: {
  items: Announcement[];
  onSaved: () => Promise<void>;
}) {
  const pushToast = useUIStore((s) => s.pushToast);
  const [editing, setEditing] = useState<Announcement | null>(null);
  const [creating, setCreating] = useState(false);
  const [confirmDelete, setConfirmDelete] = useState<Announcement | null>(null);

  const remove = async (a: Announcement) => {
    try {
      await settingsApi.deleteAnnouncement(a.id);
      pushToast("success", "已删除");
      await onSaved();
    } catch (err) {
      pushToast("error", (err as Error).message);
    } finally {
      setConfirmDelete(null);
    }
  };

  return (
    <div className="adm-section">
      <div style={{ display: "flex", justifyContent: "flex-end", marginBottom: 12 }}>
        <button className="btn-primary" onClick={() => setCreating(true)}>
          + 新建公告
        </button>
      </div>
      {items.length === 0 ? (
        <div style={{ textAlign: "center", color: "var(--text-muted)", padding: 24 }}>
          暂无公告
        </div>
      ) : (
        <table className="adm-table">
          <thead>
            <tr>
              <th>标题</th>
              <th>级别</th>
              <th>受众</th>
              <th>状态</th>
              <th>更新时间</th>
              <th style={{ width: 140 }}>操作</th>
            </tr>
          </thead>
          <tbody>
            {items.map((a) => (
              <tr key={a.id}>
                <td>{a.title}</td>
                <td>
                  <span
                    className="role-badge"
                    style={{
                      background:
                        a.level === "error"
                          ? "var(--error-dim)"
                          : a.level === "warning"
                            ? "var(--warning-dim)"
                            : "var(--info-dim)",
                      color:
                        a.level === "error"
                          ? "var(--error)"
                          : a.level === "warning"
                            ? "var(--warning)"
                            : "var(--info)",
                    }}
                  >
                    {a.level}
                  </span>
                </td>
                <td>{a.audience_scope}</td>
                <td style={{ color: a.status === "published" ? "var(--success)" : "var(--text-muted)" }}>
                  {a.status === "published" ? "已发布" : "草稿"}
                </td>
                <td style={{ fontSize: 11, color: "var(--text-muted)" }}>
                  {new Date(a.updated_at).toLocaleString()}
                </td>
                <td className="row-actions">
                  <button onClick={() => setEditing(a)}>编辑</button>
                  <button className="danger" onClick={() => setConfirmDelete(a)}>
                    删除
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
      {(creating || editing) && (
        <AnnouncementModal
          existing={editing}
          onClose={() => {
            setCreating(false);
            setEditing(null);
          }}
          onSaved={async () => {
            setCreating(false);
            setEditing(null);
            await onSaved();
          }}
        />
      )}
      <ConfirmModal
        open={!!confirmDelete}
        title={`确认删除公告「${confirmDelete?.title}」？`}
        danger
        onConfirm={() => confirmDelete && remove(confirmDelete)}
        onCancel={() => setConfirmDelete(null)}
      />
    </div>
  );
}

function AnnouncementModal({
  existing,
  onClose,
  onSaved,
}: {
  existing: Announcement | null;
  onClose: () => void;
  onSaved: () => Promise<void>;
}) {
  const pushToast = useUIStore((s) => s.pushToast);
  const [form, setForm] = useState({
    title: existing?.title || "",
    body: existing?.body || "",
    level: existing?.level || "info",
    audience_scope: existing?.audience_scope || "all",
    status: existing?.status || "draft",
  });
  const [saving, setSaving] = useState(false);

  const save = async () => {
    if (!form.title.trim()) return pushToast("warning", "请填写标题");
    setSaving(true);
    try {
      if (existing) {
        await settingsApi.updateAnnouncement(existing.id, form);
      } else {
        await settingsApi.createAnnouncement(form);
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
        <h3>{existing ? "编辑公告" : "新建公告"}</h3>
        <div className="cm-body" style={{ display: "flex", flexDirection: "column", gap: 10 }}>
          <label className="ct-field">
            <span>标题</span>
            <input value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} />
          </label>
          <label className="ct-field">
            <span>正文</span>
            <textarea
              rows={4}
              value={form.body}
              onChange={(e) => setForm({ ...form, body: e.target.value })}
            />
          </label>
          <div className="adm-form-grid">
            <label>
              级别
              <select
                value={form.level}
                onChange={(e) => setForm({ ...form, level: e.target.value as any })}
              >
                <option value="info">info</option>
                <option value="warning">warning</option>
                <option value="error">error</option>
              </select>
            </label>
            <label>
              受众
              <select
                value={form.audience_scope}
                onChange={(e) => setForm({ ...form, audience_scope: e.target.value })}
              >
                <option value="all">所有用户</option>
                <option value="admin_only">仅 admin</option>
              </select>
            </label>
            <label>
              状态
              <select
                value={form.status}
                onChange={(e) => setForm({ ...form, status: e.target.value as any })}
              >
                <option value="draft">草稿</option>
                <option value="published">立即发布</option>
              </select>
            </label>
          </div>
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
