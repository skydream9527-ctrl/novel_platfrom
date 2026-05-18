import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { agentApi, conversationApi, fileApi, shareApi, taskApi } from "@/api/endpoints";
import { TopNav } from "@/components/shell/TopNav";
import { ChatInput } from "@/components/chat/ChatInput";
import { CrystallizeModal } from "@/components/chat/CrystallizeModal";
import { MessageList } from "@/components/chat/MessageList";
import { ModelSelector } from "@/components/chat/ModelSelector";
import { ErrorState } from "@/components/feedback/ErrorState";
import { Skeleton } from "@/components/feedback/Skeleton";
import AgentUpdateBanner from "@/components/task/AgentUpdateBanner";
import ConversationTab from "@/components/task/ConversationTab";
import ImportLinkDialog from "@/components/task/ImportLinkDialog";
import JoinRequestPanel from "@/components/task/JoinRequestPanel";
import { useChatSocket } from "@/hooks/useChatSocket";
import { useFileUpload } from "@/hooks/useFileUpload";
import { useAuthStore } from "@/stores/authStore";
import { useUIStore } from "@/stores/uiStore";
import type {
  AgentCard,
  ChatMessage,
  FileMeta,
  TaskDetail,
} from "@/types/api";
import "./Workspace.css";

/**
 * 推导当前用户在任务中的角色。与后端 derive_task_role 对齐（见 spec §5）。
 * - admin / super_admin 全局管理员直接返回 "admin"
 * - owner_id 命中返回 "owner"
 * - collaborators 中 status==="active" 的条目按 role 返回
 * - 对公开任务返回 "viewer"（publish_status 判断交由后端）
 */
function deriveRole(
  task: TaskDetail,
  user: { id: string; auth_role?: string } | null,
): "owner" | "editor" | "viewer" | "admin" | null {
  if (!user) return null;
  if (user.auth_role === "admin" || user.auth_role === "super_admin") return "admin";
  if (task.owner_id === user.id) return "owner";
  const c = task.collaborators?.find((x) => x.user_id === user.id && x.status === "active");
  if (c?.role === "owner") return "owner";
  if (c?.role === "editor") return "editor";
  if (task.visibility === "public") return "viewer";
  return null;
}

