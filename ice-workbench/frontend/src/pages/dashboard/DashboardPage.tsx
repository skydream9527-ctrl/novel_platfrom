import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { agentApi, fileApi, skillApi, taskApi, templateApi } from "@/api/endpoints";
import type { TemplateRecord } from "@/api/endpoints";
import { useAuthStore } from "@/stores/authStore";
import { useUIStore } from "@/stores/uiStore";
import { TopNav } from "@/components/shell/TopNav";
import { EmptyState } from "@/components/feedback/ErrorState";
import { Skeleton } from "@/components/feedback/Skeleton";
import { ConfirmModal } from "@/components/feedback/ConfirmModal";
import type { AgentCard, FileMeta, SkillCard, TaskSummary } from "@/types/api";
import "./Dashboard.css";

type PublicTab = "tasks" | "agents" | "skills" | "files" | "templates";

const AGENT_ORDER = [
  "general",
  "data-analysis",
  "ab-experiment",
  "gray-release",
  "biz-insight",
  "wave-attribution",
];

function sortAgents(list: AgentCard[]): AgentCard[] {
  return [...list].sort((a, b) => {
    const ia = AGENT_ORDER.indexOf(a.id);
    const ib = AGENT_ORDER.indexOf(b.id);
    return (ia === -1 ? 999 : ia) - (ib === -1 ? 999 : ib);
  });
}

