import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { adminApi } from "@/api/endpoints";
import type { AdminAgent } from "@/api/endpoints";
import { Skeleton } from "@/components/feedback/Skeleton";

export function AdminAgents() {
  const [items, setItems] = useState<AdminAgent[]>([]);
  const [loading, setLoading] = useState(true);
  useEffect(() => {
    adminApi.listAgents().then((r) => setItems(r.items)).finally(() => setLoading(false));
  }, []);
  return (
    <div>
      <div className="adm-page-head">
        <h1>🤖 Agents</h1>
        <p>5 个内置 Agent，1:1 绑定工作范式</p>
      </div>
      {loading ? (
        <Skeleton lines={6} />
      ) : (
        <div className="adm-agent-grid">
          {items.map((a) => (
            <Link key={a.id} to={`/admin/agents/${a.id}`} className="adm-agent-card">
              <div className="adm-agent-icon" style={{ color: a.color }}>
                {a.icon}
              </div>
              <div className="adm-agent-name">{a.name}</div>
              <div className="adm-agent-paradigm">{a.paradigm}</div>
              <div className="adm-agent-desc">{a.description}</div>
              <div style={{ marginTop: "auto", fontSize: 11, color: "var(--text-muted)" }}>
                状态：{a.publish_status}
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
