import { useEffect, useState } from "react";
import { adminApi } from "@/api/endpoints";
import type { AdminUser } from "@/api/endpoints";
import { ConfirmModal } from "@/components/feedback/ConfirmModal";
import { Skeleton } from "@/components/feedback/Skeleton";
import { useAuthStore } from "@/stores/authStore";
import { useUIStore } from "@/stores/uiStore";

export function AdminUsers() {
  const me = useAuthStore((s) => s.user);
  const isSuper = me?.auth_role === "super_admin";
  const pushToast = useUIStore((s) => s.pushToast);

  const [items, setItems] = useState<AdminUser[]>([]);
  const [loading, setLoading] = useState(true);
  const [q, setQ] = useState("");
  const [role, setRole] = useState<string>("");
  const [showCreate, setShowCreate] = useState(false);
  const [editing, setEditing] = useState<AdminUser | null>(null);
  const [confirmDelete, setConfirmDelete] = useState<AdminUser | null>(null);

  const reload = async () => {
    setLoading(true);
    try {
      const r = await adminApi.listUsers(q || undefined, role || undefined);
      setItems(r.items);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void reload();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [role]);

  const handleDelete = async (u: AdminUser) => {
    try {
      await adminApi.deleteUser(u.id);
      pushToast("success", "已删除");
      setConfirmDelete(null);
      await reload();
    } catch (err) {
      pushToast("error", (err as Error).message);
    }
  };

  return (
    <div>
      <div className="adm-page-head" style={{ display: "flex", justifyContent: "space-between" }}>
        <div>
          <h1>👥 用户管理</h1>
          <p>三级角色：super_admin / admin / user</p>
        </div>
        <button className="btn-primary" onClick={() => setShowCreate(true)}>
          + 创建用户
        </button>
      </div>

      <div className="adm-toolbar">
        <input
          placeholder="🔍 搜索姓名 / 邮箱"
          value={q}
          onChange={(e) => setQ(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && reload()}
        />
        <select value={role} onChange={(e) => setRole(e.target.value)}>
          <option value="">全部角色</option>
          <option value="super_admin">super_admin</option>
          <option value="admin">admin</option>
          <option value="user">user</option>
        </select>
        <button className="btn-secondary" onClick={reload}>
          搜索
        </button>
      </div>

      {loading ? (
        <Skeleton lines={6} />
      ) : (
        <table className="adm-table">
          <thead>
            <tr>
              <th>姓名</th>
              <th>邮箱</th>
              <th>角色</th>
              <th>飞书</th>
              <th>状态</th>
              <th>团队</th>
              <th>注册时间</th>
              <th style={{ width: 220 }}>操作</th>
            </tr>
          </thead>
          <tbody>
            {items.map((u) => (
              <tr key={u.id}>
                <td>{u.name}</td>
                <td style={{ fontFamily: "var(--font-mono)", fontSize: 12 }}>{u.email}</td>
                <td>
                  <span className={`role-badge role-${u.auth_role}`}>{u.auth_role}</span>
                </td>
                <td>{u.feishu_bound ? "✅" : "—"}</td>
                <td>
                  <span className={`adm-status-${u.status}`}>{u.status === "active" ? "启用" : "禁用"}</span>
                </td>
                <td>{u.team || "-"}</td>
                <td style={{ fontSize: 11, color: "var(--text-muted)" }}>
                  {u.created_at ? new Date(u.created_at).toLocaleDateString() : "-"}
                </td>
                <td className="row-actions">
                  <button onClick={() => setEditing(u)}>✏ 编辑</button>
                  {isSuper && u.id !== me?.id && (
                    <button className="danger" onClick={() => setConfirmDelete(u)}>
                      🗑 删除
                    </button>
                  )}
                </td>
              </tr>
            ))}
            {items.length === 0 && (
              <tr>
                <td colSpan={8} style={{ textAlign: "center", padding: 32, color: "var(--text-muted)" }}>
                  没有匹配的用户
                </td>
              </tr>
            )}
          </tbody>
        </table>
      )}

      {(showCreate || editing) && (
        <UserModal
          existing={editing}
          isSuper={isSuper}
          selfId={me?.id}
          onClose={() => {
            setShowCreate(false);
            setEditing(null);
          }}
          onSaved={async () => {
            setShowCreate(false);
            setEditing(null);
            await reload();
          }}
        />
      )}
      <ConfirmModal
        open={!!confirmDelete}
        title={`确认删除用户 ${confirmDelete?.name}？`}
        body="该用户的所有任务、文件、对话历史都将被删除（仅清理 cache 索引；磁盘文件保留以便恢复）。"
        danger
        onConfirm={() => confirmDelete && handleDelete(confirmDelete)}
        onCancel={() => setConfirmDelete(null)}
      />
    </div>
  );
}

interface ModalProps {
  existing: AdminUser | null;
  isSuper: boolean;
  selfId?: string;
  onClose: () => void;
  onSaved: () => void | Promise<void>;
}

function UserModal({ existing, isSuper, selfId, onClose, onSaved }: ModalProps) {
  const pushToast = useUIStore((s) => s.pushToast);
  const [form, setForm] = useState({
    email: existing?.email || "",
    name: existing?.name || "",
    auth_role: existing?.auth_role || "user",
    team: existing?.team || "",
    title: existing?.title || "",
    status: existing?.status || "active",
    password: "",
  });
  const [saving, setSaving] = useState(false);
  const isSelf = existing?.id === selfId;

  const save = async () => {
    if (!form.email || !form.name) {
      return pushToast("warning", "请填写邮箱和姓名");
    }
    setSaving(true);
    try {
      if (existing) {
        const patch: any = {
          name: form.name,
          team: form.team,
          title: form.title,
          status: form.status,
        };
        if (isSuper && form.auth_role !== existing.auth_role) {
          patch.auth_role = form.auth_role;
        }
        if (form.password) patch.password = form.password;
        await adminApi.updateUser(existing.id, patch);
      } else {
        await adminApi.createUser(form);
      }
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
      <div className="cm-card" style={{ minWidth: 520 }} onClick={(e) => e.stopPropagation()}>
        <h3>{existing ? "编辑用户" : "创建用户"}</h3>
        <div className="cm-body">
          <div className="adm-form-grid">
            <label>
              邮箱 / 用户名
              <input
                value={form.email}
                onChange={(e) => setForm({ ...form, email: e.target.value })}
                disabled={!!existing}
              />
            </label>
            <label>
              姓名
              <input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
            </label>
            <label>
              角色
              {isSuper ? (
                <select
                  value={form.auth_role}
                  onChange={(e) => setForm({ ...form, auth_role: e.target.value as any })}
                  disabled={isSelf && form.auth_role === "super_admin"}
                >
                  <option value="user">user</option>
                  <option value="admin">admin</option>
                  <option value="super_admin">super_admin</option>
                </select>
              ) : (
                <input value={form.auth_role} disabled />
              )}
            </label>
            <label>
              状态
              <select
                value={form.status}
                onChange={(e) => setForm({ ...form, status: e.target.value as any })}
              >
                <option value="active">启用</option>
                <option value="disabled">禁用</option>
              </select>
            </label>
            <label>
              团队
              <input value={form.team} onChange={(e) => setForm({ ...form, team: e.target.value })} />
            </label>
            <label>
              职务
              <input value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} />
            </label>
            <label style={{ gridColumn: "span 2" }}>
              {existing ? "重置密码（留空不改）" : "初始密码（留空则仅飞书登录）"}
              <input
                type="password"
                value={form.password}
                onChange={(e) => setForm({ ...form, password: e.target.value })}
              />
            </label>
          </div>
        </div>
        <div className="cm-actions">
          <button className="btn-secondary" onClick={onClose}>
            取消
          </button>
          <button className="btn-primary" disabled={saving} onClick={save}>
            {saving ? "保存中…" : "保存"}
          </button>
        </div>
      </div>
    </div>
  );
}
