import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import { vscDarkPlus } from "react-syntax-highlighter/dist/esm/styles/prism";
import DOMPurify from "dompurify";
import "./markdown.css";

interface Props {
  content: string;
}

export function MarkdownRenderer({ content }: Props) {
  // sanitize raw HTML if any leaked through (defense-in-depth)
  const safe = DOMPurify.sanitize(content, { USE_PROFILES: { html: true } });
  return (
    <div className="md-body">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          a: ({ children, href }) => (
            <a href={href} target="_blank" rel="noopener noreferrer">
              {children}
            </a>
          ),
          code({ inline, className, children, ...rest }: any) {
            const match = /language-(\w+)/.exec(className || "");
            if (!inline && match) {
              return (
                <div className="md-code-block">
                  <div className="md-code-head">
                    <span className="md-lang">{match[1]}</span>
                    <button
                      className="md-copy"
                      onClick={() => navigator.clipboard.writeText(String(children))}
                    >
                      复制
                    </button>
                  </div>
                  <SyntaxHighlighter language={match[1]} style={vscDarkPlus} PreTag="div" customStyle={{ margin: 0 }}>
                    {String(children).replace(/\n$/, "")}
                  </SyntaxHighlighter>
                </div>
              );
            }
            return (
              <code className={className} {...rest}>
                {children}
              </code>
            );
          },
        }}
      >
        {safe}
      </ReactMarkdown>
    </div>
  );
}
