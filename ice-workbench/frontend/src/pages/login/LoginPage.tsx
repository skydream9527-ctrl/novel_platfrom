import { useEffect, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { useAuthStore } from "@/stores/authStore";
import { authApi, sysApi } from "@/api/endpoints";
import type { GlobalToggles } from "@/types/api";
import { useUIStore } from "@/stores/uiStore";
import "./Login.css";

/**
 * 三种登录方式（后端 /auth/methods 控制可见性）：
 *  ① 米盾代理：浏览器 cookie 由代理注入，进入页面自动 bootstrapMe。
 *  ② 账号密码：POST /auth/login 换 JWT。
 *  ③ 测试样例账号：一键预填密码调同一接口。
 */

type Tab = "aegis" | "password" | "sample";

interface SampleAccount {
  email: string;
  password: string;
  name: string;
  role: string;
  hint: string;
}

const SAMPLE_ACCOUNTS: SampleAccount[] = [
  {
    email: "zhangmingyuan",
    password: "test123",
    name: "张明远",
    role: "产品经理",
    hint: "Growth 团队样例用户",
  },
  {
    email: "lisihan",
    password: "test123",
    name: "李思涵",
    role: "数据分析师",
    hint: "Biz 团队样例用户",
  },
];

export function LoginPage() {
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const justLoggedOut = searchParams.get("logout") === "1";

  const bootstrapMe = useAuthStore((s) => s.bootstrapMe);
  const login = useAuthStore((s) => s.login);
  const user = useAuthStore((s) => s.user);
  const pushToast = useUIStore((s) => s.pushToast);

  const [methods, setMethods] = useState<{
    aegis_enabled: boolean;
    password_enabled: boolean;
  } | null>(null);
  const [tab, setTab] = useState<Tab>("aegis");
  const [checking, setChecking] = useState(!justLoggedOut);
  const [submitting, setSubmitting] = useState(false);
  const [form, setForm] = useState({ email: "", password: "" });
  const [toggles, setToggles] = useState<GlobalToggles | null>(null);

  // 读取后端启用了哪些登录方式
  useEffect(() => {
    authApi
      .methods()
      .then((m) => {
        setMethods({ aegis_enabled: m.aegis_enabled, password_enabled: m.password_enabled });
        // 若米盾已启用且不是刚登出，保持 aegis tab；否则默认密码
        if (!m.aegis_enabled && m.password_enabled) setTab("password");
      })
      .catch(() => {
        setMethods({ aegis_enabled: false, password_enabled: true });
        setTab("password");
      });
    sysApi.toggles().then(setToggles).catch(() => {});
  }, []);

  // 米盾模式自动验证身份
  useEffect(() => {
    if (justLoggedOut) {
      setChecking(false);
      return;
    }
    let cancelled = false;
    bootstrapMe().finally(() => {
      if (!cancelled) setChecking(false);
    });
    return () => {
      cancelled = true;
    };
  }, [bootstrapMe, justLoggedOut]);

  // 登录成功 → 进 Dashboard
  useEffect(() => {
    if (user && !justLoggedOut) {
      navigate("/dashboard", { replace: true });
    }
  }, [user, navigate, justLoggedOut]);

  const clearLogoutFlag = () => {
    if (justLoggedOut) {
      searchParams.delete("logout");
      setSearchParams(searchParams, { replace: true });
    }
  };

  const retryAegis = () => {
    clearLogoutFlag();
    setChecking(true);
    bootstrapMe().finally(() => setChecking(false));
  };

  const submitPassword = async (email: string, password: string) => {
    if (!email.trim() || !password) {
      pushToast("warning", "请输入账号和密码");
      return;
    }
    clearLogoutFlag();
    setSubmitting(true);
    try {
      await login(email.trim(), password);
      pushToast("success", "登录成功");
      // user 变化后由 useEffect 跳转
    } catch (err) {
      pushToast("error", (err as Error).message);
    } finally {
      setSubmitting(false);
    }
  };

  const aegisTabVisible = methods?.aegis_enabled ?? false;
  const passwordTabVisible = methods?.password_enabled ?? true;

  return (
    <div className="login-page">
      <div className="login-bg-grid" />
      <div className="login-orb login-orb-1" />
      <div className="login-orb login-orb-2" />

      <div className="login-card">
        <aside className="login-left">
          <div className="brand">
            <div className="brand-logo">
              <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="#fff" strokeWidth="2.2">
                <path d="M12 2L2 7l10 5 10-5-10-5z" />
                <path d="M2 17l10 5 10-5" />
                <path d="M2 12l10 5 10-5" />
              </svg>
            </div>
            <div>
              <div className="brand-name">
                <span className="brand-accent">ICE</span> Data Workbench
              </div>
              <div className="brand-tag">AI 数据工作流工作台</div>
            </div>
          </div>
          <div className="loop-anim">
            <div className="loop-step">
              <div className="dot user" />
              <div className="loop-text">用户：上周新版本留存…</div>
            </div>
            <div className="loop-arrow">↓</div>
            <div className="loop-step">
              <div className="dot tool" />
              <div className="loop-text">⚡ Tool: SQL → Skill → 图表</div>
            </div>
            <div className="loop-arrow">↓</div>
            <div className="loop-step">
              <div className="dot agent" />
              <div className="loop-text">📊 Agent：D7 留存 +5.6pp</div>
            </div>
          </div>
        </aside>

        <main className="login-right">
          <h1>登录</h1>
          <p className="login-sub">三种登录方式任选其一</p>

          <div className="login-tabs">
            {aegisTabVisible && (
              <button
                type="button"
                className={`login-tab ${tab === "aegis" ? "active" : ""}`}
                onClick={() => setTab("aegis")}
              >
                🛡 米盾
              </button>
            )}
            {passwordTabVisible && (
              <button
                type="button"
                className={`login-tab ${tab === "password" ? "active" : ""}`}
                onClick={() => setTab("password")}
              >
                🔑 账号密码
              </button>
            )}
            <button
              type="button"
              className={`login-tab ${tab === "sample" ? "active" : ""}`}
              onClick={() => setTab("sample")}
            >
              🧪 测试账号
            </button>
          </div>

          {tab === "aegis" && aegisTabVisible && (
            <div className="login-pane">
              {justLoggedOut ? (
                <div className="login-hint info">
                  <div className="lh-title">👋 已退出登录</div>
                  <div className="lh-body">
                    你已安全登出。若需继续使用米盾账号，点击下方重新验证。
                  </div>
                  <button
                    className="btn-primary login-submit"
                    type="button"
                    onClick={retryAegis}
                  >
                    🔁 重新登录
                  </button>
                </div>
              ) : checking ? (
                <div className="login-hint">
                  <div className="lh-body">正在通过米盾代理验证身份…</div>
                </div>
              ) : (
                <div className="login-hint warn">
                  <div className="lh-title">🔐 未检测到米盾登录态</div>
                  <div className="lh-body">
                    请通过米盾代理域名访问；本地开发可在 backend <code>.env</code> 设置{" "}
                    <code>AEGIS_DEV_BYPASS_EMAIL=admin</code> 后重启。
                  </div>
                  <button
                    className="btn-primary login-submit"
                    type="button"
                    onClick={retryAegis}
                  >
                    🔁 重新尝试
                  </button>
                </div>
              )}
            </div>
          )}

          {tab === "password" && passwordTabVisible && (
            <form
              className="login-pane login-form"
              onSubmit={(e) => {
                e.preventDefault();
                submitPassword(form.email, form.password);
              }}
            >
              <label className="login-field">
                <span>账号（邮箱或用户名）</span>
                <input
                  type="text"
                  autoComplete="username"
                  value={form.email}
                  onChange={(e) => setForm({ ...form, email: e.target.value })}
                  placeholder="例如 admin 或 zhangmingyuan"
                />
              </label>
              <label className="login-field">
                <span>密码</span>
                <input
                  type="password"
                  autoComplete="current-password"
                  value={form.password}
                  onChange={(e) => setForm({ ...form, password: e.target.value })}
                  placeholder="输入密码"
                />
              </label>
              <button
                className="btn-primary login-submit"
                type="submit"
                disabled={submitting}
              >
                {submitting ? "登录中…" : "登录"}
              </button>
            </form>
          )}

          {tab === "sample" && (
            <div className="login-pane">
              <div className="login-hint">
                <div className="lh-body">
                  开发 / 演示环境预置账号，点击任意卡片一键登录。
                </div>
              </div>
              <div className="sample-grid">
                {SAMPLE_ACCOUNTS.map((s) => (
                  <button
                    key={s.email}
                    className="sample-card"
                    type="button"
                    disabled={submitting}
                    onClick={() => submitPassword(s.email, s.password)}
                  >
                    <div className="sc-top">
                      <span className="sc-avatar">{s.name[0]}</span>
                      <div className="sc-meta">
                        <div className="sc-name">{s.name}</div>
                        <div className="sc-role">{s.role}</div>
                      </div>
                    </div>
                    <div className="sc-hint">{s.hint}</div>
                    <div className="sc-creds">
                      账号 <code>{s.email}</code> · 密码 <code>{s.password}</code>
                    </div>
                  </button>
                ))}
              </div>
            </div>
          )}

          {toggles && !toggles.feishu_enabled && tab === "aegis" && (
            <div className="login-foot">
              提示：如需启用飞书 OAuth，请在后端 <code>.env</code> 配置{" "}
              <code>FEISHU_APP_ID / FEISHU_APP_SECRET</code>。
            </div>
          )}
        </main>
      </div>
    </div>
  );
}
