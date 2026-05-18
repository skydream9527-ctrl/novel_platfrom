import { useUIStore } from "@/stores/uiStore";
import "./Toast.css";

export function ToastHost() {
  const toasts = useUIStore((s) => s.toasts);
  const dismiss = useUIStore((s) => s.dismissToast);
  return (
    <div className="toast-host">
      {toasts.map((t) => (
        <div key={t.id} className={`toast toast-${t.kind}`} onClick={() => dismiss(t.id)}>
          <span>{t.message}</span>
        </div>
      ))}
    </div>
  );
}
