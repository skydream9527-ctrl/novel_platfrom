import { useEffect, useMemo, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { TopNav } from "@/components/shell/TopNav";
import { ConfirmModal } from "@/components/feedback/ConfirmModal";
import { EmptyState } from "@/components/feedback/ErrorState";
import { Skeleton } from "@/components/feedback/Skeleton";
import { scheduledApi, taskApi } from "@/api/endpoints";
import type { ScheduledRun, ScheduledTask } from "@/api/endpoints";
import type { TaskSummary } from "@/types/api";
import { useUIStore } from "@/stores/uiStore";
import "./Scheduled.css";

export function ScheduledTasksPage() {
  const [params] = useSearchParams();
  const filterTaskId = params.get("taskId");
  const navigate = useNavigate();
  const pushToast = useUIStore((s) => s.pushToast);

  const [items, setItems] = useState<ScheduledTask[]>([]);
  const [tasks, setTasks] = useState<TaskSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [filterEnabled, setFilterEnabled] = useState<"all" | "on" | "off">("all");
  const [search, setSearch] = useState("");

  const [showCreate, setShowCreate] = useState(false);
  const [editing, setEditing] = useState<ScheduledTask | null>(null);
  const [confirmDelete, setConfirmDelete] = useState<ScheduledTask | null>(null);
  const [expandedRuns, setExpandedRuns] = useState<Record<string, ScheduledRun[]>>({});

  const reload = async () => {
    setLoading(true);
    try {
      const r = await scheduledApi.listMine();
      setItems(r.items.filter((s) => !filterTaskId || s.task_id === filterTaskId));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void reload();
    taskApi.list().then((r) => setTasks(r.items)).catch(() => {});
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filterTaskId]);

  const filtered = useMemo(
    () =>
      items.filter((s) => {
        if (filterEnabled === "on" && !s.enabled) return false;
        if (filterEnabled === "off" && s.enabled) return false;
        if (search && !`${s.name}${s.task_name || ""}${s.cron}`.includes(search)) return false;
        return true;
      }),
    [items, filterEnabled, search],
  );

  const toggle = async (s: ScheduledTask) => {
    try {
      await scheduledApi.update(s.task_id, s.id, { enabled: !s.enabled });
      pushToast("success", s.enabled ? "已暂停" : "已恢复");
      await reload();
    } catch (err) {
      pushToast("error", (err as Error).message);
    }
  };

  const runNow = async (s: ScheduledTask) => {
    try {
      pushToast("info", `正在执行 ${s.name}…`);
      const run = await scheduledApi.runNow(s.task_id, s.id);
      pushToast(
        run.status === "success" ? "success" : "warning",
        `执行${run.status === "success" ? "成功" : "结束"}：${run.status}`,
      );
      await reload();
    } catch (err) {
      pushToast("error", (err as Error).message);
    }
  };

  const expand = async (s: ScheduledTask) => {
    if (expandedRuns[s.id]) {
      const next = { ...expandedRuns };
      delete next[s.id];
      setExpandedRuns(next);
      return;
    }
    try {
      const r = await scheduledApi.listRuns(s.task_id, s.id);
      setExpandedRuns({ ...expandedRuns, [s.id]: r.items });
    } catch (err) {
      pushToast("error", (err as Error).message);
    }
  };

  const remove = async (s: ScheduledTask) => {
    try {
      await scheduledApi.remove(s.task_id, s.id);
      pushToast("success", "已删除");
      setConfirmDelete(null);
      await reload();
    } catch (err) {
      pushToast("error", (err as Error).message);
    }
  };

  return (
    <div className="sc-page">
      <TopNav mode="workspace" crumb={<span>首页 / <span className="current">定时任务</span></span>} />
      <main className="sc-main">
        <header className="sc-head">
          <div>
            <h1>⏱ 定时任务</h1>
            <p>每个任务可绑定多个 cron 触发器；执行历史可查。</p>
          </div>
          <button className="btn-primary" onClick={() => setShowCreate(true)}>
            + 创建定时任务
          </button>
        </header>

        <div className="sc-filter">
          <div className="sc-chips">
            {(["all", "on", "off"] as const).map((k) => (
              <button
                key={k}
                className={`sc-chip ${filterEnabled === k ? "on" : ""}`}
                onClick={() => setFilterEnabled(k)}
              >
                {k === "all" ? "全部" : k === "on" ? "运行中" : "已暂停"}
              </button>
            ))}
          </div>
          <input
            className="sc-search"
            placeholder="🔍 搜索任务名 / cron"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>

        {loading ? (
          <Skeleton lines={6} />
        ) : filtered.length === 0 ? (
          <EmptyState
            illustration="⏱"
            title="还没有定时任务"
            hint="从已有任务创建一个 cron 触发器，自动跑数 + 推送结果"
            cta={
              <button className="btn-primary" onClick={() => setShowCreate(true)}>
                创建第一个定时任务
              </button>
            }
          />
        ) : (
          <div className="sc-list">
            {filtered.map((s) => (
              <div key={s.id} className="sc-card">
                <div className="sc-card-head">
                  <span className={`sc-status ${s.enabled ? "on" : "off"}`}>
                    {s.enabled ? "运行中" : "已暂停"}
                  </span>
                  <div className="sc-card-name">{s.name}</div>
                  <div className="sc-card-actions">
                    <button onClick={() => runNow(s)}>▶ 立即执行</button>
                    <button onClick={() => toggle(s)}>{s.enabled ? "⏸ 暂停" : "▶ 恢复"}</button>
                    <button onClick={() => setEditing(s)}>✏ 编辑</button>
                    <button onClick={() => setConfirmDelete(s)} className="danger">🗑 删除</button>
                  </div>
                </div>
                <div className="sc-card-body">
                  <div>
                    <span className="sc-label">cron</span>
                    <code>{s.cron}</code>
                    <span className="sc-cron-readable">{readableCron(s.cron)}</span>
                  </div>
                  <div>
                    <span className="sc-label">所属任务</span>
                    <a onClick={() => navigate(`/workspace/${s.task_id}`)} style={{ cursor: "pointer" }}>
                      {s.task_name || s.task_id.slice(0, 8)}
                    </a>
                  </div>
                  <div>
                    <span className="sc-label">下次</span>
                    {fmt(s.next_fire_at)}
                  </div>
                  <div>
                    <span className="sc-label">上次</span>
                    {fmt(s.last_fire_at)}
                  </div>
                </div>
                {s.prompt && (
                  <details className="sc-prompt">
                    <summary>📜 Prompt</summary>
                    <pre>{s.prompt}</pre>
                  </details>
                )}
                <div className="sc-runs-toggle">
                  <button onClick={() => expand(s)}>
                    {expandedRuns[s.id] ? "收起" : "查看"}执行历史
                  </button>
                </div>
                {expandedRuns[s.id] && (
                  <div className="sc-runs">
                    {expandedRuns[s.id].length === 0 && (
                      <div className="sc-empty">暂无执行记录</div>
                    )}
                    {expandedRuns[s.id].map((r) => (
                      <details key={r.id} className={`sc-run sc-run-${r.status}`}>
                        <summary>
                          <span className={`sc-run-badge ${r.status}`}>{r.status}</span>
                          <span>{fmt(r.started_at)}</span>
                          <span style={{ color: "var(--text-muted)", marginLeft: "auto" }}>
                            {r.trigger}
                          </span>
                        </summary>
                        <div className="sc-run-body">
                          <div>
                            <strong>Prompt</strong>
                            <pre>{r.prompt}</pre>
                          </div>
                          {r.output && (
                            <div>
                              <strong>输出</strong>
                              <pre>{r.output}</pre>
                            </div>
                          )}
                          {r.error && (
                            <div>
                              <strong>错误</strong>
                              <pre>
                                [{r.error.code}] {r.error.message}
                              </pre>
                            </div>
                          )}
                          {r.tokens && (
                            <div>
                              <strong>Tokens</strong>
                              <span>
                                input={r.tokens.input}, output={r.tokens.output}
                              </span>
                            </div>
                          )}
                        </div>
                      </details>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </main>

      {(showCreate || editing) && (
        <ScheduleEditModal
          tasks={tasks}
          existing={editing}
          onClose={() => {
            setShowCreate(false);
            setEditing(null);
          }}
          onSaved={async () => {
            setShowCreate(false);
            setEditing(null);
            await reload();
          }}
        />
      )}
      <ConfirmModal
        open={!!confirmDelete}
        title={`确认删除“${confirmDelete?.name}”？`}
        body="删除后历史执行记录仍保留在文件系统中。"
        danger
        onConfirm={() => confirmDelete && remove(confirmDelete)}
        onCancel={() => setConfirmDelete(null)}
      />
    </div>
  );
}

function fmt(iso: string | null): string {
  if (!iso) return "-";
  const d = new Date(iso);
  return d.toLocaleString();
}

function readableCron(expr: string): string {
  const p = expr.split(/\s+/);
  if (p.length !== 5) return "";
  const [m, h, dom, mo, dow] = p;
  if (m === "0" && h === "*" && dom === "*" && mo === "*" && dow === "*") return "每小时整点";
  if (m === "0" && /^\d+$/.test(h) && dom === "*" && mo === "*" && dow === "*")
    return `每天 ${h.padStart(2, "0")}:00`;
  if (m === "0" && /^\d+$/.test(h) && dom === "*" && mo === "*" && dow === "1-5")
    return `工作日 ${h.padStart(2, "0")}:00`;
  return "";
}

interface ModalProps {
  tasks: TaskSummary[];
  existing: ScheduledTask | null;
  onClose: () => void;
  onSaved: () => void | Promise<void>;
}

function ScheduleEditModal({ tasks, existing, onClose, onSaved }: ModalProps) {
  const pushToast = useUIStore((s) => s.pushToast);
  const [form, setForm] = useState({
    task_id: existing?.task_id || tasks[0]?.id || "",
    name: existing?.name || "",
    cron: existing?.cron || "0 9 * * *",
    prompt: existing?.prompt || "",
    enabled: existing?.enabled ?? true,
  });
  const [saving, setSaving] = useState(false);
  const save = async () => {
    if (!form.task_id) return pushToast("warning", "请选择所属任务");
    if (!form.name.trim()) return pushToast("warning", "请填写名称");
    setSaving(true);
    try {
      if (existing) {
        await scheduledApi.update(existing.task_id, existing.id, form);
      } else {
        await scheduledApi.create(form.task_id, form);
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
      <div className="cm-card sc-modal" onClick={(e) => e.stopPropagation()}>
        <h3>{existing ? "编辑定时任务" : "新建定时任务"}</h3>
        <div className="cm-body">
          <label className="ct-field">
            <span>所属任务</span>
            <select
              value={form.task_id}
              onChange={(e) => setForm({ ...form, task_id: e.target.value })}
              disabled={!!existing}
            >
              {tasks.map((t) => (
                <option key={t.id} value={t.id}>
                  {t.name}
                </option>
              ))}
            </select>
          </label>
          <label className="ct-field">
            <span>名称</span>
            <input
              value={form.name}
              onChange={(e) => setForm({ ...form, name: e.target.value })}
              placeholder="例如 每日 DAU 监控"
            />
          </label>
          <label className="ct-field">
            <span>cron 表达式</span>
            <input
              value={form.cron}
              onChange={(e) => setForm({ ...form, cron: e.target.value })}
            />
          </label>
          <label className="ct-field">
            <span>Prompt</span>
            <textarea
              rows={3}
              value={form.prompt}
              onChange={(e) => setForm({ ...form, prompt: e.target.value })}
              placeholder="例如：拉今日 DAU 与昨日对比，异常时高亮"
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
