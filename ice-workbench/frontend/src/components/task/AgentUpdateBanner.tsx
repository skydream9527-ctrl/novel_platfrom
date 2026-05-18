import { useState } from "react";
import { agentSnapshotApi } from "@/api/endpoints";
import { useUIStore } from "@/stores/uiStore";
import type { TaskDetail } from "@/types/api";
import "./AgentUpdateBanner.css";

export interface AgentUpdateBannerProps {
  task: TaskDetail;
  isOwnerOrAdmin: boolean;
  onUpdated: () => void;
}

function AgentUpdateBanner({ task, isOwnerOrAdmin, onUpdated }: AgentUpdateBannerProps) {
  const pushToast = useUIStore((s) => s.pushToast);
  const [loading, setLoading] = useState(false);

  if (!isOwnerOrAdmin || !task.agent_update_available) return null;

  const handleRefresh = async () => {
    if (loading) return;
    setLoading(true);
    try {
      const expected = task.snapshot?.agent_source_version ?? null;
      const result = await agentSnapshotApi.refresh(task.id, expected);
      if (result.changed) {
        pushToast("success", "Agent 已更新到最新经验");
      } else {
        pushToast("info", "Agent 已是最新");
      }
      onUpdated();
    } catch (err: unknown) {
      const e = err as { response?: { data?: { error_code?: string; message?: string } } };
      const code = e?.response?.data?.error_code;
      if (code === "AGENT_SNAPSHOT_STALE") {
        pushToast("info", "快照已被他人更新，正在刷新…");
        onUpdated();
      } else {
        const msg = e?.response?.data?.message || "更新失败，请稍后重试";
        pushToast("error", msg);
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="agent-update-banner" role="status">
      <span className="aub-icon" aria-hidden="true">🆕</span>
      <span className="aub-text">Agent 有新经验可合入</span>
      <button
        className="aub-btn"
        type="button"
        onClick={handleRefresh}
        disabled={loading}
      >
        {loading ? "更新中…" : "更新 Agent"}
      </button>
    </div>
  );
}

export default AgentUpdateBanner;
