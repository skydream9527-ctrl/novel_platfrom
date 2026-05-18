import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuthStore } from "../stores/authStore";
import client from "../api/client";
import "./SettingsPage.css";

export default function SettingsPage() {
  const { user, loadUser } = useAuthStore();
  const navigate = useNavigate();
  const [name, setName] = useState(user?.name || "");
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [msg, setMsg] = useState<{ type: "ok" | "err"; text: string } | null>(null);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (!user) loadUser();
    else setName(user.name);
  }, [user]);

  const handleSaveName = async () => {
    if (!name.trim()) return;
    setSaving(true);
    setMsg(null);
    try {
      await client.patch("/auth/profile", { name: name.trim() });
      setMsg({ type: "ok", text: "姓名已更新" });
      loadUser();
    } catch (err: any) {
      setMsg({ type: "err", text: err.response?.data?.detail || "更新失败" });
    } finally {
      setSaving(false);
    }
  };

  const handleChangePassword = async () => {
    if (!currentPassword || !newPassword) return;
    if (newPassword !== confirmPassword) {
      setMsg({ type: "err", text: "两次输入的新密码不一致" });
      return;
    }
    if (newPassword.length < 6) {
      setMsg({ type: "err", text: "新密码至少 6 位" });
      return;
    }
    setSaving(true);
    setMsg(null);
    try {
      await client.patch("/auth/profile", {
        current_password: currentPassword,
        new_password: newPassword,
      });
      setMsg({ type: "ok", text: "密码已修改" });
      setCurrentPassword("");
      setNewPassword("");
      setConfirmPassword("");
    } catch (err: any) {
      setMsg({ type: "err", text: err.response?.data?.detail || "修改失败" });
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="settings-page">
      <header className="settings-header">
        <button className="btn-back" onClick={() => navigate("/dashboard")}>← 返回</button>
        <h1>个人设置</h1>
      </header>

      <main className="settings-main">
        {msg && (
          <div className={`settings-msg ${msg.type}`}>{msg.text}</div>
        )}

        <section className="settings-section">
          <h2>基本信息</h2>
          <div className="settings-field">
            <label>姓名</label>
            <div className="field-row">
              <input
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="你的姓名"
              />
              <button className="btn-save" onClick={handleSaveName} disabled={saving}>
                保存
              </button>
            </div>
          </div>
          <div className="settings-field">
            <label>邮箱</label>
            <input value={user?.email || ""} disabled />
          </div>
          <div className="settings-field">
            <label>角色</label>
            <input value={user?.role === "admin" ? "管理员" : "普通用户"} disabled />
          </div>
        </section>

        <section className="settings-section">
          <h2>修改密码</h2>
          <div className="settings-field">
            <label>当前密码</label>
            <input
              type="password"
              value={currentPassword}
              onChange={(e) => setCurrentPassword(e.target.value)}
              placeholder="输入当前密码"
            />
          </div>
          <div className="settings-field">
            <label>新密码</label>
            <input
              type="password"
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              placeholder="至少 6 位"
            />
          </div>
          <div className="settings-field">
            <label>确认新密码</label>
            <input
              type="password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              placeholder="再次输入新密码"
            />
          </div>
          <button className="btn-primary" onClick={handleChangePassword} disabled={saving}>
            修改密码
          </button>
        </section>

        <section className="settings-section">
          <h2>快捷键</h2>
          <div className="shortcut-list">
            <div className="shortcut-item"><kbd>Ctrl</kbd> + <kbd>S</kbd><span>保存当前章节</span></div>
            <div className="shortcut-item"><kbd>Ctrl</kbd> + <kbd>N</kbd><span>新建章节</span></div>
            <div className="shortcut-item"><kbd>Ctrl</kbd> + <kbd>K</kbd><span>搜索章节</span></div>
            <div className="shortcut-item"><kbd>Ctrl</kbd> + <kbd>Shift</kbd> + <kbd>E</kbd><span>导出当前章节</span></div>
            <div className="shortcut-item"><kbd>Ctrl</kbd> + <kbd>Shift</kbd> + <kbd>A</kbd><span>导出全部章节</span></div>
            <div className="shortcut-item"><kbd>Esc</kbd><span>关闭弹窗</span></div>
          </div>
        </section>
      </main>
    </div>
  );
}
