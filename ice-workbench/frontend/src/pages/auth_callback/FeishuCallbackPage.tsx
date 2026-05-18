/**
 * Lands here after Feishu redirects: /auth/feishu/callback?code=...&state=...
 * We POST the code to our backend, which exchanges it for tokens, creates the
 * user if needed, and returns JWT pair. Then we drop into /dashboard.
 */
import { useEffect, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import http, { setTokens } from "@/api/client";
import type { ApiEnvelope, LoginResponse } from "@/types/api";
import { useAuthStore } from "@/stores/authStore";
import { ErrorState } from "@/components/feedback/ErrorState";

export function FeishuCallbackPage() {
  const [params] = useSearchParams();
  const navigate = useNavigate();
  const setUser = useAuthStore.setState;
  const [error, setError] = useState<{ code: string; message: string } | null>(null);

  useEffect(() => {
    const code = params.get("code");
    const stateBack = params.get("state");
    const stateExpected = sessionStorage.getItem("feishu-oauth-state");
    if (!code) {
      setError({ code: "MISSING_CODE", message: "回调缺少 code 参数，请重试登录" });
      return;
    }
    if (stateExpected && stateBack && stateBack !== stateExpected) {
      setError({ code: "STATE_MISMATCH", message: "OAuth state 校验失败，可能是请求被劫持" });
      return;
    }
    sessionStorage.removeItem("feishu-oauth-state");

    http
      .post<ApiEnvelope<LoginResponse>>("/auth/feishu/oauth/callback", { code, state: stateBack })
      .then((resp) => {
        const env = resp.data;
        if (env.code !== 0) {
          setError({ code: env.error_code || "ERROR", message: env.message });
          return;
        }
        const data = env.data;
        setTokens(data.tokens.access_token, data.tokens.refresh_token);
        setUser({ user: data.user });
        navigate("/dashboard", { replace: true });
      })
      .catch((err) => {
        const body = err?.response?.data;
        setError({
          code: body?.error_code || "OAUTH_FAILED",
          message: body?.message || err?.message || "登录回调失败",
        });
      });
  }, [params, navigate, setUser]);

  if (error) {
    return (
      <div style={{ minHeight: "100vh", display: "flex", alignItems: "center", justifyContent: "center", padding: 24 }}>
        <ErrorState
          icon="🚫"
          title="飞书登录失败"
          description={error.message}
          errorCode={error.code}
          actions={
            <button className="btn-primary" onClick={() => navigate("/login", { replace: true })}>
              返回登录
            </button>
          }
        />
      </div>
    );
  }

  return (
    <div style={{ minHeight: "100vh", display: "flex", alignItems: "center", justifyContent: "center", flexDirection: "column", gap: 18 }}>
      <div style={{ fontSize: 36 }}>🪶</div>
      <div style={{ fontFamily: "var(--font-head)", fontSize: 18 }}>正在用飞书登录…</div>
      <div style={{ fontSize: 12, color: "var(--text-muted)" }}>请勿关闭页面，几秒钟内自动跳转</div>
    </div>
  );
}
