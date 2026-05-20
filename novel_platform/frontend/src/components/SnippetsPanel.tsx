import { useState, useEffect } from "react";
import client from "../api/client";

interface Snippet {
  id: number;
  title: string;
  content: string;
  category: string;
  tags: string;
  usage_count: number;
}

interface Props {
  onInsert: (content: string) => void;
}

const CATEGORIES = [
  { key: "all", label: "全部", icon: "📋" },
  { key: "scene", label: "场景", icon: "🎬" },
  { key: "dialogue", label: "对话", icon: "💬" },
  { key: "description", label: "描写", icon: "✍️" },
  { key: "general", label: "通用", icon: "📝" },
];

export default function SnippetsPanel({ onInsert }: Props) {
  const [snippets, setSnippets] = useState<Snippet[]>([]);
  const [selectedCategory, setSelectedCategory] = useState("all");
  const [showCreate, setShowCreate] = useState(false);
  const [newSnippet, setNewSnippet] = useState({ title: "", content: "", category: "general", tags: "" });
  const [searchQuery, setSearchQuery] = useState("");

  useEffect(() => {
    loadSnippets();
  }, []);

  const loadSnippets = async () => {
    try {
      const res = await client.get("/snippets/");
      setSnippets(res.data);
    } catch {
      setSnippets([]);
    }
  };

  const handleCreate = async () => {
    if (!newSnippet.title.trim() || !newSnippet.content.trim()) return;
    await client.post("/snippets/", newSnippet);
    setShowCreate(false);
    setNewSnippet({ title: "", content: "", category: "general", tags: "" });
    loadSnippets();
  };

  const handleUse = async (snippet: Snippet) => {
    await client.post(`/snippets/${snippet.id}/use`);
    onInsert(snippet.content);
    loadSnippets();
  };

  const handleDelete = async (id: number) => {
    await client.delete(`/snippets/${id}`);
    loadSnippets();
  };

  const filteredSnippets = snippets.filter((s) => {
    if (selectedCategory !== "all" && s.category !== selectedCategory) return false;
    if (searchQuery && !s.title.toLowerCase().includes(searchQuery.toLowerCase()) && !s.content.toLowerCase().includes(searchQuery.toLowerCase())) return false;
    return true;
  });

  return (
    <div style={{ display: "flex", flexDirection: "column", height: "100%" }}>
      <div style={{ padding: 12, borderBottom: "1px solid var(--color-border)" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 8 }}>
          <h3 style={{ margin: 0, fontSize: 14 }}>片段库</h3>
          <button className="btn-add" onClick={() => setShowCreate(true)} style={{ fontSize: 12, width: 24, height: 24, padding: 0 }}>+</button>
        </div>
        <input
          placeholder="搜索片段..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          style={{ width: "100%", padding: "6px 8px", fontSize: 12, borderRadius: 4, border: "1px solid var(--color-border)" }}
        />
        <div style={{ display: "flex", gap: 4, marginTop: 8, flexWrap: "wrap" }}>
          {CATEGORIES.map((cat) => (
            <button
              key={cat.key}
              onClick={() => setSelectedCategory(cat.key)}
              style={{
                fontSize: 11,
                padding: "2px 8px",
                borderRadius: 12,
                background: selectedCategory === cat.key ? "var(--color-primary)" : "var(--color-bg-secondary)",
                color: selectedCategory === cat.key ? "white" : "var(--color-text)",
                border: "none",
                cursor: "pointer",
              }}
            >
              {cat.icon} {cat.label}
            </button>
          ))}
        </div>
      </div>

      <div style={{ flex: 1, overflow: "auto", padding: 8 }}>
        {filteredSnippets.length === 0 ? (
          <div style={{ textAlign: "center", padding: 20, color: "var(--color-text-secondary)", fontSize: 13 }}>
            暂无片段
          </div>
        ) : (
          filteredSnippets.map((snippet) => (
            <div
              key={snippet.id}
              style={{
                padding: 10,
                marginBottom: 8,
                background: "var(--color-bg-secondary)",
                borderRadius: 6,
                cursor: "pointer",
              }}
              onClick={() => handleUse(snippet)}
            >
              <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 4 }}>
                <span style={{ fontSize: 13, fontWeight: 600 }}>{snippet.title}</span>
                <button
                  onClick={(e) => { e.stopPropagation(); handleDelete(snippet.id); }}
                  style={{ background: "none", border: "none", cursor: "pointer", fontSize: 12, color: "#94a3b8" }}
                >
                  ×
                </button>
              </div>
              <div style={{ fontSize: 12, color: "var(--color-text-secondary)", overflow: "hidden", textOverflow: "ellipsis", display: "-webkit-box", WebkitLineClamp: 2, WebkitBoxOrient: "vertical" }}>
                {snippet.content}
              </div>
              <div style={{ fontSize: 11, color: "var(--color-text-secondary)", marginTop: 4 }}>
                使用 {snippet.usage_count} 次
              </div>
            </div>
          ))
        )}
      </div>

      {showCreate && (
        <div className="modal-overlay" onClick={() => setShowCreate(false)}>
          <div className="modal-card" onClick={(e) => e.stopPropagation()} style={{ width: 400 }}>
            <h3>创建片段</h3>
            <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
              <input
                placeholder="片段标题"
                value={newSnippet.title}
                onChange={(e) => setNewSnippet((prev) => ({ ...prev, title: e.target.value }))}
              />
              <textarea
                placeholder="片段内容"
                value={newSnippet.content}
                onChange={(e) => setNewSnippet((prev) => ({ ...prev, content: e.target.value }))}
                rows={6}
              />
              <select
                value={newSnippet.category}
                onChange={(e) => setNewSnippet((prev) => ({ ...prev, category: e.target.value }))}
              >
                {CATEGORIES.filter((c) => c.key !== "all").map((cat) => (
                  <option key={cat.key} value={cat.key}>{cat.icon} {cat.label}</option>
                ))}
              </select>
              <input
                placeholder="标签（逗号分隔）"
                value={newSnippet.tags}
                onChange={(e) => setNewSnippet((prev) => ({ ...prev, tags: e.target.value }))}
              />
            </div>
            <div className="modal-actions">
              <button className="btn-cancel" onClick={() => setShowCreate(false)}>取消</button>
              <button className="btn-save" onClick={handleCreate}>创建</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
