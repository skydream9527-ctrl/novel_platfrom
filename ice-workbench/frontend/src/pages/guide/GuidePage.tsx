import { useEffect, useMemo, useState } from "react";
import { TopNav } from "@/components/shell/TopNav";
import { Skeleton } from "@/components/feedback/Skeleton";
import { ErrorState } from "@/components/feedback/ErrorState";
import { MarkdownRenderer } from "@/components/markdown/MarkdownRenderer";
import { guideApi } from "@/api/endpoints";
import "./Guide.css";

interface TocItem {
  level: number;
  text: string;
  id: string;
}

export function GuidePage() {
  const [content, setContent] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState("");

  useEffect(() => {
    guideApi
      .get()
      .then((r) => setContent(r.content))
      .catch((e) => setError(e.message));
  }, []);

  const toc = useMemo<TocItem[]>(() => {
    if (!content) return [];
    return content
      .split("\n")
      .filter((l) => /^##+\s/.test(l))
      .map((l) => {
        const m = l.match(/^(#+)\s+(.*)/)!;
        const text = m[2].trim().replace(/`/g, "");
        return {
          level: m[1].length,
          text,
          id: text.toLowerCase().replace(/\s+/g, "-"),
        };
      });
  }, [content]);

  const display = useMemo(() => {
    if (!content) return "";
    if (!search.trim()) return content;
    const re = new RegExp(`(${escape(search)})`, "gi");
    return content.replace(re, "**$1**");
  }, [content, search]);

  return (
    <div className="gd-page">
      <TopNav mode="workspace" crumb={<span>首页 / <span className="current">使用指南</span></span>} />
      <div className="gd-body">
        <aside className="gd-toc">
          <div className="gd-toc-head">📑 目录</div>
          <input
            className="gd-search"
            placeholder="🔍 关键词高亮"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
          <ul>
            {toc.map((t) => (
              <li key={t.id} className={`gd-toc-l${t.level}`}>
                <a href={`#${t.id}`}>{t.text}</a>
              </li>
            ))}
          </ul>
        </aside>
        <main className="gd-content">
          <div className="gd-info">
            <span>📅 最后更新 2026-05-07</span>
            <button onClick={() => window.print()} className="btn-ghost">🖨 打印</button>
            <a href="mailto:gongyunhe@example.com" className="btn-ghost">✉ 反馈</a>
          </div>
          {error ? (
            <ErrorState
              icon="🚫"
              title="加载失败"
              description={error}
              errorCode="GUIDE_LOAD_FAILED"
            />
          ) : content === null ? (
            <Skeleton lines={8} />
          ) : (
            <article className="gd-article">
              <MarkdownRenderer content={display} />
            </article>
          )}
        </main>
      </div>
    </div>
  );
}

function escape(s: string): string {
  return s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}
