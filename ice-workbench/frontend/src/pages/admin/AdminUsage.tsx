import { useEffect, useMemo, useState } from "react";
import { adminApi, usageApi } from "@/api/endpoints";
import type { DailyUsage, DimUsage, UsageSummary } from "@/api/endpoints";
import type { AdminUser, AdminAgent } from "@/api/endpoints";
import { Skeleton } from "@/components/feedback/Skeleton";
import { BarSeries, Sparkline } from "@/components/charts/Sparkline";

type Tab = "daily" | "model" | "user" | "agent" | "task";

const TABS: { k: Tab; label: string }[] = [
  { k: "daily", label: "日趋势" },
  { k: "model", label: "按模型" },
  { k: "user", label: "按用户" },
  { k: "agent", label: "按 Agent" },
  { k: "task", label: "按任务" },
];

const PERIODS = [7, 30, 90];

export function AdminUsage() {
  const [tab, setTab] = useState<Tab>("daily");
  const [days, setDays] = useState(30);
  const [summary, setSummary] = useState<UsageSummary | null>(null);
  const [daily, setDaily] = useState<DailyUsage[]>([]);
  const [byDim, setByDim] = useState<Record<Tab, DimUsage[]>>({
    daily: [],
    model: [],
    user: [],
    agent: [],
    task: [],
  });
  const [users, setUsers] = useState<AdminUser[]>([]);
  const [agents, setAgents] = useState<AdminAgent[]>([]);

  const reload = async () => {
    setSummary(await usageApi.summary());
    setDaily((await usageApi.daily(days)).items);
    const [m, u, a, t] = await Promise.all([
      usageApi.byDim("model", days, 10),
      usageApi.byDim("user_id", days, 10),
      usageApi.byDim("agent_id", days, 10),
      usageApi.byDim("task_id", days, 10),
    ]);
    setByDim({ daily: [], model: m.items, user: u.items, agent: a.items, task: t.items });
  };

  useEffect(() => {
    void reload();
    adminApi.listUsers().then((r) => setUsers(r.items)).catch(() => {});
    adminApi.listAgents().then((r) => setAgents(r.items)).catch(() => {});
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [days]);

  const userById = useMemo(() => {
    const m: Record<string, AdminUser> = {};
    users.forEach((u) => (m[u.id] = u));
    return m;
  }, [users]);
  const agentById = useMemo(() => {
    const m: Record<string, AdminAgent> = {};
    agents.forEach((a) => (m[a.id] = a));
    return m;
  }, [agents]);

  const labelFor = (t: Tab, key: string): string => {
    if (t === "user") return userById[key]?.name || key.slice(0, 8);
    if (t === "agent") return agentById[key]?.name || key;
    if (t === "task") return key.slice(0, 12) + "…";
    return key;
  };

  if (!summary) {
    return (
      <div>
        <Skeleton lines={6} />
      </div>
    );
  }

  return (
    <div>
      <div className="adm-page-head" style={{ display: "flex", justifyContent: "space-between" }}>
        <div>
          <h1>💰 用量与成本</h1>
          <p>按 LLM tokens × 单价计算；超预算自动告警</p>
        </div>
        <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
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
          <a className="btn-secondary" href={usageApi.exportCsvUrl(days)} target="_blank" rel="noreferrer">
            📥 CSV
          </a>
        </div>
      </div>

      <BudgetCard summary={summary} />

      <div className="adm-stat-grid">
        <Stat label="本月调用" val={summary.calls.toLocaleString()} color="var(--primary)" />
        <Stat label="本月输入" val={fmtTokens(summary.input_tokens)} color="var(--p-data)" />
        <Stat label="本月输出" val={fmtTokens(summary.output_tokens)} color="var(--p-biz)" />
        <Stat label="本月成本" val={`$${summary.cost_usd.toFixed(2)}`} color="var(--agent)" />
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
            {t.label}
          </button>
        ))}
      </div>

      {tab === "daily" && (
        <div className="adm-section">
          <h3 style={{ fontFamily: "var(--font-head)", fontSize: 14, marginTop: 0 }}>
            过去 {days} 天每日成本（USD）
          </h3>
          <Sparkline values={daily.map((d) => d.cost_usd)} height={140} />
          <h3 style={{ fontFamily: "var(--font-head)", fontSize: 13, marginTop: 24 }}>调用次数</h3>
          <Sparkline values={daily.map((d) => d.calls)} height={100} stroke="var(--p-data)" fill="var(--p-data-dim)" />
          <table className="adm-table" style={{ marginTop: 16 }}>
            <thead>
              <tr>
                <th>日期</th>
                <th style={{ textAlign: "right" }}>调用</th>
                <th style={{ textAlign: "right" }}>输入 tokens</th>
                <th style={{ textAlign: "right" }}>输出 tokens</th>
                <th style={{ textAlign: "right" }}>成本 (USD)</th>
              </tr>
            </thead>
            <tbody>
              {daily.slice().reverse().slice(0, 14).map((d) => (
                <tr key={d.day}>
                  <td>{d.day}</td>
                  <td style={{ textAlign: "right" }}>{d.calls}</td>
                  <td style={{ textAlign: "right", fontFamily: "var(--font-mono)" }}>{d.input_tokens.toLocaleString()}</td>
                  <td style={{ textAlign: "right", fontFamily: "var(--font-mono)" }}>{d.output_tokens.toLocaleString()}</td>
                  <td style={{ textAlign: "right", fontFamily: "var(--font-mono)" }}>${d.cost_usd.toFixed(4)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {tab !== "daily" && (
        <div className="adm-section">
          <BarSeries
            items={byDim[tab].map((it) => ({ key: it.key, value: it.cost_usd }))}
            color={tab === "model" ? "var(--primary)" : tab === "user" ? "var(--p-data)" : tab === "agent" ? "var(--agent)" : "var(--p-biz)"}
            formatLabel={(k) => labelFor(tab, k)}
            formatValue={(v) => `$${v.toFixed(4)}`}
          />
          <table className="adm-table" style={{ marginTop: 18 }}>
            <thead>
              <tr>
                <th>{tab === "model" ? "模型" : tab === "user" ? "用户" : tab === "agent" ? "Agent" : "任务"}</th>
                <th style={{ textAlign: "right" }}>调用</th>
                <th style={{ textAlign: "right" }}>输入</th>
                <th style={{ textAlign: "right" }}>输出</th>
                <th style={{ textAlign: "right" }}>成本</th>
              </tr>
            </thead>
            <tbody>
              {byDim[tab].map((it) => (
                <tr key={it.key}>
                  <td>{labelFor(tab, it.key)}</td>
                  <td style={{ textAlign: "right" }}>{it.calls}</td>
                  <td style={{ textAlign: "right", fontFamily: "var(--font-mono)" }}>{it.input_tokens.toLocaleString()}</td>
                  <td style={{ textAlign: "right", fontFamily: "var(--font-mono)" }}>{it.output_tokens.toLocaleString()}</td>
                  <td style={{ textAlign: "right", fontFamily: "var(--font-mono)" }}>${it.cost_usd.toFixed(4)}</td>
                </tr>
              ))}
              {byDim[tab].length === 0 && (
                <tr>
                  <td colSpan={5} style={{ textAlign: "center", padding: 32, color: "var(--text-muted)" }}>
                    暂无数据
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

function BudgetCard({ summary }: { summary: UsageSummary }) {
  const ratio = summary.budget_used_ratio;
  const pct = Math.min(100, ratio * 100);
  const color =
    summary.budget_state === "exceeded"
      ? "var(--error)"
      : summary.budget_state === "warning"
        ? "var(--warning)"
        : "var(--success)";
  const label =
    summary.budget_state === "exceeded"
      ? "已超预算"
      : summary.budget_state === "warning"
        ? "接近预算上限"
        : "预算充足";
  return (
    <div
      className="adm-section"
      style={{
        marginBottom: 16,
        borderColor: color,
        background:
          summary.budget_state === "ok"
            ? "var(--surface)"
            : summary.budget_state === "warning"
              ? "var(--warning-dim)"
              : "var(--error-dim)",
      }}
    >
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", marginBottom: 10 }}>
        <div>
          <div style={{ fontFamily: "var(--font-head)", fontSize: 14, color }}>{label}</div>
          <div style={{ fontSize: 11, color: "var(--text-muted)", marginTop: 2 }}>
            本月预算 ${summary.budget_usd.toFixed(2)} · 已用 ${summary.cost_usd.toFixed(2)} ({(ratio * 100).toFixed(1)}%)
          </div>
        </div>
        <div style={{ fontFamily: "var(--font-mono)", fontSize: 12, color: "var(--text-muted)" }}>{summary.month}</div>
      </div>
      <div style={{ height: 8, background: "var(--surface-2)", borderRadius: 4, overflow: "hidden" }}>
        <div style={{ width: `${pct}%`, height: "100%", background: color, transition: "width .3s" }} />
      </div>
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

function fmtTokens(n: number): string {
  if (n < 1000) return String(n);
  if (n < 1_000_000) return `${(n / 1000).toFixed(1)}K`;
  return `${(n / 1_000_000).toFixed(2)}M`;
}
