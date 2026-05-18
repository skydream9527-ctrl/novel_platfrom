import { create } from "zustand";

export type Theme = "dark" | "light";

export interface ToastMsg {
  id: string;
  kind: "success" | "warning" | "error" | "info";
  message: string;
}

interface UIState {
  theme: Theme;
  toasts: ToastMsg[];
  toggleTheme: () => void;
  setTheme: (t: Theme) => void;
  pushToast: (kind: ToastMsg["kind"], message: string) => void;
  dismissToast: (id: string) => void;
}

const THEME_KEY = "ice-theme-v3";

function readTheme(): Theme {
  if (typeof window === "undefined") return "dark";
  const saved = localStorage.getItem(THEME_KEY);
  return saved === "light" ? "light" : "dark";
}

function applyTheme(t: Theme) {
  document.documentElement.setAttribute("data-theme", t);
  localStorage.setItem(THEME_KEY, t);
}

export const useUIStore = create<UIState>((set, get) => ({
  theme: readTheme(),
  toasts: [],
  toggleTheme: () => {
    const next: Theme = get().theme === "dark" ? "light" : "dark";
    applyTheme(next);
    set({ theme: next });
  },
  setTheme: (t) => {
    applyTheme(t);
    set({ theme: t });
  },
  pushToast: (kind, message) => {
    const id = Math.random().toString(36).slice(2);
    set({ toasts: [...get().toasts, { id, kind, message }] });
    setTimeout(() => get().dismissToast(id), 3500);
  },
  dismissToast: (id) => set({ toasts: get().toasts.filter((t) => t.id !== id) }),
}));

if (typeof window !== "undefined") {
  applyTheme(readTheme());
}
