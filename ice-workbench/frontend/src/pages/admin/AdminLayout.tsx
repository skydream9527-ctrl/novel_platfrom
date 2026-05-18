import { useState } from "react";
import { NavLink, Outlet, useLocation, useNavigate } from "react-router-dom";
import { useEffect } from "react";
import { TopNav } from "@/components/shell/TopNav";
import { useAuthStore } from "@/stores/authStore";
import "./Admin.css";

interface NavItem {
  to: string;
  label: string;
  icon: string;
  group: "monitor" | "review" | "resource" | "users";
  super?: boolean;
}

const NAV: NavItem[] = [
  { to: "/admin", label: "概览", icon: "📊", group: "monitor" },
  { to: "/admin/usage", label: "用量与成本", icon: "💰", group: "monitor" },
  { to: "/admin/sql-audit", label: "SQL 审计", icon: "🔍", group: "monitor" },
  { to: "/admin/audit", label: "操作审计", icon: "📜", group: "monitor" },
  { to: "/admin/review-center", label: "审核中心", icon: "📥", group: "review" },
  { to: "/admin/experience-cards", label: "经验卡片", icon: "💡", group: "review" },
  { to: "/admin/public-tasks", label: "公共任务", icon: "🌐", group: "review" },
  { to: "/admin/agents", label: "Agents", icon: "🤖", group: "resource" },
  { to: "/admin/skills", label: "Skills", icon: "⚡", group: "resource" },
  { to: "/admin/knowledge-bases", label: "知识库", icon: "📚", group: "resource" },
  { to: "/admin/files", label: "公共文件", icon: "📁", group: "resource" },
  { to: "/admin/templates", label: "任务模板", icon: "📋", group: "resource" },
  { to: "/admin/users", label: "用户管理", icon: "👥", group: "users" },
  { to: "/admin/settings", label: "系统设置", icon: "⚙", group: "users", super: true },
];

const GROUP_LABEL: Record<NavItem["group"], string> = {
  monitor: "监控",
  review: "内容审核",
  resource: "资源管理",
  users: "用户与配置",
};

export function AdminLayout() {
  const user = useAuthStore((s) => s.user);
  const navigate = useNavigate();
  const groupOrder: NavItem["group"][] = ["monitor", "review", "resource", "users"];
  const [mobileOpen, setMobileOpen] = useState(false);
  const location = useLocation();
  useEffect(() => {
    setMobileOpen(false);
  }, [location.pathname]);
  return (
    <div className="adm-shell">
      <TopNav
        mode="admin"
        crumb={
          <span>
            <button className="adm-mobile-menu" onClick={() => setMobileOpen((v) => !v)}>
              ☰ 菜单
            </button>
            首页 / <span className="current">管理后台</span>
          </span>
        }
        rightActions={
          <button
            className="btn-ghost"
            onClick={() => navigate("/dashboard")}
            title="返回用户首页"
          >
            🏠 返回首页
          </button>
        }
      />
      <div className="adm-body">
        <aside className={`adm-sb ${mobileOpen ? "mobile-open" : ""}`}>
          {groupOrder.map((g) => {
            const items = NAV.filter((n) => n.group === g);
            if (items.length === 0) return null;
            return (
              <div key={g}>
                <div className="adm-sb-group">{GROUP_LABEL[g]}</div>
                {items.map((n) => (
                  <NavLink
                    key={n.to}
                    to={n.to}
                    end={n.to === "/admin"}
                    className={({ isActive }) => `adm-sb-item ${isActive ? "active" : ""}`}
                  >
                    <span className="ico">{n.icon}</span>
                    {n.label}
                    {n.super && user?.auth_role !== "super_admin" && <span className="lock">🔒</span>}
                  </NavLink>
                ))}
              </div>
            );
          })}
        </aside>
        <main className="adm-main">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
