import { ReactNode } from "react";
import "./ErrorState.css";

interface Props {
  icon?: string;
  title: string;
  description?: string;
  errorCode?: string;
  actions?: ReactNode;
}

export function ErrorState({ icon = "💥", title, description, errorCode, actions }: Props) {
  return (
    <div className="error-state">
      <div className="es-icon">{icon}</div>
      <div className="es-title">{title}</div>
      {description && <div className="es-desc">{description}</div>}
      {errorCode && <div className="es-code">{errorCode}</div>}
      {actions && <div className="es-actions">{actions}</div>}
    </div>
  );
}

export function EmptyState({
  illustration = "📋",
  title,
  hint,
  cta,
}: {
  illustration?: string;
  title: string;
  hint?: string;
  cta?: ReactNode;
}) {
  return (
    <div className="empty-state">
      <div className="es-illust">{illustration}</div>
      <div className="es-title">{title}</div>
      {hint && <div className="es-desc">{hint}</div>}
      {cta && <div className="es-actions">{cta}</div>}
    </div>
  );
}
