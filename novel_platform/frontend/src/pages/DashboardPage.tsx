import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import client from "../api/client";
import { TYPE_LABELS, TYPE_ICONS } from "../constants";
import "./DashboardPage.css";

interface Task {
  id: number;
  title: string;
  description: string;
  type: string;
  status: string;
  chapter_count: number;
  directory_path: string | null;
  created_at: string;
  updated_at: string;
}

interface Template {
  id: number;
  name: string;
  type: string;
  content: string;
  is_builtin?: number;
  is_public?: boolean;
  author_name?: string;
  created_at?: string;
}

interface FolderItem {
  name: string;
  path: string;
}

export default function DashboardPage() {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [showCreate, setShowCreate] = useState(false);
  const [newTitle, setNewTitle] = useState("");
  const [newType, setNewType] = useState("novel");
  const [newDesc, setNewDesc] = useState("");
  const [newDirPath, setNewDirPath] = useState("");
  const [dirStatus, setDirStatus] = useState<"idle" | "checking" | "valid" | "invalid">("idle");
  const [dirError, setDirError] = useState("");
  const [templates, setTemplates] = useState<Template[]>([]);
  const [selectedTemplate, setSelectedTemplate] = useState<number | null>(null);
  const [showTemplateMarket, setShowTemplateMarket] = useState(false);
  const [publicTemplates, setPublicTemplates] = useState<Template[]>([]);
  const [showCreateTemplate, setShowCreateTemplate] = useState(false);
  const [newTemplateName, setNewTemplateName] = useState("");
  const [newTemplateType, setNewTemplateType] = useState("novel");
  const [newTemplateContent, setNewTemplateContent] = useState("");
  const navigate = useNavigate();

  // Folder browser state
  const [showBrowser, setShowBrowser] = useState(false);
  const [browserPath, setBrowserPath] = useState("");
  const [browserParent, setBrowserParent] = useState<string | null>(null);
  const [browserFolders, setBrowserFolders] = useState<FolderItem[]>([]);
  const [browserLoading, setBrowserLoading] = useState(false);
  const [newFolderName, setNewFolderName] = useState("");

  const loadTasks = async () => {
    const res = await client.get("/tasks/");
    setTasks(res.data);
  };

  useEffect(() => {
    loadTasks();
    client.get("/templates/").then((res) => setTemplates(res.data));
  }, []);

  const loadPublicTemplates = async () => {
    try {
      const res = await client.get("/templates/public");
      setPublicTemplates(res.data);
    } catch {
      setPublicTemplates([]);
    }
  };

  const createTemplate = async () => {
    if (!newTemplateName.trim() || !newTemplateContent.trim()) return;
    await client.post("/templates/", {
      name: newTemplateName,
      type: newTemplateType,
      content: newTemplateContent,
      is_public: true,
    });
    setShowCreateTemplate(false);
    setNewTemplateName("");
    setNewTemplateContent("");
    loadPublicTemplates();
  };

  const forkTemplate = async (templateId: number) => {
    await client.post(`/templates/${templateId}/fork`);
    client.get("/templates/").then((res) => setTemplates(res.data));
    alert("模板已复制到你的模板库");
  };

  const verifyDirectory = async (path: string) => {
    if (!path.trim()) { setDirStatus("idle"); setDirError(""); return; }
    setDirStatus("checking");
    try {
      const res = await client.post("/tasks/verify-directory", { path: path.trim() });
      if (res.data.valid) {
        setDirStatus("valid");
        setDirError("");
      } else {
        setDirStatus("invalid");
        setDirError(res.data.error);
      }
    } catch {
      setDirStatus("invalid");
      setDirError("验证失败");
    }
  };

  const browseDirectory = async (path: string) => {
    setBrowserLoading(true);
    try {
      const res = await client.post("/tasks/browse-directory", { path });
      console.log("browse-directory 返回:", res.data);
      if (res.data.error) {
        console.error("browse-directory 错误:", res.data.error);
        alert(`浏览目录失败: ${res.data.error}`);
      }
      setBrowserPath(res.data.current || "");
      setBrowserParent(res.data.parent);
      setBrowserFolders(res.data.folders || []);
    } catch (err: any) {
      console.error("browse-directory 请求失败:", err);
      const errorMsg = err.response?.data?.detail || err.message || "浏览目录失败";
      alert(`浏览目录失败: ${errorMsg}`);
      setBrowserFolders([]);
    } finally {
      setBrowserLoading(false);
    }
  };

  const openBrowser = () => {
    // 直接打开 Web 文件夹浏览器，不依赖系统对话框
    setShowBrowser(true);
    setNewFolderName("");
    browseDirectory("");
  };

  const selectFolder = (folderPath: string) => {
    console.log("selectFolder 被调用, folderPath:", folderPath);
    setNewDirPath(folderPath);
    setShowBrowser(false);
    verifyDirectory(folderPath);
  };

  const navigateTo = (path: string) => {
    setNewFolderName("");
    browseDirectory(path);
  };

  const createNewFolder = async () => {
    if (!newFolderName.trim()) return;
    // 使用 Path.join 的逻辑，确保跨平台兼容
    const separator = browserPath.includes("\\") ? "\\" : "/";
    const newPath = browserPath.endsWith(separator)
      ? browserPath + newFolderName.trim()
      : browserPath + separator + newFolderName.trim();
    console.log("创建文件夹:", { browserPath, newFolderName: newFolderName.trim(), newPath });
    setBrowserLoading(true);
    try {
      const res = await client.post("/tasks/create-directory", { path: newPath });
      console.log("创建文件夹响应:", res.data);
      if (res.data.ok) {
        selectFolder(res.data.path);
      } else {
        alert(res.data.error || "创建文件夹失败");
      }
    } catch (err: any) {
      console.error("创建文件夹请求失败:", err);
      const errorMsg = err.response?.data?.detail || err.message || "创建文件夹失败";
      alert(`创建文件夹失败: ${errorMsg}`);
    } finally {
      setBrowserLoading(false);
    }
  };

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newDirPath.trim()) { alert("请选择或输入本地空文件夹路径"); return; }
    if (dirStatus === "invalid") { alert(dirError || "文件夹不可用"); return; }
    if (dirStatus !== "valid") {
      await verifyDirectory(newDirPath);
      // Re-check after verification
      const res2 = await client.post("/tasks/verify-directory", { path: newDirPath.trim() });
      if (!res2.data.valid) {
        alert(res2.data.error || "文件夹不可用");
        return;
      }
    }
    const payload: any = { title: newTitle, type: newType, description: newDesc, directory_path: newDirPath.trim() };
    if (selectedTemplate) payload.template_id = selectedTemplate;
    const res = await client.post("/tasks/", payload);
    setShowCreate(false);
    setNewTitle("");
    setNewDesc("");
    setNewDirPath("");
    setSelectedTemplate(null);
    navigate(`/workspace/${res.data.id}`);
  };

  const handleDelete = async (id: number) => {
    if (!confirm("确认删除此任务？")) return;
    await client.delete(`/tasks/${id}`);
    loadTasks();
  };

  return (
    <div className="dashboard">
      <header className="dashboard-header">
        <h1>AI 文字创作平台</h1>
        <div className="header-right">
          <button className="btn-text" onClick={() => navigate("/settings")}>设置</button>
          <button className="btn-text" onClick={() => navigate("/admin")}>管理后台</button>
        </div>
      </header>

      <main className="dashboard-main">
        <div className="section-header">
          <h2>我的任务</h2>
          <div style={{ display: "flex", gap: 8 }}>
            <button className="btn-text" onClick={() => { setShowTemplateMarket(true); loadPublicTemplates(); }}>模板市场</button>
            <button className="btn-primary" onClick={() => setShowCreate(true)}>+ 新建任务</button>
          </div>
        </div>

        {showCreate && (
          <div className="create-card">
            <form onSubmit={handleCreate}>
              <input
                placeholder="任务标题"
                value={newTitle}
                onChange={(e) => setNewTitle(e.target.value)}
                required
                autoFocus
              />
              <div className="type-selector">
                {Object.entries(TYPE_LABELS).map(([key, label]) => (
                  <button
                    key={key}
                    type="button"
                    className={newType === key ? "active" : ""}
                    onClick={() => setNewType(key)}
                  >
                    {TYPE_ICONS[key]} {label}
                  </button>
                ))}
              </div>
              <textarea
                placeholder="任务描述（可选）"
                value={newDesc}
                onChange={(e) => setNewDesc(e.target.value)}
                rows={3}
              />
              <div className="dir-picker">
                <input
                  placeholder="本地空文件夹路径（必填）"
                  value={newDirPath}
                  onChange={(e) => { setNewDirPath(e.target.value); setDirStatus("idle"); }}
                  onBlur={() => verifyDirectory(newDirPath)}
                  className={dirStatus === "valid" ? "dir-valid" : dirStatus === "invalid" ? "dir-invalid" : ""}
                  required
                />
                <button type="button" className="btn-browse" onClick={openBrowser}>选择文件夹</button>
              </div>
              {dirStatus === "checking" && <div className="dir-hint">验证中...</div>}
              {dirStatus === "valid" && <div className="dir-hint dir-hint-ok">文件夹可用</div>}
              {dirStatus === "invalid" && <div className="dir-hint dir-hint-err">{dirError}</div>}
              {templates.length > 0 && (
                <div className="template-selector">
                  <label style={{ fontSize: 13, color: "var(--color-text-secondary)", marginBottom: 4 }}>选择模板（可选）</label>
                  <div className="template-options">
                    <button type="button" className={selectedTemplate === null ? "active" : ""} onClick={() => setSelectedTemplate(null)}>不使用模板</button>
                    {templates.filter(t => t.type === newType).map((t) => (
                      <button type="button" key={t.id} className={selectedTemplate === t.id ? "active" : ""} onClick={() => setSelectedTemplate(t.id)}>{t.name}</button>
                    ))}
                  </div>
                </div>
              )}
              <div className="create-actions">
                <button type="button" className="btn-text" onClick={() => setShowCreate(false)}>取消</button>
                <button type="submit" className="btn-primary">创建并进入</button>
              </div>
            </form>
          </div>
        )}

        <div className="task-grid">
          {tasks.map((task) => (
            <div key={task.id} className="task-card" onClick={() => navigate(`/workspace/${task.id}`)}>
              <div className="task-type-badge">{TYPE_ICONS[task.type]} {TYPE_LABELS[task.type]}</div>
              <h3>{task.title}</h3>
              {task.description && <p className="task-desc">{task.description}</p>}
              <div className="task-meta">
                <span>{task.chapter_count} 章</span>
                <span>{new Date(task.updated_at).toLocaleDateString("zh-CN")}</span>
              </div>
              {task.directory_path && (
                <div className="task-dir" title={task.directory_path}>
                  📁 {task.directory_path}
                </div>
              )}
              <button
                className="task-delete"
                onClick={(e) => { e.stopPropagation(); handleDelete(task.id); }}
                title="删除"
              >
                ×
              </button>
            </div>
          ))}
          {tasks.length === 0 && !showCreate && (
            <div className="empty-state">
              <p>还没有任务，点击「新建任务」开始创作</p>
            </div>
          )}
        </div>
      </main>

      {/* Folder Browser Modal */}
      {showBrowser && (
        <div className="modal-overlay" onClick={() => setShowBrowser(false)}>
          <div className="modal-card folder-browser" onClick={(e) => e.stopPropagation()}>
            <h3>选择文件夹</h3>
            <div className="browser-path">
              <span className="browser-current">{browserPath}</span>
            </div>
            <div className="browser-actions">
              {browserParent && (
                <button className="btn-up" onClick={() => navigateTo(browserParent)}>
                  ⬆️ 上级目录
                </button>
              )}
              <button className="btn-select-current" onClick={() => {
                console.log("选择当前目录按钮被点击, browserPath:", browserPath);
                selectFolder(browserPath);
              }}>
                选择当前目录
              </button>
              <div className="new-folder-row">
                <input
                  placeholder="新建文件夹名称"
                  value={newFolderName}
                  onChange={(e) => setNewFolderName(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && (e.preventDefault(), createNewFolder())}
                />
                <button className="btn-create-folder" onClick={createNewFolder} disabled={!newFolderName.trim()}>
                  新建
                </button>
              </div>
            </div>
            <div className="browser-list">
              {browserLoading ? (
                <div className="browser-loading">加载中...</div>
              ) : browserFolders.length === 0 ? (
                <div className="browser-empty">
                  <p>此目录下没有子文件夹</p>
                  <p className="browser-hint">可以输入新文件夹名称并点击「新建」</p>
                </div>
              ) : (
                browserFolders.map((folder) => (
                  <div
                    key={folder.path}
                    className="browser-item"
                    onClick={() => navigateTo(folder.path)}
                    onDoubleClick={() => selectFolder(folder.path)}
                  >
                    <span className="browser-icon">📁</span>
                    <span className="browser-name">{folder.name}</span>
                    <button
                      className="btn-select-folder"
                      onClick={(e) => { e.stopPropagation(); selectFolder(folder.path); }}
                    >
                      选择
                    </button>
                  </div>
                ))
              )}
            </div>
            <div className="modal-actions">
              <button className="btn-cancel" onClick={() => setShowBrowser(false)}>取消</button>
            </div>
          </div>
        </div>
      )}

      {/* Template Market Modal */}
      {showTemplateMarket && (
        <div className="modal-overlay" onClick={() => setShowTemplateMarket(false)}>
          <div className="modal-card" onClick={(e) => e.stopPropagation()} style={{ width: 700, maxHeight: "80vh", overflow: "auto" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
              <h3 style={{ margin: 0 }}>模板市场</h3>
              <button className="btn-primary" onClick={() => setShowCreateTemplate(true)} style={{ fontSize: 13, padding: "6px 12px" }}>
                + 分享模板
              </button>
            </div>
            <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
              {publicTemplates.length === 0 ? (
                <p style={{ color: "var(--color-text-secondary)", textAlign: "center", padding: 40 }}>暂无公共模板</p>
              ) : (
                publicTemplates.map((t) => (
                  <div key={t.id} style={{
                    padding: 16,
                    background: "var(--color-bg-secondary)",
                    borderRadius: 8,
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                  }}>
                    <div style={{ flex: 1 }}>
                      <div style={{ fontWeight: 600, marginBottom: 4 }}>{t.name}</div>
                      <div style={{ fontSize: 13, color: "var(--color-text-secondary)" }}>
                        {TYPE_LABELS[t.type] || t.type} · 作者: {t.author_name || "系统"}
                      </div>
                      <div style={{ fontSize: 12, color: "var(--color-text-secondary)", marginTop: 4, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap", maxWidth: 400 }}>
                        {t.content.slice(0, 100)}...
                      </div>
                    </div>
                    <button className="btn-save" onClick={() => forkTemplate(t.id)} style={{ fontSize: 13, padding: "6px 12px" }}>
                      使用模板
                    </button>
                  </div>
                ))
              )}
            </div>
            <div className="modal-actions" style={{ marginTop: 16 }}>
              <button className="btn-cancel" onClick={() => setShowTemplateMarket(false)}>关闭</button>
            </div>
          </div>
        </div>
      )}

      {/* Create Template Modal */}
      {showCreateTemplate && (
        <div className="modal-overlay" onClick={() => setShowCreateTemplate(false)}>
          <div className="modal-card" onClick={(e) => e.stopPropagation()} style={{ width: 600 }}>
            <h3>分享模板</h3>
            <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
              <input placeholder="模板名称" value={newTemplateName} onChange={(e) => setNewTemplateName(e.target.value)} />
              <div className="type-selector">
                {Object.entries(TYPE_LABELS).map(([key, label]) => (
                  <button
                    key={key}
                    type="button"
                    className={newTemplateType === key ? "active" : ""}
                    onClick={() => setNewTemplateType(key)}
                  >
                    {TYPE_ICONS[key]} {label}
                  </button>
                ))}
              </div>
              <textarea placeholder="模板内容（Markdown 格式）" value={newTemplateContent} onChange={(e) => setNewTemplateContent(e.target.value)} rows={10} />
            </div>
            <div className="modal-actions">
              <button className="btn-cancel" onClick={() => setShowCreateTemplate(false)}>取消</button>
              <button className="btn-save" onClick={createTemplate}>分享</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
