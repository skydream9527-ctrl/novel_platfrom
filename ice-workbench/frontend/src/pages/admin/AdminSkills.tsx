import { useEffect, useState } from "react";
import { adminSkillApi } from "@/api/endpoints";
import type { SkillRecord } from "@/api/endpoints";
import { ConfirmModal } from "@/components/feedback/ConfirmModal";
import { Skeleton } from "@/components/feedback/Skeleton";
import { useUIStore } from "@/stores/uiStore";

export function AdminSkills() {
  const pushToast = useUIStore((s) => s.pushToast);
  const [items, setItems] = useState<SkillRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [editing, setEditing] = useState<SkillRecord | null>(null);
  const [creating, setCreating] = useState(false);
  const [confirmDelete, setConfirmDelete] = useState<SkillRecord | null>(null);
  const [testFor, setTestFor] = useState<SkillRecord | null>(null);

  const reload = async () => {
    setLoading(true);
    try {
      const r = await adminSkillApi.list();
      setItems(r.items);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void reload();
  }, []);

  const remove = async (s: SkillRecord) => {
    try {
      await adminSkillApi.remove(s.id);
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
          <h1>⚡ Skills</h1>
          <p>Agent 可调用的 function tools。内置 3 个不可改，自定义可 CRUD。</p>
        </div>
        <button className="btn-primary" onClick={() => setCreating(true)}>
          + 新建 Skill
        </button>
      </div>

      {loading ? (
        <Skeleton lines={6} />
      ) : (
        <table className="adm-table">
          <thead>
            <tr>
              <th>ID</th>
              <th>名称</th>
              <th>分类</th>
              <th>描述</th>
              <th>状态</th>
              <th style={{ width: 280 }}>操作</th>
            </tr>
          </thead>
          <tbody>
            {items.map((s) => (
              <tr key={s.id}>
                <td style={{ fontFamily: "var(--font-mono)", fontSize: 12 }}>{s.id}</td>
                <td>{s.name}</td>
                <td>
                  <span className="role-badge role-user">{s.category}</span>
                  {s.builtin && (
                    <span style={{ marginLeft: 6, fontSize: 10, color: "var(--text-muted)" }}>
                      内置
                    </span>
                  )}
                </td>
                <td
                  style={{
                    maxWidth: 360,
                    overflow: "hidden",
                    textOverflow: "ellipsis",
                    whiteSpace: "nowrap",
                    color: "var(--text-dim)",
                    fontSize: 12,
                  }}
                  title={s.description}
                >
                  {s.description}
                </td>
                <td>{s.enabled ? "✅" : "❌"}</td>
                <td className="row-actions">
                  <button onClick={() => setTestFor(s)}>▶ 试运行</button>
                  {!s.builtin && (
                    <>
                      <button onClick={() => setEditing(s)}>✏ 编辑</button>
                      <button className="danger" onClick={() => setConfirmDelete(s)}>
                        🗑
                      </button>
                    </>
                  )}
                  {s.builtin && (
                    <button onClick={() => setEditing({ ...s })} title="只读查看">
                      👁 查看
                    </button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      {(creating || editing) && (
        <SkillModal
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
      {testFor && <TestRunModal skill={testFor} onClose={() => setTestFor(null)} />}
      <ConfirmModal
        open={!!confirmDelete}
        title={`确认删除 Skill「${confirmDelete?.name}」？`}
        body="删除后已绑定此 Skill 的 Agent 将无法调用。"
        danger
        onConfirm={() => confirmDelete && remove(confirmDelete)}
        onCancel={() => setConfirmDelete(null)}
      />
    </div>
  );
}

function SkillModal({
  existing,
  onClose,
  onSaved,
}: {
  existing: SkillRecord | null;
  onClose: () => void;
  onSaved: () => void | Promise<void>;
}) {
  const pushToast = useUIStore((s) => s.pushToast);
  const readonly = !!existing?.builtin;
  const [form, setForm] = useState({
    id: existing?.id || "",
    name: existing?.name || "",
    description: existing?.description || "",
    category: existing?.category || "custom",
    tool_entry: existing?.tool_entry || "",
    schemaJson: JSON.stringify(existing?.tool_schema || { name: "", description: "", parameters: { type: "object", properties: {} } }, null, 2),
    enabled: existing?.enabled ?? true,
  });
  const [saving, setSaving] = useState(false);
  const [validation, setValidation] = useState<string | null>(null);

  const validate = async () => {
    try {
      const parsed = JSON.parse(form.schemaJson);
      const r = await adminSkillApi.validate(parsed);
      setValidation(r.valid ? "✅ schema 合法" : `❌ ${r.reason}`);
    } catch (e) {
      setValidation(`❌ JSON 解析失败：${(e as Error).message}`);
    }
  };

  const formatJson = () => {
    try {
      const parsed = JSON.parse(form.schemaJson);
      setForm({ ...form, schemaJson: JSON.stringify(parsed, null, 2) });
    } catch (e) {
      pushToast("error", `JSON 解析失败：${(e as Error).message}`);
    }
  };

  const save = async () => {
    if (readonly) {
      onClose();
      return;
    }
    let schema: Record<string, unknown>;
    try {
      schema = JSON.parse(form.schemaJson);
    } catch (e) {
      return pushToast("error", `tool_schema 解析失败：${(e as Error).message}`);
    }
    setSaving(true);
    try {
      if (existing) {
        await adminSkillApi.update(existing.id, {
          name: form.name,
          description: form.description,
          category: form.category,
          tool_entry: form.tool_entry,
          tool_schema: schema,
          enabled: form.enabled,
        });
      } else {
        await adminSkillApi.create({
          name: form.name,
          description: form.description,
          category: form.category,
          tool_entry: form.tool_entry,
          tool_schema: schema,
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
      <div className="cm-card" style={{ minWidth: 720, maxWidth: "85vw" }} onClick={(e) => e.stopPropagation()}>
        <h3>
          {readonly ? `查看「${existing?.name}」（内置不可编辑）` : existing ? `编辑「${existing.name}」` : "新建 Skill"}
        </h3>
        <div className="cm-body" style={{ display: "flex", flexDirection: "column", gap: 10 }}>
          <div className="adm-form-grid">
            <label>
              名称
              <input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} disabled={readonly} />
            </label>
            <label>
              分类
              <input value={form.category} onChange={(e) => setForm({ ...form, category: e.target.value })} disabled={readonly} />
            </label>
            <label style={{ gridColumn: "span 2" }}>
              描述
              <input
                value={form.description}
                onChange={(e) => setForm({ ...form, description: e.target.value })}
                disabled={readonly}
              />
            </label>
            <label style={{ gridColumn: "span 2" }}>
              tool_entry（执行入口，例如 module:func）
              <input
                value={form.tool_entry}
                onChange={(e) => setForm({ ...form, tool_entry: e.target.value })}
                disabled={readonly}
              />
            </label>
          </div>
          <div>
            <div style={{ display: "flex", alignItems: "center", marginBottom: 6 }}>
              <span style={{ fontSize: 12, color: "var(--text-dim)" }}>tool_schema (JSON)</span>
              <div style={{ marginLeft: "auto", display: "flex", gap: 6 }}>
                <button className="btn-ghost" onClick={formatJson} disabled={readonly}>
                  格式化
                </button>
                <button className="btn-ghost" onClick={validate}>
                  验证
                </button>
              </div>
            </div>
            <textarea
              rows={14}
              value={form.schemaJson}
              onChange={(e) => setForm({ ...form, schemaJson: e.target.value })}
              disabled={readonly}
              style={{
                width: "100%",
                background: "var(--surface-2)",
                border: "1px solid var(--border)",
                borderRadius: 6,
                color: "var(--text)",
                fontFamily: "var(--font-mono)",
                fontSize: 12,
                padding: 10,
                outline: "none",
                resize: "vertical",
              }}
            />
            {validation && (
              <div style={{ fontSize: 11, marginTop: 4, color: validation.startsWith("✅") ? "var(--success)" : "var(--error)" }}>
                {validation}
              </div>
            )}
          </div>
          <label className="ct-toggle">
            <input
              type="checkbox"
              checked={form.enabled}
              onChange={(e) => setForm({ ...form, enabled: e.target.checked })}
              disabled={readonly}
            />
            启用
          </label>
        </div>
        <div className="cm-actions">
          <button className="btn-secondary" onClick={onClose}>
            {readonly ? "关闭" : "取消"}
          </button>
          {!readonly && (
            <button className="btn-primary" disabled={saving} onClick={save}>
              {saving ? "保存中…" : "保存"}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

function TestRunModal({ skill, onClose }: { skill: SkillRecord; onClose: () => void }) {
  const [argsJson, setArgsJson] = useState("{}");
  const [running, setRunning] = useState(false);
  const [result, setResult] = useState<unknown | null>(null);
  const [error, setError] = useState<string | null>(null);

  const run = async () => {
    setRunning(true);
    setResult(null);
    setError(null);
    let args: Record<string, unknown>;
    try {
      args = JSON.parse(argsJson || "{}");
    } catch (e) {
      setError(`参数 JSON 解析失败：${(e as Error).message}`);
      setRunning(false);
      return;
    }
    try {
      const r = await adminSkillApi.testRun(skill.id, args);
      if (r.success) setResult(r.result);
      else setError(r.error || "未知错误");
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setRunning(false);
    }
  };

  return (
    <div className="cm-overlay" onClick={onClose}>
      <div className="cm-card" style={{ minWidth: 600 }} onClick={(e) => e.stopPropagation()}>
        <h3>▶ 测试运行：{skill.name}</h3>
        <div className="cm-body" style={{ display: "flex", flexDirection: "column", gap: 10 }}>
          <label className="ct-field">
            <span>参数 (JSON)</span>
            <textarea
              rows={5}
              value={argsJson}
              onChange={(e) => setArgsJson(e.target.value)}
              placeholder='{"sql":"SELECT 1"}'
              style={{ fontFamily: "var(--font-mono)" }}
            />
          </label>
          {result !== null && (
            <div>
              <div style={{ fontSize: 12, color: "var(--success)", marginBottom: 4 }}>✅ 成功</div>
              <pre
                style={{
                  background: "var(--surface-2)",
                  border: "1px solid var(--border)",
                  borderRadius: 6,
                  padding: 10,
                  fontSize: 11,
                  margin: 0,
                  whiteSpace: "pre-wrap",
                  maxHeight: 280,
                  overflow: "auto",
                }}
              >
                {JSON.stringify(result, null, 2)}
              </pre>
            </div>
          )}
          {error && (
            <div style={{ background: "var(--error-dim)", padding: 10, borderRadius: 6, fontSize: 12, color: "var(--error)" }}>
              ❌ {error}
            </div>
          )}
        </div>
        <div className="cm-actions">
          <button className="btn-secondary" onClick={onClose}>
            关闭
          </button>
          <button className="btn-primary" disabled={running} onClick={run}>
            {running ? "执行中…" : "▶ 运行"}
          </button>
        </div>
      </div>
    </div>
  );
}