export function DashboardPage() {
  const navigate = useNavigate();
  const user = useAuthStore((s) => s.user);
  const pushToast = useUIStore((s) => s.pushToast);
  const [agents, setAgents] = useState<AgentCard[]>([]);
  const [skills, setSkills] = useState<SkillCard[]>([]);
  const [tasks, setTasks] = useState<TaskSummary[]>([]);
  const [publicTasks, setPublicTasks] = useState<TaskSummary[]>([]);
  const [publicFiles, setPublicFiles] = useState<FileMeta[]>([]);
  const [publicTemplates, setPublicTemplates] = useState<TemplateRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [publicTab, setPublicTab] = useState<PublicTab>("tasks");
  const [confirmDelete, setConfirmDelete] = useState<TaskSummary | null>(null);
  const [deleting, setDeleting] = useState(false);

  useEffect(() => {
    Promise.all([
      agentApi.list().then((r) => setAgents(sortAgents(r.items))).catch(() => {}),
      skillApi.list().then((r) => setSkills(r.items)).catch(() => {}),
      taskApi.list().then((r) => setTasks(r.items)).catch(() => {}),
      taskApi.listPublic().then((r) => setPublicTasks(r.items)).catch(() => {}),
      fileApi.listPublic().then((r) => setPublicFiles(r.items)).catch(() => {}),
      templateApi.list("public").then((r) => setPublicTemplates(r.items)).catch(() => {}),
    ]).finally(() => setLoading(false));
  }, []);

  const startWith = (agent: AgentCard) => {
    navigate(`/create-task?paradigm=${agent.paradigm}&agentId=${agent.id}`);
  };

  const openPublicFile = (f: FileMeta) => {
    window.open(`/public-files/${f.id}`, "_blank", "noopener,noreferrer");
  };

  const deleteTask = async () => {
    if (!confirmDelete) return;
    setDeleting(true);
    try {
      await taskApi.remove(confirmDelete.id);
      setTasks((arr) => arr.filter((x) => x.id !== confirmDelete.id));
      pushToast("success", `已删除 "${confirmDelete.name}"`);
      setConfirmDelete(null);
    } catch (err) {
      pushToast("error", (err as Error).message);
    } finally {
      setDeleting(false);
    }
  };

  // 公共区 Skills 只展示 skills/ 目录下的真实 SKILL.md（即 category === "agentic"），
  // 内置工具（now/echo/write_file 等）不属于用户视角的 Skill，不暴露在公共区。
  const agenticSkills = skills.filter((s) => s.category === "agentic");

  return (
    <div className="dash">
      <TopNav
        mode="dashboard"
        rightActions={
          <>
            <button className="btn-primary" onClick={() => navigate("/create-task")}>
              + 新任务
            </button>
            <button className="btn-ghost" onClick={() => navigate("/scheduled-tasks")}>
              ⏱ 定时
            </button>
            <button className="btn-ghost" onClick={() => navigate("/guide")}>
              📖 指南
            </button>
            {(user?.auth_role === "admin" || user?.auth_role === "super_admin") && (
              <button className="btn-ghost" onClick={() => navigate("/admin")}>
                🛡 管理
              </button>
            )}
          </>
        }
      />
      <main className="dash-main">
        <div className="dash-welcome">
          <h1>👋 你好，{user?.name || "同学"}</h1>
          <p>选一个范式开始今天的工作</p>
        </div>

        <section className="dash-section dash-start">
          <div className="start-grid">
            <button
              className="start-card start-blank"
              onClick={() => navigate("/create-task?origin=blank")}
            >
              <div className="sc-icon">📝</div>
              <div className="sc-body">
                <div className="sc-name">空白任务</div>
                <div className="sc-desc">从 0 开始，自由配置</div>
              </div>
            </button>
            <button
              className="start-card start-open"
              onClick={() =>
                navigate("/create-task?origin=open&paradigm=open&agentId=general")
              }
            >
              <div className="sc-icon">🤖</div>
              <div className="sc-body">
                <div className="sc-name">开放任务</div>
                <div className="sc-desc">通用 Agent · 跨范式自由对话</div>
              </div>
            </button>
            <button
              className="start-card start-template"
              onClick={() => navigate("/create-task?origin=template")}
            >
              <div className="sc-icon">📋</div>
              <div className="sc-body">
                <div className="sc-name">从模板</div>
                <div className="sc-desc">复用我的或公共模板</div>
              </div>
            </button>
            <button
              className="start-card start-public"
              onClick={() => navigate("/create-task?origin=public")}
            >
              <div className="sc-icon">🌐</div>
              <div className="sc-body">
                <div className="sc-name">公共任务</div>
                <div className="sc-desc">参考团队已有任务</div>
              </div>
            </button>
          </div>
        </section>

        <section className="dash-section">
          <h2>⚡ 快速开始</h2>
          <div className="paradigm-grid">
            {loading
              ? Array.from({ length: 5 }).map((_, i) => (
                  <div key={i} className="paradigm-card">
                    <Skeleton lines={3} />
                  </div>
                ))
              : agents.map((a) => (
                  <button
                    key={a.id}
                    className="paradigm-card"
                    onClick={() => startWith(a)}
                    style={{ borderTopColor: a.color }}
                  >
                    <div className="pc-icon" style={{ background: `${a.color}22`, color: a.color }}>
                      {a.icon}
                    </div>
                    <div className="pc-name">{a.name}</div>
                    <div className="pc-desc">{a.description}</div>
                  </button>
                ))}
          </div>
        </section>

        <section className="dash-section">
          <h2>📋 我的任务</h2>
          {loading ? (
            <Skeleton lines={4} />
          ) : tasks.length === 0 ? (
            <EmptyState
              illustration="📋"
              title="还没有任务"
              hint="选择上方一个范式开始你的第一个任务"
            />
          ) : (
            <div className="task-grid">
              {tasks.map((t) => (
                <div
                  key={t.id}
                  className={`task-card ${paradigmClass(t.paradigm)}`}
                  role="button"
                  tabIndex={0}
                  onClick={() => navigate(`/workspace/${t.id}`)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter" || e.key === " ") {
                      e.preventDefault();
                      navigate(`/workspace/${t.id}`);
                    }
                  }}
                >
                  {t.role !== "collaborator" && (
                    <button
                      className="tc-delete"
                      title="删除任务"
                      onClick={(e) => {
                        e.stopPropagation();
                        setConfirmDelete(t);
                      }}
                    >
                      🗑
                    </button>
                  )}
                  <div className="tc-name">{t.name}</div>
                  <div className="tc-meta">
                    <span className="tc-paradigm">{t.paradigm}</span>
                    {t.role === "collaborator" && <span className="tc-collab">👥 协作</span>}
                  </div>
                  {t.last_message_preview && (
                    <div className="tc-preview">💬 “{t.last_message_preview}”</div>
                  )}
                  <div className="tc-foot">
                    ⏱ {formatTime(t.updated_at)} · 📄 {t.file_count}
                  </div>
                </div>
              ))}
            </div>
          )}
        </section>

        <section className="dash-section" id="public-zone">
          <h2>🌐 团队公共区</h2>
          <div className="public-tabs">
            {(
              [
                { k: "tasks", label: "📋 公共任务", count: publicTasks.length },
                { k: "agents", label: "🤖 Agents", count: agents.length },
                { k: "skills", label: "🧰 Skills", count: agenticSkills.length },
                { k: "files", label: "📁 公共文件", count: publicFiles.length },
                { k: "templates", label: "📑 任务模板", count: publicTemplates.length },
              ] as const
            ).map((t) => (
              <button
                key={t.k}
                className={`public-tab ${publicTab === t.k ? "active" : ""}`}
                onClick={() => setPublicTab(t.k)}
              >
                {t.label}
                <span className="public-tab-count">{t.count}</span>
              </button>
            ))}
          </div>

          {publicTab === "tasks" && (
            <div className="public-grid">
              {publicTasks.length === 0 ? (
                <EmptyState
                  illustration="🌐"
                  title="公共区暂无任务"
                  hint="同事在 Workspace 顶栏点 🔗 分享并通过审核后出现在这里"
                />
              ) : (
                publicTasks.map((t) => (
                  <button
                    key={t.id}
                    className="public-task-card"
                    onClick={() => navigate(`/workspace/${t.id}`)}
                  >
                    <div className="ptc-name">{t.name}</div>
                    <div className="ptc-meta">
                      {t.paradigm} · {t.last_message_preview ? "💬 已展开" : "📭 空"}
                    </div>
                  </button>
                ))
              )}
            </div>
          )}

          {publicTab === "agents" && (
            <div className="public-grid">
              {agents.length === 0 ? (
                <EmptyState illustration="🤖" title="暂无可用 Agent" />
              ) : (
                agents.map((a) => (
                  <button
                    key={a.id}
                    className="public-task-card"
                    onClick={() => navigate(`/agent/${a.id}`)}
                    style={{ borderLeft: `3px solid ${a.color}` }}
                  >
                    <div className="ptc-name">
                      {a.icon} {a.name}
                    </div>
                    <div className="ptc-meta">
                      {a.paradigm} · {a.description?.slice(0, 32) || ""}
                    </div>
                  </button>
                ))
              )}
            </div>
          )}

          {publicTab === "skills" && (
            <div className="public-grid">
              {agenticSkills.length === 0 ? (
                <EmptyState
                  illustration="🧰"
                  title="暂无 Skill"
                  hint="把 SKILL.md 放到仓库根目录的 skills/ 下即可在此展示"
                />
              ) : (
                agenticSkills.map((s) => {
                  const brief = skillBrief(s.description);
                  return (
                    <div
                      key={s.id}
                      className="public-task-card"
                      title={brief.full}
                    >
                      <div className="ptc-name">🧰 {brief.title || s.name}</div>
                      <div className="ptc-meta">{brief.summary || "—"}</div>
                    </div>
                  );
                })
              )}
            </div>
          )}

          {publicTab === "files" && (
            <div className="public-grid">
              {publicFiles.length === 0 ? (
                <EmptyState
                  illustration="📁"
                  title="公共文件为空"
                  hint="admin 在 /admin/files 上传后这里可见"
                />
              ) : (
                publicFiles.map((f) => (
                  <button
                    key={f.id}
                    className="public-task-card"
                    onClick={() => openPublicFile(f)}
                  >
                    <div className="ptc-name">
                      {f.is_pinned && "📌 "}
                      {f.name}
                    </div>
                    <div className="ptc-meta">
                      {f.format} · {fmtSize(f.size_bytes)}
                    </div>
                  </button>
                ))
              )}
            </div>
          )}

          {publicTab === "templates" && (
            <div className="public-grid">
              {publicTemplates.length === 0 ? (
                <EmptyState
                  illustration="📑"
                  title="暂无公共模板"
                  hint="admin 审核通过的公共模板会出现在这里，可一键复用"
                />
              ) : (
                publicTemplates.map((tpl) => (
                  <button
                    key={tpl.id}
                    className="public-task-card"
                    onClick={() => navigate(`/create-task?template=${tpl.id}`)}
                  >
                    <div className="ptc-name">{tpl.name}</div>
                    <div className="ptc-meta">
                      {tpl.paradigm} · {tpl.has_schedule ? "⏱ 含定时" : "手动触发"}
                    </div>
                  </button>
                ))
              )}
            </div>
          )}
        </section>
      </main>

      <ConfirmModal
        open={!!confirmDelete}
        title="删除任务？"
        body={
          <>
            确定删除 <b>{confirmDelete?.name}</b>？
            <br />
            该任务的所有对话、文件、经验卡片都会一并删除，无法恢复。
          </>
        }
        confirmText={deleting ? "删除中…" : "删除"}
        danger
        onConfirm={deleteTask}
        onCancel={() => setConfirmDelete(null)}
      />

    </div>
  );
}

