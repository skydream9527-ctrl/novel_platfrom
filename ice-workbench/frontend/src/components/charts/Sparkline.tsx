/**
 * Minimal SVG sparkline + bar chart for admin dashboards.
 * Avoids pulling in echarts to keep bundle small.
 */
import { useMemo } from "react";

export function Sparkline({
  values,
  width = 600,
  height = 80,
  stroke = "var(--primary)",
  fill = "var(--primary-dim)",
}: {
  values: number[];
  width?: number;
  height?: number;
  stroke?: string;
  fill?: string;
}) {
  const path = useMemo(() => buildPath(values, width, height), [values, width, height]);
  if (values.length === 0) return <div style={{ height, width: "100%", color: "var(--text-muted)", textAlign: "center" }}>暂无数据</div>;
  return (
    <svg width="100%" height={height} viewBox={`0 0 ${width} ${height}`} preserveAspectRatio="none" style={{ display: "block" }}>
      <path d={`${path.line} L ${width} ${height} L 0 ${height} Z`} fill={fill} />
      <path d={path.line} fill="none" stroke={stroke} strokeWidth={1.5} />
      {path.points.map((p, i) => (
        <circle key={i} cx={p.x} cy={p.y} r={1.6} fill={stroke} />
      ))}
    </svg>
  );
}

export function BarSeries({
  items,
  width = 600,
  height = 200,
  color = "var(--primary)",
  formatLabel,
  formatValue,
}: {
  items: { key: string; value: number }[];
  width?: number;
  height?: number;
  color?: string;
  formatLabel?: (key: string) => string;
  formatValue?: (v: number) => string;
}) {
  const max = Math.max(1, ...items.map((i) => i.value));
  if (items.length === 0)
    return <div style={{ height, color: "var(--text-muted)", textAlign: "center", paddingTop: 40 }}>暂无数据</div>;
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 6, width: "100%" }}>
      {items.map((it) => (
        <div key={it.key} style={{ display: "flex", alignItems: "center", gap: 8, fontSize: 12 }}>
          <span style={{ minWidth: 160, color: "var(--text-dim)", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
            {formatLabel ? formatLabel(it.key) : it.key}
          </span>
          <div style={{ flex: 1, background: "var(--surface-2)", borderRadius: 3, overflow: "hidden", height: 14 }}>
            <div
              style={{
                width: `${(it.value / max) * 100}%`,
                background: color,
                height: "100%",
                transition: "width .3s",
              }}
            />
          </div>
          <span style={{ minWidth: 80, textAlign: "right", color: "var(--text)" }}>
            {formatValue ? formatValue(it.value) : it.value}
          </span>
        </div>
      ))}
    </div>
  );
}

function buildPath(values: number[], w: number, h: number) {
  if (values.length === 0) return { line: "", points: [] };
  const max = Math.max(1, ...values);
  const min = 0;
  const dx = values.length > 1 ? w / (values.length - 1) : w;
  const points = values.map((v, i) => {
    const x = i * dx;
    const y = h - ((v - min) / (max - min || 1)) * (h - 6) - 3;
    return { x, y };
  });
  let line = `M ${points[0].x} ${points[0].y}`;
  for (let i = 1; i < points.length; i++) line += ` L ${points[i].x} ${points[i].y}`;
  return { line, points };
}
