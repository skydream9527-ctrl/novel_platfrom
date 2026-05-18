import { useEffect, useState } from "react";
import { adminApi } from "@/api/endpoints";
import { Skeleton } from "@/components/feedback/Skeleton";

interface AuditRow {
  id: string;
  admin_id: string;
  action: string;
  target_type: string;
  target_id: string;
  created_at: string;
  diff: unknown;
}

export function AdminAuditLogs() {
  const [items, setItems] = useState<AuditRow[]>([]);
  const [loading, setLoading] = useState(true);
  useEffect(() => {
    adminApi
      .auditLogs(200)
      .then((r) => setItems(r.items as AuditRow[]))
      .finally(() => setLoading(false));
  }, []);
  return (
    <div>
      <div className="adm-page-head">
        <h1>📜 审计日志</h1>
        <p>所有 admin 写操作记录在 users/&#123;uid&#125;/audit/&#123;YYYY-MM&#125;.jsonl</p>
      </div>
      {loading ? (
        <Skeleton lines={6} />
      ) : items.length === 0 ? (
        <div style={{ padding: 32, textAlign: "center", color: "var(--text-muted)" }}>
          本月暂无审计记录
        </div>
      ) : (
        <div className="adm-audit-log">
          {items.map((r) => (
            <details key={r.id} className="adm-audit-row">
              <summary
                style={{
                  display: "grid",
                  gridTemplateColumns: "180px 100px 100px 1fr",
                  alignItems: "center",
                  cursor: "pointer",
                  width: "100%",
                }}
              >
                <span className="adm-audit-time">{new Date(r.created_at).toLocaleString()}</span>
                <span className="adm-audit-action">{r.action}</span>
                <span style={{ color: "var(--text-dim)" }}>{r.target_type}</span>
                <span style={{ fontFamily: "var(--font-mono)", fontSize: 11, color: "var(--text-muted)" }}>
                  {r.target_id.slice(0, 12)}…
                </span>
              </summary>
              <pre
                style={{
                  background: "var(--surface-2)",
                  padding: 10,
                  margin: "10px 0 0",
                  fontFamily: "var(--font-mono)",
                  fontSize: 11,
                  borderRadius: 4,
                  overflow: "auto",
                }}
              >
                {JSON.stringify(r.diff, null, 2)}
              </pre>
            </details>
          ))}
        </div>
      )}
    </div>
  );
}
