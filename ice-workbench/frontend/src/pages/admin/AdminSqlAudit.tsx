import { useEffect, useState } from "react";
import { sqlAuditApi } from "@/api/endpoints";
import type { SqlAuditRow, SqlAuditStats } from "@/api/endpoints";
import { Skeleton } from "@/components/feedback/Skeleton";

const PERIODS = [7, 30, 90];

export function AdminSqlAudit() {
  const [items, setItems] = useState<SqlAuditRow[]>([]);
  const [stats, setStats] = useState<SqlAuditStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [days, setDays] = useState(30);
  const [decision, setDecision] = useState<string>("");
  const [q, setQ] = useState("");
  const [active, setActive] = useState<SqlAuditRow | null>(null);

  const reload = async () => {
    setLoading(true);
    try {
      const [r, s] = await Promise.all([
        sqlAuditApi.list({ days, decision: decision || undefined, q: q || undefined, limit: 200 }),
        sqlAuditApi.stats(days),
      ]);
      setItems(r.items);
      setStats(s);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void reload();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [days, decision]);

  return (
    <div>
      <div className="adm-page-head" style={{ display: "flex", justifyContent: "space-between" }}>
        <div>
          <h1>🔍 SQL 审计</h1>
          <p>每条 SQL Skill 调用都会被分类（allow / warn / block）并持久化</p>
        </div>
        <div style={{ display: "flex", gap: 8 }}>
          {PERIODS.map((d) => (
            <button
              key={d}
              className={d === days ? "btn-primary" : "btn-secondary"}
              onClick={() => setDays(d)}
              style={{ padding: "6px 14px", fontSize: 12 }}
            >
              {d} 天
            </button>
          ))}
          <a className="btn-secondary" href={sqlAuditApi.exportCsvUrl(days)} target="_blank" rel="noreferrer">
            📥 CSV
          </a>
        </div>
      </div>

      {stats && (
        <div className="adm-stat-grid">
          <Stat label="放行" val={stats.by_decision.allow || 0} color="var(--success)" />
          <Stat label="警告" val={stats.by_decision.warn || 0} color="var(--warning)" />
          <Stat label="拦截" val={stats.by_decision.block || 0} color="var(--error)" />
          <Stat
            label="拦截比例"
            val={
              fmtPct(
                (stats.by_decision.block || 0),
                (stats.by_decision.allow || 0) +
                  (stats.by_decision.warn || 0) +
                  (stats.by_decision.block || 0),
              )
            }
            color="var(--error)"
          />
        </div>
      )}

      <div className="adm-toolbar">
        <input
          placeholder="🔍 SQL 关键字"
          value={q}
          onChange={(e) => setQ(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && reload()}
        />
        <select value={decision} onChange={(e) => setDecision(e.target.value)}>
          <option value="">全部判定</option>
          <option value="allow">放行</option>
          <option value="warn">警告</option>
          <option value="block">拦截</option>
        </select>
        <button className="btn-secondary" onClick={reload}>
          搜索
        </button>
      </div>

      {loading ? (
        <Skeleton lines={6} />
      ) : items.length === 0 ? (
        <div className="adm-section" style={{ textAlign: "center", color: "var(--text-muted)" }}>
          暂无审计记录。SQL Skill 调用后会自动落库。
        </div>
      ) : (
        <table className="adm-table">
          <thead>
            <tr>
              <th>时间</th>
              <th>判定</th>
              <th>SQL</th>
              <th style={{ textAlign: "right" }}>耗时</th>
              <th style={{ textAlign: "right" }}>行数</th>
              <th style={{ width: 80 }}>操作</th>
            </tr>
          </thead>
          <tbody>
            {items.map((r) => (
              <tr key={r.id}>
                <td style={{ fontFamily: "var(--font-mono)", fontSize: 11, color: "var(--text-muted)" }}>
                  {new Date(r.created_at).toLocaleString()}
                </td>
                <td>
                  <span className={`role-badge`} style={{ background: decisionDim(r.decision), color: decisionColor(r.decision) }}>
                    {r.decision}
                  </span>
                </td>
                <td
                  style={{
                    fontFamily: "var(--font-mono)",
                    fontSize: 11,
                    maxWidth: 480,
                    overflow: "hidden",
                    textOverflow: "ellipsis",
                    whiteSpace: "nowrap",
                  }}
                  title={r.sql}
                >
                  {r.sql}
                </td>
                <td style={{ textAlign: "right", fontFamily: "var(--font-mono)", fontSize: 11 }}>
                  {r.duration_ms != null ? `${r.duration_ms}ms` : "-"}
                </td>
                <td style={{ textAlign: "right", fontFamily: "var(--font-mono)", fontSize: 11 }}>
                  {r.rows_returned ?? "-"}
                </td>
                <td>
                  <button
                    className="btn-ghost"
                    onClick={() => setActive(r)}
                    style={{ fontSize: 11, padding: "4px 8px" }}
                  >
                    详情
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      {active && (
        <div className="cm-overlay" onClick={() => setActive(null)}>
          <div className="cm-card" style={{ minWidth: 640, maxWidth: "80vw" }} onClick={(e) => e.stopPropagation()}>
            <h3>SQL 审计详情</h3>
            <div className="cm-body" style={{ display: "flex", flexDirection: "column", gap: 12 }}>
              <KV label="时间" val={new Date(active.created_at).toLocaleString()} />
              <KV
                label="判定"
                val={
                  <span style={{ color: decisionColor(active.decision) }}>
                    {active.decision} {active.block_reason ? `· ${active.block_reason}` : ""}
                  </span>
                }
              />
              <KV label="用户" val={active.user_id || "-"} />
              <KV label="Agent" val={active.agent_id || "-"} />
              <KV label="任务" val={active.task_id || "-"} />
              <KV label="耗时" val={active.duration_ms != null ? `${active.duration_ms}ms` : "-"} />
              <KV label="返回行数" val={active.rows_returned ?? "-"} />
              {active.error_message && <KV label="错误" val={active.error_message} />}
              <div>
                <div style={{ fontSize: 12, color: "var(--text-muted)", marginBottom: 4 }}>SQL</div>
                <pre
                  style={{
                    background: "var(--surface-2)",
                    border: "1px solid var(--border)",
                    borderRadius: 6,
                    padding: 12,
                    fontFamily: "var(--font-mono)",
                    fontSize: 12,
                    margin: 0,
                    whiteSpace: "pre-wrap",
                  }}
                >
                  {active.sql}
                </pre>
              </div>
            </div>
            <div className="cm-actions">
              <button className="btn-secondary" onClick={() => navigator.clipboard.writeText(active.sql)}>
                复制 SQL
              </button>
              <button className="btn-primary" onClick={() => setActive(null)}>
                关闭
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function KV({ label, val }: { label: string; val: React.ReactNode }) {
  return (
    <div style={{ display: "flex", gap: 12, fontSize: 13 }}>
      <span style={{ minWidth: 80, color: "var(--text-muted)" }}>{label}</span>
      <span style={{ fontFamily: "var(--font-mono)", fontSize: 12 }}>{val}</span>
    </div>
  );
}

function Stat({ label, val, color }: { label: string; val: string | number; color: string }) {
  return (
    <div className="adm-stat">
      <div className="adm-stat-label">{label}</div>
      <div className="adm-stat-val" style={{ color }}>
        {val}
      </div>
    </div>
  );
}

function decisionColor(d: string): string {
  return d === "allow" ? "var(--success)" : d === "warn" ? "var(--warning)" : "var(--error)";
}
function decisionDim(d: string): string {
  return d === "allow" ? "var(--success-dim)" : d === "warn" ? "var(--warning-dim)" : "var(--error-dim)";
}
function fmtPct(num: number, den: number): string {
  if (den <= 0) return "-";
  return `${((num / den) * 100).toFixed(1)}%`;
}
