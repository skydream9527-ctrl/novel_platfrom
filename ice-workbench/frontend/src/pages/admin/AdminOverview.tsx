import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { adminApi } from "@/api/endpoints";
import { Skeleton } from "@/components/feedback/Skeleton";

interface Stats {
  users: number;
  tasks: number;
  messages: number;
}
interface Alerts {
  experience_cards: number;
  public_tasks: number;
  templates: number;
  scheduled_failed: number;
}
interface RankItem {
  agent_id: string;
  name: string;
  icon: string;
  messages: number;
  satisfaction: number;
}
interface RecentUser {
  id: string;
  email: string;
  name: string;
  auth_role: string;
  created_at?: string | null;
}

export function AdminOverview() {
  const [stats, setStats] = useState<Stats | null>(null);
  const [alerts, setAlerts] = useState<Alerts | null>(null);
  const [rank, setRank] = useState<RankItem[]>([]);
  const [recent, setRecent] = useState<RecentUser[]>([]);

  useEffect(() => {
    adminApi.stats().then(setStats).catch(() => {});
    adminApi.alerts().then(setAlerts).catch(() => {});
    adminApi.agentRanking().then((r) => setRank(r.items)).catch(() => {});
    adminApi.recentUsers().then((r) => setRecent(r.items)).catch(() => {});
  }, []);

  const totalAlert = alerts
    ? alerts.experience_cards + alerts.public_tasks + alerts.templates + alerts.scheduled_failed
    : 0;
  const maxRank = Math.max(1, ...rank.map((r) => r.messages));

  return (
    <div>
      <div className="adm-page-head">
        <h1>📊 概览</h1>
        <p>查看平台运营全景</p>
      </div>

      {totalAlert > 0 && (
        <div className="adm-alert-card">
          <h3>🚨 待处理事项</h3>
          <div className="adm-alert-list">
            {alerts!.experience_cards > 0 && (
              <div className="adm-alert-item">
                <span>💡</span>
                {alerts!.experience_cards} 条经验卡片待审批
                <a>→ 立即审批</a>
              </div>
            )}
            {alerts!.public_tasks > 0 && (
              <div className="adm-alert-item">
                <span>🌐</span>
                {alerts!.public_tasks} 个公共任务待审核
                <a>→ 立即审核</a>
              </div>
            )}
            {alerts!.templates > 0 && (
              <div className="adm-alert-item">
                <span>📋</span>
                {alerts!.templates} 个模板待审核
                <a>→ 立即审核</a>
              </div>
            )}
          </div>
        </div>
      )}

      <div className="adm-stat-grid">
        {stats ? (
          <>
            <Stat label="用户数" val={stats.users} color="var(--primary)" />
            <Stat label="任务总数" val={stats.tasks} color="var(--p-biz)" />
            <Stat label="消息总数" val={stats.messages} color="var(--p-data)" />
            <Stat label="本月成本" val="—" color="var(--agent)" />
          </>
        ) : (
          Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="adm-stat">
              <Skeleton lines={2} />
            </div>
          ))
        )}
      </div>

      <div className="adm-two-col">
        <section className="adm-section">
          <h3>最近注册用户</h3>
          {recent.length === 0 ? (
            <Skeleton lines={3} />
          ) : (
            recent.map((u) => (
              <div key={u.id} className="adm-list-item">
                <div className="adm-list-avatar">{u.name?.[0] || "?"}</div>
                <div className="adm-list-info">
                  <div className="name">{u.name}</div>
                  <div className="meta">
                    {u.email} · {u.auth_role}
                  </div>
                </div>
                <div className="adm-list-time">{fmt(u.created_at)}</div>
              </div>
            ))
          )}
          <div style={{ textAlign: "right", marginTop: 8 }}>
            <Link to="/admin/users" style={{ fontSize: 12 }}>
              查看全部 →
            </Link>
          </div>
        </section>

        <section className="adm-section">
          <h3>🤖 Agent 使用排行（30 天）</h3>
          {rank.length === 0 ? (
            <Skeleton lines={4} />
          ) : (
            <div className="adm-rank-list">
              {rank.map((r, i) => (
                <div key={r.agent_id} className="adm-rank-item">
                  <span className={`adm-rank-num ${i < 3 ? "top" : ""}`}>#{i + 1}</span>
                  <div style={{ flex: 1 }}>
                    <div style={{ fontSize: 13, fontWeight: 500 }}>
                      {r.icon} {r.name}
                    </div>
                    <div style={{ fontSize: 10, color: "var(--text-muted)", margin: "4px 0" }}>
                      {r.messages} 条消息 · 满意度 {(r.satisfaction * 100).toFixed(0)}%
                    </div>
                    <div className="adm-rank-bar">
                      <div className="adm-rank-bar-fill" style={{ width: `${(r.messages / maxRank) * 100}%` }} />
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </section>
      </div>
    </div>
  );
}

function Stat({ label, val, color }: { label: string; val: number | string; color: string }) {
  return (
    <div className="adm-stat">
      <div className="adm-stat-label">{label}</div>
      <div className="adm-stat-val" style={{ color }}>
        {val}
      </div>
    </div>
  );
}

function fmt(iso?: string | null): string {
  if (!iso) return "-";
  const d = new Date(iso);
  return d.toLocaleDateString();
}
