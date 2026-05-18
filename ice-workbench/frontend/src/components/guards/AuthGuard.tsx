import { useEffect, useState } from "react";
import { Navigate } from "react-router-dom";
import { useAuthStore } from "@/stores/authStore";

/**
 * 米盾 (Aegis) 模式下 cookie 由代理注入、后端直接从 header 识别用户；
 * 本地 dev 则有 AEGIS_DEV_BYPASS_EMAIL 兜底。因此不再用 access_token 判断登录态，
 * 直接调 /users/me：200 即已登录，401 才跳 /login。
 */
export function AuthGuard({ children }: { children: React.ReactNode }) {
  const user = useAuthStore((s) => s.user);
  const bootstrapMe = useAuthStore((s) => s.bootstrapMe);
  const [checked, setChecked] = useState(false);

  useEffect(() => {
    let cancelled = false;
    if (user) {
      setChecked(true);
      return;
    }
    void bootstrapMe().finally(() => {
      if (!cancelled) setChecked(true);
    });
    return () => {
      cancelled = true;
    };
  }, [user, bootstrapMe]);

  if (!checked && !user) {
    return <div style={{ padding: 32, color: "var(--text-dim)" }}>正在验证身份…</div>;
  }
  if (!user) {
    return <Navigate to="/login" replace />;
  }
  return <>{children}</>;
}