export function WorkspacePage() {
  const { taskId = "" } = useParams<{ taskId: string }>();
  const pushToast = useUIStore((s) => s.pushToast);
  const currentUser = useAuthStore((s) => s.user);
  const [task, setTask] = useState<TaskDetail | null>(null);
  const [agent, setAgent] = useState<AgentCard | null>(null);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [history, setHistory] = useState<ChatMessage[]>([]);
  const [files, setFiles] = useState<FileMeta[]>([]);
  const [activeRightTab, setActiveRightTab] = useState<"file" | "config" | "agent" | "conv">("agent");
  const [activeFile, setActiveFile] = useState<FileMeta | null>(null);
  const [activeContent, setActiveContent] = useState<string | null>(null);
  const [loadErr, setLoadErr] = useState<string | null>(null);
  const [crystallizeFor, setCrystallizeFor] = useState<ChatMessage | null>(null);
  const [mobileSidebar, setMobileSidebar] = useState(false);
  const [mobileRight, setMobileRight] = useState(false);
  const [mobileActionsOpen, setMobileActionsOpen] = useState(false);
  const [model, setModel] = useState<string>("");
  const [importOpen, setImportOpen] = useState(false);

  const socket = useChatSocket({
    taskId,
    conversationId,
    onError: (code, msg) => pushToast("error", `${msg}（${code}）`),
    onFileCreated: () => {
      fileApi
        .listTask(taskId)
        .then((r) => setFiles(r.items))
        .catch(() => {});
    },
  });

  const upload = useFileUpload({
    taskId,
    onSuccess: (m) => {
      setFiles((arr) => [m, ...arr]);
      pushToast("success", `${m.name} 已上传`);
    },
  });

  useEffect(() => {
    let cancelled = false;
    setLoadErr(null);
    Promise.all([
      taskApi.detail(taskId),
      taskApi.conversation(taskId),
      fileApi.listTask(taskId),
    ])
      .then(async ([t, conv, fs]) => {
        if (cancelled) return;
        setTask(t);
        setConversationId(conv.conversation_id);
        setHistory(conv.messages);
        setFiles(fs.items);
        if (t.workspace?.model) setModel(t.workspace.model);
        if (t.agent_id) {
          try {
            const a = await agentApi.get(t.agent_id);
            setAgent(a);
          } catch {
            /* ignore */
          }
        }
      })
      .catch((e) => setLoadErr(e.message));
    return () => {
      cancelled = true;
    };
  }, [taskId]);

  const openFile = async (f: FileMeta) => {
    setActiveRightTab("file");
    setActiveFile(f);
    setActiveContent(null);
    try {
      const r = await fileApi.read(taskId, f.id);
      setActiveContent(r.binary ? "[二进制文件，无法预览]" : r.content || "");
    } catch (err) {
      setActiveContent(`加载失败：${(err as Error).message}`);
    }
  };

  const removeFile = async (f: FileMeta) => {
    try {
      await fileApi.remove(taskId, f.id);
      setFiles((arr) => arr.filter((x) => x.id !== f.id));
      if (activeFile?.id === f.id) {
        setActiveFile(null);
        setActiveContent(null);
      }
    } catch (err) {
      pushToast("error", (err as Error).message);
    }
  };

  // 重新拉取任务/对话/文件（不做 location.reload，避免断 WS 与丢未保存状态）。
  const refreshTaskData = async () => {
    try {
      const [t, conv, fs] = await Promise.all([
        taskApi.detail(taskId),
        taskApi.conversation(taskId),
        fileApi.listTask(taskId),
      ]);
      setTask(t);
      setConversationId(conv.conversation_id);
      setHistory(conv.messages);
      setFiles(fs.items);
      pushToast("success", "已刷新");
    } catch (err) {
      pushToast("error", (err as Error).message);
    }
  };

  // 把当前对话（含工具调用摘要）导出为 Markdown 并触发浏览器下载。
  const exportConversation = () => {
    try {
      const messages: ChatMessage[] = [...history, ...socket.finalized];
      const lines: string[] = [];
      lines.push(`# ${task?.name || "对话导出"}`);
      lines.push("");
      lines.push(`- Agent：${agent?.name || task?.agent_id || "-"}`);
      lines.push(`- 任务 ID：${taskId}`);
      lines.push(`- 导出时间：${new Date().toLocaleString()}`);
      lines.push(`- 消息条数：${messages.length}`);
      lines.push("");
      lines.push("---");
      lines.push("");

      for (const m of messages) {
        const role = m.role === "user" ? "👤 用户" : m.role === "assistant" ? "🤖 Agent" : m.role;
        const ts = m.created_at ? new Date(m.created_at).toLocaleString() : "";
        lines.push(`## ${role}${ts ? ` · ${ts}` : ""}`);
        lines.push("");
        if (m.content) {
          lines.push(m.content);
          lines.push("");
        }
        const tools = m.tool_uses || [];
        if (tools.length > 0) {
          lines.push("**🛠 工具调用**");
          lines.push("");
          for (const tu of tools) {
            const argStr = (() => {
              try {
                return "```json\n" + JSON.stringify(tu.input ?? {}, null, 2) + "\n```";
              } catch {
                return String(tu.input ?? "");
              }
            })();
            lines.push(`- \`${tu.name}\``);
            lines.push(argStr);
          }
          lines.push("");
        }
        lines.push("---");
        lines.push("");
      }

      const blob = new Blob([lines.join("\n")], { type: "text/markdown;charset=utf-8" });
      const url = URL.createObjectURL(blob);
      const safeName = (task?.name || "conversation").replace(/[\\/:*?"<>|]/g, "_");
      const stamp = new Date().toISOString().replace(/[:T]/g, "-").slice(0, 16);
      const a = document.createElement("a");
      a.href = url;
      a.download = `${safeName}-${stamp}.md`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      pushToast("success", "对话已导出为 Markdown");
    } catch (err) {
      pushToast("error", (err as Error).message);
    }
  };

  if (loadErr) {
    return (
      <div className="ws">
        <TopNav mode="workspace" />
        <div className="ws-error">
          <ErrorState icon="🚫" title="任务加载失败" description={loadErr} errorCode="TASK_LOAD_FAILED" />
        </div>
      </div>
    );
  }

  if (!task) {
    return (
      <div className="ws">
        <TopNav mode="workspace" />
        <div className="ws-loading">
          <Skeleton lines={6} />
        </div>
      </div>
    );
  }

  const allMessages: ChatMessage[] = [...history, ...socket.finalized];
  const wsErrCode = socket.errorCode;
  const isStreaming = ["streaming", "tool", "typing"].includes(socket.phase);
  const role = deriveRole(task, currentUser);
  const canWrite = role === "editor" || role === "owner" || role === "admin";

  return (
    <div className="ws">
      <TopNav
        mode="workspace"
        crumb={
          <span>
            首页 / <span className="current">{task.name}</span>
          </span>
        }
        agentChip={
          agent ? (
            <span>
              {agent.icon} {agent.name} · <span style={{ color: "var(--text-muted)" }}>{agent.paradigm}</span>
            </span>
          ) : null
        }
        rightActions={
          <ShareToggle
            taskId={taskId}
            visibility={task.visibility}
            publishStatus={(task as any).publish_status}
            onChanged={async () => {
              const t = await taskApi.detail(taskId);
              setTask(t);
            }}
          />
        }
      />

      <div className="ws-body">
        <aside className={`ws-sidebar ${mobileSidebar ? "mobile-open" : ""}`}>
          <div className="ws-sb-section">
            <div className="ws-sb-head">
              <span>📂 工作文件</span>
              <label className="ws-upload">
                + 上传
                <input
                  type="file"
                  multiple
                  onChange={(e) => {
                    if (e.target.files) upload.upload(e.target.files);
                    e.target.value = "";
                  }}
                />
              </label>
              <button
                className="btn-ghost ws-import-btn"
                onClick={() => setImportOpen(true)}
                title="从飞书文档 / 知识库链接导入文件"
              >
                🔗 导入链接
              </button>
            </div>
            {files.length === 0 && upload.items.length === 0 ? (
              <div className="ws-empty">还没有文件，拖拽或点击上传</div>
            ) : (
              <ul className="ws-file-list">
                {files.map((f) => {
                  const isImported = f.scope === "imported";
                  return (
                    <li key={f.id} onClick={() => openFile(f)}>
                      <span className="fl-icon" title={isImported ? "已导入链接" : undefined}>
                        {isImported ? "🔗" : fmtIcon(f.format)}
                      </span>
                      <span
                        className="fl-name"
                        title={isImported && f.source_url ? f.source_url : f.name}
                      >
                        {f.name}
                      </span>
                      <span className="fl-size">{fmtSize(f.size_bytes)}</span>
                      {isImported && (
                        <button
                          className="fl-refresh"
                          onClick={async (e) => {
                            e.stopPropagation();
                            try {
                              await fileApi.refresh(taskId, f.file_id ?? f.id);
                              const r = await fileApi.listTask(taskId);
                              setFiles(r.items);
                              pushToast("success", `${f.name} 已刷新`);
                            } catch (err) {
                              alert(`刷新失败：${(err as Error).message}`);
                            }
                          }}
                          title="重新抓取最新内容"
                        >
                          ↻
                        </button>
                      )}
                      <button
                        className="fl-del"
                        onClick={(e) => {
                          e.stopPropagation();
                          removeFile(f);
                        }}
                        title="删除"
                      >
                        ×
                      </button>
                    </li>
                  );
                })}
                {upload.items
                  .filter((u) => u.status !== "done")
                  .map((u, i) => (
                    <li key={`u${i}`} className="ws-upload-row">
                      <span className="fl-icon">⏳</span>
                      <span className="fl-name">{u.name}</span>
                      <span className="fl-size">
                        {u.status === "uploading" ? `${u.percent}%` : u.message || "失败"}
                      </span>
                    </li>
                  ))}
              </ul>
            )}
          </div>
        </aside>

        <main className="ws-main">
          <div className="ws-chat-head">
            <button className="ws-mobile-toggle" onClick={() => setMobileSidebar(!mobileSidebar)}>
              📂 文件
            </button>
            <span className="model">
              📦 <ModelSelector value={model} onChange={setModel} compact />
            </span>
            <button
              className="btn-ghost ws-sec-action"
              onClick={exportConversation}
              title="把当前对话（含工具调用）导出为 Markdown 下载"
            >
              💾 导出对话
            </button>
            <button
              className="btn-ghost ws-sec-action"
              onClick={refreshTaskData}
              title="重新拉取任务详情 / 对话历史 / 文件（保持 WS 连接）"
            >
              🔁 重新加载
            </button>
            {/* 移动端：上面两个按钮被 CSS 隐藏，用"⋯"弹出菜单替代 */}
            <div className="ws-sec-more">
              <button
                className="ws-mobile-toggle"
                onClick={() => setMobileActionsOpen((v) => !v)}
                aria-label="更多"
              >
                ⋯
              </button>
              {mobileActionsOpen && (
                <>
                  <div
                    className="ws-sec-more-mask"
                    onClick={() => setMobileActionsOpen(false)}
                  />
                  <div className="ws-sec-more-menu" role="menu">
                    <button
                      onClick={() => {
                        setMobileActionsOpen(false);
                        exportConversation();
                      }}
                    >
                      💾 导出对话
                    </button>
                    <button
                      onClick={() => {
                        setMobileActionsOpen(false);
                        refreshTaskData();
                      }}
                    >
                      🔁 重新加载
                    </button>
                  </div>
                </>
              )}
            </div>
            <button className="ws-mobile-toggle" onClick={() => setMobileRight(!mobileRight)}>
              🤖 详情
            </button>
          </div>
          <AgentUpdateBanner
            task={task}
            isOwnerOrAdmin={role === "owner" || role === "admin"}
            onUpdated={async () => {
              const t = await taskApi.detail(taskId);
              setTask(t);
            }}
          />
          {wsErrCode && (
            <div className="ws-banner">
              <ErrorState
                icon="⚠"
                title="对话异常"
                description={
                  wsErrCode === "LLM_KEY_MISSING"
                    ? "LLM API Key 未配置，请在 .env 填入 ANTHROPIC_API_KEY 后重启后端"
                    : wsErrCode === "WS_DISCONNECTED"
                      ? "WebSocket 已断开，正在尝试重连…"
                      : "请稍后重试"
                }
                errorCode={wsErrCode}
                actions={
                  <button className="btn-secondary" onClick={socket.clearError}>
                    我知道了
                  </button>
                }
              />
            </div>
          )}
          <MessageList
            finalized={allMessages}
            partial={socket.partial}
            phase={socket.phase}
            onCrystallize={(m) => setCrystallizeFor(m)}
          />
          <ChatInput
            paradigm={task.paradigm}
            disabled={!conversationId}
            isStreaming={isStreaming}
            onSend={(text) => socket.send(text, { model })}
            onAbort={socket.abort}
          />
        </main>

        <aside className={`ws-right ${mobileRight ? "mobile-open" : ""}`}>
          <div className="ws-right-tabs">
            {(
              [
                { k: "agent", label: "🤖 Agent" },
                { k: "file", label: "📄 文件" },
                { k: "conv", label: "💬 对话" },
                { k: "config", label: "⚙ 配置" },
              ] as const
            ).map((t) => (
              <button
                key={t.k}
                className={activeRightTab === t.k ? "active" : ""}
                onClick={() => setActiveRightTab(t.k)}
              >
                {t.label}
              </button>
            ))}
          </div>
          <div className="ws-right-body">
            {activeRightTab === "agent" && (
              <div className="ws-agent-tab">
                {agent ? (
                  <>
                    <div className="ws-agent-head">
                      <span style={{ fontSize: 28 }}>{agent.icon}</span>
                      <div>
                        <div className="ws-agent-name">{agent.name}</div>
                        <div className="ws-agent-paradigm">{agent.paradigm}</div>
                      </div>
                    </div>
                    <p className="ws-agent-desc">{agent.description}</p>
                  </>
                ) : (
                  <div className="ws-empty">未绑定 Agent</div>
                )}
              </div>
            )}
            {activeRightTab === "file" && (
              <div className="ws-file-tab">
                {!activeFile ? (
                  <div className="ws-empty">从左栏点击文件查看预览</div>
                ) : (
                  <>
                    <div className="ws-file-head">
                      <span className="ws-file-name">{activeFile.name}</span>
                      <button
                        className="btn-ghost"
                        onClick={() => {
                          setActiveFile(null);
                          setActiveContent(null);
                        }}
                      >
                        ×
                      </button>
                    </div>
                    {activeContent === null ? (
                      <Skeleton lines={6} />
                    ) : (
                      <pre className="ws-file-pre">{activeContent}</pre>
                    )}
                  </>
                )}
              </div>
            )}
            {activeRightTab === "conv" && (
              <div className="ws-conv-tab">
                <ConversationTab
                  taskId={taskId}
                  currentConvId={conversationId}
                  canWrite={canWrite}
                  onSelect={async (cid) => {
                    setConversationId(cid);
                    try {
                      const data = await conversationApi.get(taskId, cid);
                      setHistory(data.messages);
                    } catch (err: any) {
                      alert("加载对话历史失败: " + (err?.response?.data?.message ?? String(err)));
                    }
                  }}
                />
              </div>
            )}
            {activeRightTab === "config" && (
              <div className="ws-config-tab">
                <div className="cfg-row">
                  <span>范式</span>
                  <span>{task.paradigm}</span>
                </div>
                <div className="cfg-row">
                  <span>状态</span>
                  <span>{task.status}</span>
                </div>
                <div className="cfg-row">
                  <span>模型</span>
                  <span style={{ fontFamily: "var(--font-mono)", fontSize: 11 }}>
                    {model || task.workspace?.model || "(default)"}
                  </span>
                </div>
                <div className="cfg-row">
                  <span>可见性</span>
                  <span>{task.visibility}</span>
                </div>
                <div className="cfg-row">
                  <span>初始 Prompt</span>
                  <span style={{ fontSize: 12, color: "var(--text-dim)" }}>
                    {task.initial_prompt || "-"}
                  </span>
                </div>
                <JoinRequestPanel
                  taskId={taskId}
                  role={role ?? "viewer"}
                  onJoined={async () => {
                    const t = await taskApi.detail(taskId);
                    setTask(t);
                  }}
                />
              </div>
            )}
          </div>
        </aside>
      </div>

      <CrystallizeModal
        open={!!crystallizeFor}
        taskId={taskId}
        sourceMessage={crystallizeFor && { id: crystallizeFor.id, content: crystallizeFor.content }}
        onClose={() => setCrystallizeFor(null)}
      />

      <ImportLinkDialog
        open={importOpen}
        taskId={taskId}
        onClose={() => setImportOpen(false)}
        onImported={async () => {
          try {
            const f = await fileApi.listTask(taskId);
            setFiles(f.items);
          } catch (err) {
            pushToast("error", (err as Error).message);
          }
        }}
      />
    </div>
  );
}

function ShareToggle({
  taskId,
  visibility,
  publishStatus,
  onChanged,
}: {
  taskId: string;
  visibility: string;
  publishStatus?: string;
  onChanged: () => void | Promise<void>;
}) {
  const pushToast = useUIStore((s) => s.pushToast);
  const [busy, setBusy] = useState(false);
  const isPublic = visibility === "public";
  const isPending = publishStatus === "pending";
  const isRejected = publishStatus === "rejected";
  const click = async () => {
    setBusy(true);
    try {
      if (isPublic) {
        await shareApi.unshare(taskId);
        pushToast("success", "已撤回到私有");
      } else {
        const r = await shareApi.share(taskId);
        pushToast(
          r.publish_status === "pending" ? "info" : "success",
          r.publish_status === "pending" ? "已提交审核，admin 通过后才会展示" : "已发布到公共区",
        );
      }
      await onChanged();
    } catch (err) {
      pushToast("error", (err as Error).message);
    } finally {
      setBusy(false);
    }
  };
  return (
    <button
      className="btn-ghost"
      onClick={click}
      disabled={busy}
      title={isPending ? "审核中" : isRejected ? "审核未通过，可重新分享" : isPublic ? "撤回到私有" : "分享到公共区"}
    >
      {isPending ? "🕓 审核中" : isRejected ? "🚫 已驳回" : isPublic ? "🔗 已分享" : "🔗 分享"}
    </button>
  );
}

function fmtIcon(fmt?: string | null): string {
  switch ((fmt || "").toLowerCase()) {
    case "md":
    case "txt":
      return "📝";
    case "csv":
    case "tsv":
      return "📊";
    case "json":
      return "🧾";
    case "py":
      return "🐍";
    case "sql":
      return "🗃";
    case "png":
    case "jpg":
    case "jpeg":
      return "🖼";
    default:
      return "📄";
  }
}

function fmtSize(n: number): string {
  if (n < 1024) return `${n} B`;
  if (n < 1024 * 1024) return `${(n / 1024).toFixed(1)} KB`;
  return `${(n / 1024 / 1024).toFixed(1)} MB`;
}
