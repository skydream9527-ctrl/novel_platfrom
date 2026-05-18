import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import client from "../api/client";
import { TYPE_LABELS } from "../constants";
import "./AdminPage.css";

interface User {
  id: number;
  name: string;
  email: string;
  role: string;
  status: string;
  created_at: string;
}

interface Template {
  id: number;
  name: string;
  type: string;
  content: string;
  is_builtin: number;
}

interface Stats {
  user_count: number;
  task_count: number;
  chapter_count: number;
  conversation_count: number;
  message_count: number;
  template_count: number;
}

export default function AdminPage() {
  const [tab, setTab] = useState<"overview" | "users" | "templates" | "settings">("overview");
  const [stats, setStats] = useState<Stats>({ user_count: 0, task_count: 0, chapter_count: 0, conversation_count: 0, message_count: 0, template_count: 0 });
  const [users, setUsers] = useState<User[]>([]);
  const [templates, setTemplates] = useState<Template[]>([]);
  const [showTemplateModal, setShowTemplateModal] = useState(false);
  const [editingTemplate, setEditingTemplate] = useState<Template | null>(null);
  const [tplName, setTplName] = useState("");
  const [tplType, setTplType] = useState("novel");
  const [tplContent, setTplContent] = useState("");
  const navigate = useNavigate();

  useEffect(() => {
    client.get("/admin/stats").then((res) => setStats(res.data));
    client.get("/admin/users").then((res) => setUsers(res.data));
    client.get("/admin/templates").then((res) => setTemplates(res.data));
  }, []);

  const toggleUserStatus = async (u: User) => {
    await client.patch(`/admin/users/${u.id}`, { status: u.status === "active" ? "disabled" : "active" });
    const res = await client.get("/admin/users");
    setUsers(res.data);
  };

  const openNewTemplate = () => {
    setEditingTemplate(null);
    setTplName("");
    setTplType("novel");
    setTplContent("");
    setShowTemplateModal(true);
  };

  const openEditTemplate = (t: Template) => {
    setEditingTemplate(t);
    setTplName(t.name);
    setTplType(t.type);
    setTplContent(t.content);
    setShowTemplateModal(true);
  };

  const saveTemplate = async () => {
    if (!tplName.trim() || !tplContent.trim()) return;
    if (editingTemplate) {
      await client.patch(`/admin/templates/${editingTemplate.id}`, { name: tplName, type: tplType, content: tplContent });
    } else {
      await client.post("/admin/templates", { name: tplName, type: tplType, content: tplContent });
    }
    setShowTemplateModal(false);
    const res = await client.get("/admin/templates");
    setTemplates(res.data);
    const statsRes = await client.get("/admin/stats");
    setStats(statsRes.data);
  };

  const deleteTemplate = async (id: number) => {
    if (!confirm("确认删除此模板？")) return;
    await client.delete(`/admin/templates/${id}`);
    const res = await client.get("/admin/templates");
    setTemplates(res.data);
  };

  return (
    <div className="admin-page">
      <header className="admin-header">
        <button className="btn-back" onClick={() => navigate("/dashboard")}>← 返回</button>
        <h1>管理后台</h1>
      </header>

      <div className="admin-body">
        <nav className="admin-nav">
          <button className={tab === "overview" ? "active" : ""} onClick={() => setTab("overview")}>概览</button>
          <button className={tab === "users" ? "active" : ""} onClick={() => setTab("users")}>用户管理</button>
          <button className={tab === "templates" ? "active" : ""} onClick={() => setTab("templates")}>模板管理</button>
          <button className={tab === "settings" ? "active" : ""} onClick={() => setTab("settings")}>系统设置</button>
        </nav>

        <main className="admin-content">
          {tab === "overview" && (
            <div className="stats-grid">
              <div className="stat-card">
                <div className="stat-number">{stats.user_count}</div>
                <div className="stat-label">用户数</div>
              </div>
              <div className="stat-card">
                <div className="stat-number">{stats.task_count}</div>
                <div className="stat-label">任务数</div>
              </div>
              <div className="stat-card">
                <div className="stat-number">{stats.chapter_count}</div>
                <div className="stat-label">章节数</div>
              </div>
              <div className="stat-card">
                <div className="stat-number">{stats.conversation_count}</div>
                <div className="stat-label">对话数</div>
              </div>
              <div className="stat-card">
                <div className="stat-number">{stats.message_count}</div>
                <div className="stat-label">消息数</div>
              </div>
              <div className="stat-card">
                <div className="stat-number">{stats.template_count}</div>
                <div className="stat-label">模板数</div>
              </div>
            </div>
          )}

          {tab === "users" && (
            <table className="admin-table">
              <thead>
                <tr>
                  <th>ID</th>
                  <th>姓名</th>
                  <th>邮箱</th>
                  <th>角色</th>
                  <th>状态</th>
                  <th>注册时间</th>
                  <th>操作</th>
                </tr>
              </thead>
              <tbody>
                {users.map((u) => (
                  <tr key={u.id}>
                    <td>{u.id}</td>
                    <td>{u.name}</td>
                    <td>{u.email}</td>
                    <td>{u.role}</td>
                    <td>
                      <span className={`status-badge ${u.status}`}>{u.status === "active" ? "正常" : "禁用"}</span>
                    </td>
                    <td>{new Date(u.created_at).toLocaleDateString("zh-CN")}</td>
                    <td>
                      <button className="btn-sm" onClick={() => toggleUserStatus(u)}>
                        {u.status === "active" ? "禁用" : "启用"}
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}

          {tab === "templates" && (
            <div>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
                <h3 style={{ fontSize: 16, fontWeight: 600 }}>模板管理</h3>
                <button className="btn-primary" onClick={openNewTemplate}>+ 新建模板</button>
              </div>
              <table className="admin-table">
                <thead>
                  <tr>
                    <th>ID</th>
                    <th>名称</th>
                    <th>类型</th>
                    <th>内置</th>
                    <th>操作</th>
                  </tr>
                </thead>
                <tbody>
                  {templates.map((t) => (
                    <tr key={t.id}>
                      <td>{t.id}</td>
                      <td>{t.name}</td>
                      <td>{TYPE_LABELS[t.type] || t.type}</td>
                      <td>{t.is_builtin ? "是" : "否"}</td>
                      <td>
                        <button className="btn-sm" onClick={() => openEditTemplate(t)} style={{ marginRight: 8 }}>编辑</button>
                        {!t.is_builtin && (
                          <button className="btn-sm" onClick={() => deleteTemplate(t.id)}>删除</button>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {showTemplateModal && (
                <div className="modal-overlay" onClick={() => setShowTemplateModal(false)}>
                  <div className="modal-card" onClick={(e) => e.stopPropagation()} style={{ width: 560 }}>
                    <h3>{editingTemplate ? "编辑模板" : "新建模板"}</h3>
                    <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
                      <input placeholder="模板名称" value={tplName} onChange={(e) => setTplName(e.target.value)} />
                      <select value={tplType} onChange={(e) => setTplType(e.target.value)} style={{ padding: "10px 14px", borderRadius: "var(--radius)", border: "1px solid var(--color-border)", fontSize: 14 }}>
                        <option value="novel">小说</option>
                        <option value="script">剧本</option>
                        <option value="storyboard">分镜</option>
                      </select>
                      <textarea placeholder="模板内容..." value={tplContent} onChange={(e) => setTplContent(e.target.value)} rows={8} />
                    </div>
                    <div className="modal-actions">
                      <button className="btn-cancel" onClick={() => setShowTemplateModal(false)}>取消</button>
                      <button className="btn-save" onClick={saveTemplate}>{editingTemplate ? "保存" : "创建"}</button>
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}

          {tab === "settings" && (
            <div className="settings-info">
              <h3>系统设置</h3>
              <p className="settings-hint">请通过服务器 .env 文件配置以下项：</p>
              <ul>
                <li><strong>LLM_PROVIDER</strong> — AI 模型提供商</li>
                <li><strong>LLM_MODEL</strong> — 默认模型</li>
                <li><strong>LLM_BASE_URL</strong> — API 端点</li>
              </ul>
            </div>
          )}
        </main>
      </div>
    </div>
  );
}
