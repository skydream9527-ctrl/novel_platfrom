import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { fileApi } from "@/api/endpoints";
import { MarkdownRenderer } from "@/components/markdown/MarkdownRenderer";
import { Skeleton } from "@/components/feedback/Skeleton";
import type { FileMeta } from "@/types/api";
import "./PublicFile.css";

const TEXT_EXTS = new Set(["md", "txt", "csv", "json", "tsv", "log", "yml", "yaml", "sql", "py"]);

function fmtSize(n: number): string {
  if (n < 1024) return `${n} B`;
  if (n < 1024 * 1024) return `${(n / 1024).toFixed(1)} KB`;
  return `${(n / 1024 / 1024).toFixed(1)} MB`;
}

export function PublicFilePage() {
  const { fileId } = useParams<{ fileId: string }>();
  const [meta, setMeta] = useState<FileMeta | null>(null);
  const [content, setContent] = useState<string | null>(null);
  const [binary, setBinary] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!fileId) return;
    setLoading(true);
    setError(null);
    fileApi
      .readPublic(fileId)
      .then((r) => {
        setMeta(r.meta);
        setBinary(!!r.binary);
        setContent(r.content);
      })
      .catch((err) => {
        const e = err as { message?: string; errorCode?: string };
        setError(`${e.message || "无法读取"}（${e.errorCode || "ERROR"}）`);
      })
      .finally(() => setLoading(false));
  }, [fileId]);

  useEffect(() => {
    if (meta?.name) {
      document.title = `${meta.name} · 公共文件`;
    }
  }, [meta?.name]);

  const ext = (meta?.format || "").toLowerCase();

  return (
    <div className="pf-page">
      <header className="pf-head">
        <div className="pf-title">
          {meta?.is_pinned && "📌 "}
          {meta?.name || (loading ? "加载中…" : "公共文件")}
        </div>
        {meta && (
          <div className="pf-meta">
            {meta.format} · {fmtSize(meta.size_bytes)}
          </div>
        )}
      </header>

      <main className="pf-body">
        {loading ? (
          <Skeleton lines={12} />
        ) : error ? (
          <div className="pf-error">{error}</div>
        ) : binary ? (
          <div className="pf-empty">该文件为二进制，暂不支持预览。</div>
        ) : ext === "md" ? (
          <MarkdownRenderer content={content || ""} />
        ) : TEXT_EXTS.has(ext) ? (
          <pre className="pf-pre">{content || ""}</pre>
        ) : (
          <pre className="pf-pre">{content || ""}</pre>
        )}
      </main>
    </div>
  );
}
