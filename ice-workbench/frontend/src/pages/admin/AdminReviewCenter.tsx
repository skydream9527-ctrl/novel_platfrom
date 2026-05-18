import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { reviewApi } from "@/api/endpoints";
import type { ReviewSummary } from "@/api/endpoints";
import { Skeleton } from "@/components/feedback/Skeleton";

export function AdminReviewCenter() {
  const [s, setSummary] = useState<ReviewSummary | null>(null);

  useEffect(() => {
    reviewApi.summary().then(setSummary).catch(() => {});
  }, []);

  if (!s) {
    return (
      <div>
        <div className="adm-page-head">
          <h1>📥 审核中心</h1>
          <p>聚合所有待办：经验卡片 / 公共任务 / 任务模板</p>
        </div>
        <Skeleton lines={4} />
      </div>
    );
  }

  const total = s.experience_cards_pending + s.public_tasks_pending + s.templates_pending;

  return (
    <div>
      <div className="adm-page-head">
        <h1>📥 审核中心</h1>
        <p>
          聚合所有待办（共 <strong style={{ color: total > 0 ? "var(--warning)" : "var(--success)" }}>{total}</strong> 项）
        </p>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(260px, 1fr))", gap: 14 }}>
        <ReviewCard
          icon="💡"
          title="经验卡片"
          count={s.experience_cards_pending}
          to="/admin/experience-cards"
          desc="批准后自动注入 Agent system prompt"
          color="var(--p-biz)"
        />
        <ReviewCard
          icon="🌐"
          title="公共任务"
          count={s.public_tasks_pending}
          to="/admin/public-tasks"
          desc="用户共享的任务，审核通过后展示在公共区"
          color="var(--p-data)"
        />
        <ReviewCard
          icon="📋"
          title="任务模板"
          count={s.templates_pending}
          to="/admin/agents"
          desc="待审核的公共模板（继承到 /admin/templates 页，下轮交付）"
          color="var(--agent)"
        />
      </div>

      {total === 0 && (
        <div className="adm-section" style={{ marginTop: 24, textAlign: "center", color: "var(--success)" }}>
          🎉 没有待办事项
        </div>
      )}
    </div>
  );
}

function ReviewCard({
  icon,
  title,
  count,
  to,
  desc,
  color,
}: {
  icon: string;
  title: string;
  count: number;
  to: string;
  desc: string;
  color: string;
}) {
  return (
    <Link
      to={to}
      style={{
        background: "var(--surface)",
        border: `1px solid ${count > 0 ? color : "var(--border)"}`,
        borderLeft: `3px solid ${color}`,
        borderRadius: "var(--radius)",
        padding: 18,
        textDecoration: "none",
        color: "var(--text)",
        display: "flex",
        flexDirection: "column",
        gap: 8,
        transition: "all .18s",
      }}
    >
      <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
        <span style={{ fontSize: 22 }}>{icon}</span>
        <span style={{ fontFamily: "var(--font-head)", fontSize: 15, fontWeight: 600 }}>{title}</span>
        <span
          style={{
            marginLeft: "auto",
            fontFamily: "var(--font-head)",
            fontSize: 22,
            fontWeight: 700,
            color: count > 0 ? color : "var(--text-muted)",
          }}
        >
          {count}
        </span>
      </div>
      <div style={{ fontSize: 12, color: "var(--text-dim)", lineHeight: 1.5 }}>{desc}</div>
      <div style={{ fontSize: 11, color, marginTop: "auto" }}>→ 立即审核</div>
    </Link>
  );
}
