import { create } from "zustand";
import { authApi } from "@/api/endpoints";
import { clearTokens, setTokens } from "@/api/client";
import type { UserPublic } from "@/types/api";

/**
 * 支持三种登录方式：
 *  1) 米盾代理（自动）—— /users/me 通过 X-Proxy-UserDetail 识别身份；
 *  2) 账号密码 —— POST /auth/login 返回 access/refresh JWT，浏览器本地保存；
 *  3) 测试样例账号 —— 走相同的账号密码通道（admin / zhangmingyuan / lisihan 密码 test123）。
 */
interface AuthState {
  user: UserPublic | null;
  loading: boolean;
  error: string | null;
  /** 账号密码登录（同时覆盖测试样例）。成功后 setTokens 并刷新 user。 */
  login: (email: string, password: string) => Promise<void>;
  bootstrapMe: () => Promise<void>;
  logout: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  loading: false,
  error: null,
  async login(email: string, password: string) {
    set({ loading: true, error: null });
    try {
      const resp = await authApi.login(email, password);
      setTokens(resp.tokens.access_token, resp.tokens.refresh_token);
      set({ user: resp.user });
    } catch (err) {
      const e = err as { message?: string; errorCode?: string };
      const msg = e.message || "登录失败";
      set({ error: msg });
      throw new Error(msg);
    } finally {
      set({ loading: false });
    }
  },
  async bootstrapMe() {
    try {
      const me = await authApi.me();
      set({ user: me });
    } catch {
      clearTokens();
      set({ user: null });
    }
  },
  logout() {
    clearTokens();
    set({ user: null });
  },
}));
