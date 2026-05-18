import axios, { AxiosError, AxiosResponse } from "axios";
import type { ApiEnvelope } from "@/types/api";

const TOKEN_KEY = "ice-access-token";
const REFRESH_KEY = "ice-refresh-token";

export function getAccessToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}

export function setTokens(access: string, refresh: string): void {
  localStorage.setItem(TOKEN_KEY, access);
  localStorage.setItem(REFRESH_KEY, refresh);
}

export function clearTokens(): void {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(REFRESH_KEY);
}

const http = axios.create({
  baseURL: "/api/v1",
  timeout: 30000,
});

http.interceptors.request.use((cfg) => {
  const token = getAccessToken();
  if (token) {
    cfg.headers.Authorization = `Bearer ${token}`;
  }
  return cfg;
});

http.interceptors.response.use(
  (resp: AxiosResponse<ApiEnvelope>) => resp,
  async (err: AxiosError<ApiEnvelope>) => {
    if (err.response?.status === 401 && err.config && !(err.config as any)._retried) {
      const refresh = localStorage.getItem(REFRESH_KEY);
      if (refresh) {
        try {
          const r = await axios.post<ApiEnvelope<{ access_token: string; refresh_token: string }>>(
            "/api/v1/auth/refresh",
            { refresh_token: refresh },
          );
          setTokens(r.data.data.access_token, r.data.data.refresh_token);
          (err.config as any)._retried = true;
          err.config.headers.Authorization = `Bearer ${r.data.data.access_token}`;
          return http.request(err.config);
        } catch {
          clearTokens();
          if (location.pathname !== "/login") {
            location.href = "/login";
          }
        }
      } else if (location.pathname !== "/login") {
        location.href = "/login";
      }
    }
    return Promise.reject(err);
  },
);

export interface ApiError extends Error {
  errorCode?: string;
  status?: number;
  detail?: unknown;
}

export async function api<T>(promise: Promise<AxiosResponse<ApiEnvelope<T>>>): Promise<T> {
  try {
    const resp = await promise;
    if (resp.data.code !== 0) {
      const e = new Error(resp.data.message) as ApiError;
      e.errorCode = resp.data.error_code;
      throw e;
    }
    return resp.data.data;
  } catch (err) {
    if (axios.isAxiosError<ApiEnvelope>(err) && err.response) {
      const body = err.response.data;
      const e = new Error(body?.message || err.message) as ApiError;
      e.errorCode = body?.error_code;
      e.status = err.response.status;
      e.detail = body?.data;
      throw e;
    }
    throw err;
  }
}

export default http;
