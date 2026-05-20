import { useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

interface Props {
  title: string;
  content: string;
  onClose: () => void;
}

export default function ReadingMode({ title, content, onClose }: Props) {
  const [fontSize, setFontSize] = useState(18);
  const [lineHeight, setLineHeight] = useState(2);
  const [theme, setTheme] = useState<"light" | "sepia" | "dark">("light");

  const themes = {
    light: { bg: "#ffffff", text: "#1a1a1a" },
    sepia: { bg: "#f5e6d3", text: "#5b4636" },
    dark: { bg: "#1a1a1a", text: "#e0e0e0" },
  };

  const currentTheme = themes[theme];

  return (
    <div style={{
      position: "fixed",
      inset: 0,
      zIndex: 1000,
      background: currentTheme.bg,
      color: currentTheme.text,
      overflow: "auto",
    }}>
      {/* Toolbar */}
      <div style={{
        position: "fixed",
        top: 0,
        left: 0,
        right: 0,
        display: "flex",
        justifyContent: "space-between",
        alignItems: "center",
        padding: "12px 24px",
        background: theme === "dark" ? "#2a2a2a" : "#f5f5f5",
        borderBottom: `1px solid ${theme === "dark" ? "#444" : "#e0e0e0"}`,
        zIndex: 10,
      }}>
        <button onClick={onClose} style={{
          background: "none",
          border: "none",
          cursor: "pointer",
          fontSize: 16,
          color: currentTheme.text,
        }}>
          ← 返回编辑
        </button>

        <div style={{ display: "flex", gap: 16, alignItems: "center" }}>
          <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
            <span style={{ fontSize: 13 }}>字号</span>
            <button onClick={() => setFontSize((s) => Math.max(14, s - 2))} style={{ background: "none", border: "1px solid #ccc", borderRadius: 4, padding: "2px 8px", cursor: "pointer" }}>-</button>
            <span style={{ fontSize: 13, minWidth: 30, textAlign: "center" }}>{fontSize}</span>
            <button onClick={() => setFontSize((s) => Math.min(28, s + 2))} style={{ background: "none", border: "1px solid #ccc", borderRadius: 4, padding: "2px 8px", cursor: "pointer" }}>+</button>
          </div>

          <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
            <span style={{ fontSize: 13 }}>行距</span>
            <button onClick={() => setLineHeight((l) => Math.max(1.5, l - 0.2))} style={{ background: "none", border: "1px solid #ccc", borderRadius: 4, padding: "2px 8px", cursor: "pointer" }}>-</button>
            <span style={{ fontSize: 13, minWidth: 30, textAlign: "center" }}>{lineHeight.toFixed(1)}</span>
            <button onClick={() => setLineHeight((l) => Math.min(3, l + 0.2))} style={{ background: "none", border: "1px solid #ccc", borderRadius: 4, padding: "2px 8px", cursor: "pointer" }}>+</button>
          </div>

          <div style={{ display: "flex", gap: 8 }}>
            {(["light", "sepia", "dark"] as const).map((t) => (
              <button
                key={t}
                onClick={() => setTheme(t)}
                style={{
                  width: 28,
                  height: 28,
                  borderRadius: "50%",
                  background: themes[t].bg,
                  border: theme === t ? "2px solid #3b82f6" : "2px solid #ccc",
                  cursor: "pointer",
                }}
              />
            ))}
          </div>
        </div>
      </div>

      {/* Content */}
      <div style={{
        maxWidth: 700,
        margin: "80px auto 40px",
        padding: "0 24px",
        fontSize,
        lineHeight,
        fontFamily: '"Noto Serif SC", "Source Han Serif SC", Georgia, serif',
      }}>
        <h1 style={{
          fontSize: fontSize * 1.5,
          textAlign: "center",
          marginBottom: 40,
          fontWeight: 700,
        }}>
          {title}
        </h1>
        <div className="reading-content">
          <ReactMarkdown remarkPlugins={[remarkGfm]}>{content || "*暂无内容*"}</ReactMarkdown>
        </div>
      </div>
    </div>
  );
}