function fmtSize(n: number): string {
  if (n < 1024) return `${n} B`;
  if (n < 1024 * 1024) return `${(n / 1024).toFixed(1)} KB`;
  return `${(n / 1024 / 1024).toFixed(1)} MB`;
}

function paradigmClass(p: string): string {
  return `tc-${p}`;
}

/**
 * 从 Skill 的 markdown 描述里提取紧凑展示用的三件套：
 * - title：第一个 #/## 标题（如 `# 文章配图生成`）
 * - summary：第一个非标题段落，去掉粗体/代码/引号标记，限制长度
 * - full：整段纯文本（用于悬停 title 提示）
 */
function skillBrief(desc?: string | null): { title: string; summary: string; full: string } {
  const text = (desc || "").trim();
  if (!text) return { title: "", summary: "", full: "" };
  const lines = text.split("\n").map((l) => l.trim());
  let title = "";
  let summary = "";
  for (const l of lines) {
    if (!l) continue;
    if (!title && l.startsWith("#")) {
      title = l.replace(/^#+\s*/, "").trim();
      continue;
    }
    if (!summary) {
      const stripped = l
        .replace(/^[-*]\s+/, "")
        .replace(/\*\*([^*]+)\*\*/g, "$1")
        .replace(/`([^`]+)`/g, "$1")
        .trim();
      if (stripped) {
        summary = stripped.length > 90 ? stripped.slice(0, 90).trim() + "…" : stripped;
        break;
      }
    }
  }
  return { title, summary, full: text.slice(0, 400) };
}

function formatTime(iso?: string | null): string {
  if (!iso) return "-";
  const d = new Date(iso);
  const diff = Date.now() - d.getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return "刚刚";
  if (mins < 60) return `${mins} 分钟前`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `${hours} 小时前`;
  return d.toLocaleDateString();
}
