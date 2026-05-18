import { useEffect, useState } from "react";
import { conversationApi } from "@/api/endpoints";
import type { ConversationSummary } from "@/types/api";
import "./ConversationTab.css";

export interface ConversationTabProps {
  taskId: string;
  currentConvId: string | null;
  onSelect: (convId: string) => void;
  canWrite: boolean;
  reloadKey?: number;
}

function formatRelative(iso?: string): string {
  if (!iso) return "";
  const ts = new Date(iso).getTime();
  if (Number.isNaN(ts)) return "";
  const diff = Date.now() - ts;
  const sec = Math.floor(diff / 1000);
  if (sec < 60) return "刚刚";
  const min = Math.floor(sec / 60);
  if (min < 60) return `${min} 分钟前`;
  const hr = Math.floor(min / 60);
  if (hr < 24) return `${hr} 小时前`;
  const day = Math.floor(hr / 24);
  if (day < 7) return `${day} 天前`;
  return new Date(iso).toLocaleDateString();
}

function extractErrMsg(err: unknown, fallback: string): string {
  const e = err as { response?: { data?: { message?: string; error_code?: string } } };
  return e?.response?.data?.message || fallback;
}

function ConversationTab({
  taskId,
  currentConvId,
  onSelect,
  canWrite,
  reloadKey,
}: ConversationTabProps) {
  const [items, setItems] = useState<ConversationSummary[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = async () => {
    if (!taskId) return;
    setLoading(true);
    setError(null);
    try {
      const res = await conversationApi.list(taskId);
      const sorted = [...res.items].sort((a, b) => {
        const ta = new Date(a.last_message_at).getTime() || 0;
        const tb = new Date(b.last_message_at).getTime() || 0;
        return tb - ta;
      });
      setItems(sorted);
    } catch (err: unknown) {
      setError(extractErrMsg(err, "加载对话失败"));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [taskId, reloadKey]);

  const handleCreate = async () => {
    const input = window.prompt("新对话标题（可留空）", "");
    if (input === null) return;
    const title = input.trim() || "新对话";
    try {
      const created = await conversationApi.create(taskId, title);
      setItems((arr) => [created, ...arr]);
      onSelect(created.id);
    } catch (err: unknown) {
      alert(extractErrMsg(err, "创建对话失败"));
    }
  };

  const handleRename = async (conv: ConversationSummary) => {
    const input = window.prompt("重命名对话", conv.title);
    if (input === null) return;
    const title = input.trim();
    if (!title || title === conv.title) return;
    try {
      const updated = await conversationApi.rename(taskId, conv.id, title);
      setItems((arr) => arr.map((c) => (c.id === conv.id ? updated : c)));
    } catch (err: unknown) {
      alert(extractErrMsg(err, "重命名失败"));
    }
  };

  const handleDelete = async (conv: ConversationSummary) => {
    if (!window.confirm(`确定删除对话 "${conv.title}"？`)) return;
    try {
      await conversationApi.remove(taskId, conv.id);
      setItems((arr) => arr.filter((c) => c.id !== conv.id));
    } catch (err: unknown) {
      alert(extractErrMsg(err, "删除失败"));
    }
  };

  return (
    <div className="conv-tab">
      <div className="conv-tab-head">
        <span className="conv-tab-title">对话</span>
        {canWrite && (
          <button
            type="button"
            className="conv-tab-new"
            onClick={handleCreate}
          >
            + 新对话
          </button>
        )}
      </div>

      {loading && <div className="conv-tab-loading">加载中…</div>}
      {error && <div className="conv-tab-error">{error}</div>}

      {!loading && !error && items.length === 0 && (
        <div className="conv-tab-empty">暂无对话，点击新建开始</div>
      )}

      <ul className="conv-list">
        {items.map((c) => {
          const active = c.id === currentConvId;
          return (
            <li
              key={c.id}
              className={`conv-item${active ? " is-active" : ""}`}
              onClick={() => onSelect(c.id)}
            >
              <div className="conv-item-main">
                <div className="conv-item-title" title={c.title}>
                  {c.title || "未命名对话"}
                </div>
                <div className="conv-item-meta">
                  <span>{formatRelative(c.last_message_at)}</span>
                  <span className="conv-dot">·</span>
                  <span>{c.message_count} 条</span>
                </div>
              </div>
              {canWrite && (
                <div className="conv-item-actions">
                  <button
                    type="button"
                    className="conv-icon-btn"
                    title="重命名"
                    onClick={(e) => {
                      e.stopPropagation();
                      handleRename(c);
                    }}
                  >
                    ✎
                  </button>
                  <button
                    type="button"
                    className="conv-icon-btn conv-icon-danger"
                    title="删除"
                    onClick={(e) => {
                      e.stopPropagation();
                      handleDelete(c);
                    }}
                  >
                    🗑
                  </button>
                </div>
              )}
            </li>
          );
        })}
      </ul>
    </div>
  );
}

export default ConversationTab;
