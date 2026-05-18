import { useEffect, useRef, useState } from "react";
import { adminFileApi } from "@/api/endpoints";
import type { PublicFileMeta } from "@/api/endpoints";
import { ConfirmModal } from "@/components/feedback/ConfirmModal";
import { Skeleton } from "@/components/feedback/Skeleton";
import { useUIStore } from "@/stores/uiStore";

const TEXT_FORMATS = ["md", "txt", "csv", "sql", "py", "json", "tsv", "log", "yml", "yaml"];

export function AdminFiles() {
  const pushToast = useUIStore((s) => s.pushToast);
  const fileInput = useRef<HTMLInputElement>(null);
  const [items, setItems] = useState<PublicFileMeta[]>([]);
  const [loading, setLoading] = useState(true);
  const [editing, setEditing] = useState<PublicFileMeta | null>(null);
  const [confirmDelete, setConfirmDelete] = useState<PublicFileMeta | null>(null);

  const reload = async () => {
    setLoading(true);
    try {
      const r = await adminFileApi.list();
      setItems(r.items);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void reload();
  }, []);

  const upload = async (f: File) => {
    try {
      await adminFileApi.upload(f);
      pushToast("success", `${f.name} 已上传`);
      await reload();
    } catch (err) {
      pushToast("error", (err as Error).message);
    }
  };

  const togglePin = async (f: PublicFileMeta) => {
    try {
      await adminFileApi.update(f.id, { is_pinned: !f.is_pinned });
      pushToast("success", f.is_pinned ? "已取消置顶" : "已置顶");
      await reload();
    } catch (err) {
      pushToast("error", (err as Error).message);
    }
  };

  const remove = async (f: PublicFileMeta) => {
    try {
      await adminFileApi.remove(f.id);
      pushToast("success", "已删除");
      await reload();
    } catch (err) {
      pushToast("error", (err as Error).message);
    } finally {
      setConfirmDelete(null);
    }
  };

  return (
    <div>
      <div className="adm-page-head" style={{ display: "flex", justifyContent: "space-between" }}>
        <div>
          <h1>📁 公共文件</h1>
          <p>团队共享的文件，所有用户可在 Workspace 中引用</p>
        </div>
        <div>
          <input
            ref={fileInput}
            type="file"
            style={{ display: "none" }}
            onChange={(e) => {
              const f = e.target.files?.[0];
              if (f) upload(f);
              e.target.value = "";
            }}
          />
          <button className="btn-primary" onClick={() => fileInput.current?.click()}>
            + 上传文件
          </button>
        </div>
      </div>

      {loading ? (
        <Skeleton lines={6} />
      ) : items.length === 0 ? (
        <div className="adm-section" style={{ textAlign: "center", color: "var(--text-muted)" }}>
          暂无公共文件
        </div>
      ) : (
        <table className="adm-table">
          <thead>
            <tr>
              <th>名称</th>
              <th>类型</th>
              <th style={{ textAlign: "right" }}>大小</th>
              <th>置顶</th>
              <th>更新时间</th>
              <th style={{ width: 240 }}>操作</th>
            </tr>
          </thead>
          <tbody>
            {items.map((f) => (
              <tr key={f.id}>
                <td>
                  {f.is_pinned && <span title="置顶">📌</span>} {f.name}
                </td>
                <td>
                  <span className="role-badge role-user">{f.format || "?"}</span>
                </td>
                <td style={{ textAlign: "right", fontFamily: "var(--font-mono)" }}>
                  {fmtSize(f.size_bytes)}
                </td>
                <td>{f.is_pinned ? "✅" : "—"}</td>
                <td style={{ fontSize: 11, color: "var(--text-muted)" }}>
                  {f.updated_at
                    ? new Date(f.updated_at).toLocaleString()
                    : f.created_at
                      ? new Date(f.created_at).toLocaleString()
                      : "-"}
                </td>
                <td className="row-actions">
                  {TEXT_FORMATS.includes(f.format || "") && (
                    <button onClick={() => setEditing(f)}>✏ 编辑</button>
                  )}
                  <button onClick={() => togglePin(f)}>{f.is_pinned ? "取消置顶" : "📌 置顶"}</button>
                  {!f.is_pinned && (
                    <button className="danger" onClick={() => setConfirmDelete(f)}>
                      🗑 删除
                    </button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      {editing && (
        <FileEditModal
          file={editing}
          onClose={() => setEditing(null)}
          onSaved={async () => {
            setEditing(null);
            await reload();
          }}
        />
      )}
      <ConfirmModal
        open={!!confirmDelete}
        title={`确认删除「${confirmDelete?.name}」？`}
        body="删除后不可恢复，且会影响已引用此文件的对话。"
        danger
        onConfirm={() => confirmDelete && remove(confirmDelete)}
        onCancel={() => setConfirmDelete(null)}
      />
    </div>
  );
}

function FileEditModal({
  file,
  onClose,
  onSaved,
}: {
  file: PublicFileMeta;
  onClose: () => void;
  onSaved: () => void | Promise<void>;
}) {
  const pushToast = useUIStore((s) => s.pushToast);
  const [content, setContent] = useState<string | null>(null);
  const [isPinned, setIsPinned] = useState(file.is_pinned);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    adminFileApi.read(file.id).then((r) => setContent(r.content || ""));
  }, [file.id]);

  const save = async () => {
    setSaving(true);
    try {
      await adminFileApi.update(file.id, { content: content || "", is_pinned: isPinned });
      pushToast("success", "已保存");
      await onSaved();
    } catch (err) {
      pushToast("error", (err as Error).message);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="cm-overlay" onClick={onClose}>
      <div className="cm-card" style={{ minWidth: 720, maxWidth: "85vw" }} onClick={(e) => e.stopPropagation()}>
        <h3>编辑「{file.name}」</h3>
        <div className="cm-body">
          <label className="ct-toggle" style={{ marginBottom: 10 }}>
            <input type="checkbox" checked={isPinned} onChange={(e) => setIsPinned(e.target.checked)} />
            置顶（防误删）
          </label>
          {content === null ? (
            <Skeleton lines={6} />
          ) : (
            <textarea
              rows={20}
              value={content}
              onChange={(e) => setContent(e.target.value)}
              style={{
                width: "100%",
                background: "var(--surface-2)",
                border: "1px solid var(--border)",
                borderRadius: 6,
                color: "var(--text)",
                fontFamily: "var(--font-mono)",
                fontSize: 13,
                padding: 12,
                outline: "none",
                resize: "vertical",
              }}
            />
          )}
        </div>
        <div className="cm-actions">
          <button className="btn-secondary" onClick={onClose}>
            取消
          </button>
          <button className="btn-primary" disabled={saving || content === null} onClick={save}>
            {saving ? "保存中…" : "💾 保存"}
          </button>
        </div>
      </div>
    </div>
  );
}

function fmtSize(n: number): string {
  if (n < 1024) return `${n} B`;
  if (n < 1024 * 1024) return `${(n / 1024).toFixed(1)} KB`;
  return `${(n / 1024 / 1024).toFixed(1)} MB`;
}
