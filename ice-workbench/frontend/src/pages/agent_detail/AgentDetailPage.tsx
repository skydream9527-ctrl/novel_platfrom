import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { adminApi, agentApi, taskApi } from "@/api/endpoints";
import type { AgentCard } from "@/types/api";
import type { AdminAgent, AgentPromptSnapshot } from "@/api/endpoints";
import { TopNav } from "@/components/shell/TopNav";
import { ErrorState } from "@/components/feedback/ErrorState";
import { Skeleton } from "@/components/feedback/Skeleton";
import { useAuthStore } from "@/stores/authStore";
import { useUIStore } from "@/stores/uiStore";
import { MarkdownRenderer } from "@/components/markdown/MarkdownRenderer";
import "./AgentDetail.css";

export function AgentDetailPage() {
  const { agentId = "" } = useParams<{ agentId: string }>();
  const navigate = useNavigate();
  const me = useAuthStore((s) => s.user);
  const pushToast = useUIStore((s) => s.pushToast);
  const isAdmin = me?.auth_role === "admin" || me?.auth_role === "super_admin";

  const [agent, setAgent] = useState<AgentCard | null>(null);
  const [adminAgent, setAdminAgent] = useState<AdminAgent | null>(null);
  const [history, setHistory] = useState<AgentPromptSnapshot[]>([]);
  const [editingPrompt, setEditingPrompt] = useState<string>("");
  const [changeNote, setChangeNote] = useState<string>("");
  const [savingPrompt, setSavingPrompt] = useState(false);
  const [testInput, setTestInput] = useState("");
  const [testOutput, setTestOutput] = useState<string | null>(null);
  const [testRunning, setTestRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setError(null);
    agentApi.get(agentId).then(setAgent).catch((e) => setError(e.message));
    if (isAdmin) {
      adminApi
        .getAgent(agentId)
        .then((a) => {
          setAdminAgent(a);
          setEditingPrompt(a.system_prompt || "");
        })
        .catch(() => {});
      adminApi
        .promptHistory(agentId)
        .then((r) => setHistory(r.items))
        .catch(() => {});
    }
  }, [agentId, isAdmin]);

  const startTask = async () => {
    if (!agent) return;
    try {
      const t = await taskApi.create({
        name: `用 ${agent.name} 创建的任务 · ${new Date().toLocaleDateString()}`,
        paradigm: agent.paradigm,
        agent_id: agent.id,
        visibility: "private",
      });
      navigate(`/workspace/${t.id}`);
    } catch (err) {
      pushToast("error", (err as Error).message);
    }
  };

  const savePrompt = async () => {
    if (!isAdmin) return;
    setSavingPrompt(true);
    try {
      await adminApi.updateAgent(agentId, {
        system_prompt: editingPrompt,
        change_note: changeNote || undefined,
      });
      pushToast("success", "Prompt 已保存");
      setChangeNote("");
      const r = await adminApi.promptHistory(agentId);
      setHistory(r.items);
    } catch (err) {
      pushToast("error", (err as Error).message);
    } finally {
      setSavingPrompt(false);
    }
  };

  const rollback = async (snap: AgentPromptSnapshot) => {
    try {
      await adminApi.promptRollback(agentId, snap.id);
      pushToast("success", "已回滚");
      const a = await adminApi.getAgent(agentId);
      setAdminAgent(a);
      setEditingPrompt(a.system_prompt || "");
      const r = await adminApi.promptHistory(agentId);
      setHistory(r.items);
    } catch (err) {
      pushToast("error", (err as Error).message);
    }
  };

  const testChat = async () => {
    if (!testInput.trim()) return;
    setTestRunning(true);
    setTestOutput(null);
    try {
      const r = await adminApi.testChat(agentId, {
        content: testInput,
        system_prompt: editingPrompt,
      });
      setTestOutput(r.response);
    } catch (err) {
      const e = err as { errorCode?: string; message: string };
      setTestOutput(`[${e.errorCode || "ERROR"}] ${e.message}`);
    } finally {
      setTestRunning(false);
    }
  };

  if (error) {
    return (
      <div className="ad-page">
        <TopNav mode="workspace" crumb={<span>首页 / Agent</span>} />
        <div className="ad-main">
          <ErrorState icon="🚫" title="Agent 加载失败" description={error} errorCode="AGENT_LOAD_FAILED" />
        </div>
      </div>
    );
  }

  if (!agent) {
    return (
      <div className="ad-page">
        <TopNav mode="workspace" crumb={<span>首页 / Agent</span>} />
        <div className="ad-main">
          <Skeleton lines={6} />
        </div>
      </div>
    );
  }

  return (
    <div className="ad-page">
      <TopNav
        mode="workspace"
        crumb={
          <span>
            首页 / Agent / <span className="current">{agent.name}</span>
          </span>
        }
      />

      <main className="ad-main">
        <header className="ad-header">
          <div className="ad-icon" style={{ background: `${agent.color}22`, color: agent.color }}>
            {agent.icon}
          </div>
          <div className="ad-meta">
            <h1>{agent.name}</h1>
            <div className="ad-paradigm">{agent.paradigm}</div>
            <p>{agent.description}</p>
          </div>
          <button className="btn-primary ad-start-desktop" onClick={startTask}>
            + 用此 Agent 创建任务
          </button>
        </header>

        <section className="ad-section">
          <h2>能力</h2>
          <p className="ad-section-desc">该 Agent 在对话中可调用以下 Skills（5 轮上限）。</p>
          <ul className="ad-skill-list">
            <li>📅 当前时间（now）</li>
            <li>🪞 回声测试（echo）</li>
            <li>🗃 SQL 查询（kyuubi_query）</li>
          </ul>
        </section>

        <section className="ad-section">
          <h2>System Prompt</h2>
          {!isAdmin ? (
            <div className="ad-prompt-readonly">
              <MarkdownRenderer content={"```\n" + (adminAgent?.system_prompt || "（无访问权限查看）") + "\n```"} />
            </div>
          ) : (
            <>
              <textarea
                className="ad-prompt-edit"
                value={editingPrompt}
                onChange={(e) => setEditingPrompt(e.target.value)}
                rows={14}
              />
              <div className="ad-prompt-actions">
                <input
                  className="ad-note"
                  placeholder="变更说明（可选）"
                  value={changeNote}
                  onChange={(e) => setChangeNote(e.target.value)}
                />
                <button className="btn-primary" disabled={savingPrompt} onClick={savePrompt}>
                  {savingPrompt ? "保存中…" : "💾 保存 Prompt"}
                </button>
              </div>
            </>
          )}
        </section>

        {isAdmin && (
          <section className="ad-section ad-admin">
            <h2>🛡 管理区</h2>

            <h3>📜 版本历史（{history.length}）</h3>
            <div className="ad-history">
              {history.length === 0 && <div className="ad-empty">暂无历史版本</div>}
              {history.map((h) => (
                <div key={h.id} className="ad-history-row">
                  <div className="ad-history-time">{new Date(h.saved_at).toLocaleString()}</div>
                  <div className="ad-history-meta">
                    {h.saved_by_name || h.saved_by} · {h.change_note || "(无说明)"}
                  </div>
                  <div className="ad-history-actions">
                    <button onClick={() => setEditingPrompt(h.system_prompt)}>预览</button>
                    <button onClick={() => rollback(h)}>↩ 回滚</button>
                  </div>
                </div>
              ))}
            </div>

            <h3>🧪 测试沙盒</h3>
            <p className="ad-section-desc">不入对话历史 / 不计费。用上方编辑中的 Prompt 试跑。</p>
            <div className="ad-test">
              <textarea
                rows={3}
                placeholder="例如：上周新版本 DAU 提升的归因思路？"
                value={testInput}
                onChange={(e) => setTestInput(e.target.value)}
              />
              <div className="ad-test-actions">
                <button className="btn-primary" disabled={testRunning} onClick={testChat}>
                  {testRunning ? "执行中…" : "▶ 试跑"}
                </button>
              </div>
              {testOutput !== null && (
                <div className="ad-test-output">
                  <MarkdownRenderer content={testOutput} />
                </div>
              )}
            </div>
          </section>
        )}
      </main>

      {/* 移动端粘底启动栏：桌面端通过 CSS 隐藏；避免主操作被折叠在滚动外。 */}
      <div className="ad-start-sticky">
        <button className="btn-primary" onClick={startTask}>
          🚀 用此 Agent 创建任务
        </button>
      </div>
    </div>
  );
}
