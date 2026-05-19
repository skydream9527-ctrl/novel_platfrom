import React, { useState, useEffect, useRef } from 'react';
import { parseLinks, ParsedLink } from '../api/links';

interface WikiLinkEditorProps {
  content: string;
  taskId: number;
  onContentChange: (content: string) => void;
  onLinkClick?: (type: string, id: number) => void;
}

export const WikiLinkEditor: React.FC<WikiLinkEditorProps> = ({
  content,
  taskId,
  onContentChange,
  onLinkClick,
}) => {
  const [parsedLinks, setParsedLinks] = useState<ParsedLink[]>([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const [cursorPosition, setCursorPosition] = useState(0);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // 解析内容中的链接
  useEffect(() => {
    const parseContent = async () => {
      if (content) {
        try {
          const result = await parseLinks(content, taskId);
          setParsedLinks(result.links);
        } catch (error) {
          console.error('Failed to parse links:', error);
        }
      }
    };

    const debounceTimer = setTimeout(parseContent, 500);
    return () => clearTimeout(debounceTimer);
  }, [content, taskId]);

  // 处理文本变化
  const handleTextChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const newContent = e.target.value;
    onContentChange(newContent);

    // 检测是否输入了 [[
    const textarea = e.target;
    const cursorPos = textarea.selectionStart;
    setCursorPosition(cursorPos);

    const textBeforeCursor = newContent.substring(0, cursorPos);
    const lastOpenBracket = textBeforeCursor.lastIndexOf('[[');

    if (lastOpenBracket !== -1) {
      const textAfterBracket = textBeforeCursor.substring(lastOpenBracket + 2);
      if (!textAfterBracket.includes(']]')) {
        // 正在输入链接
        setShowSuggestions(true);
        // 这里可以添加自动补全逻辑
      }
    } else {
      setShowSuggestions(false);
    }
  };

  // 插入链接语法
  const insertLinkSyntax = (type: string = '', name: string = '') => {
    const textarea = textareaRef.current;
    if (!textarea) return;

    const start = textarea.selectionStart;
    const end = textarea.selectionEnd;
    const selectedText = content.substring(start, end);

    let linkText = '';
    if (type && name) {
      linkText = `[[${type}:${name}]]`;
    } else if (selectedText) {
      linkText = `[[${selectedText}]]`;
    } else {
      linkText = '[[链接名称]]';
    }

    const newContent =
      content.substring(0, start) + linkText + content.substring(end);
    onContentChange(newContent);

    // 设置光标位置
    setTimeout(() => {
      textarea.focus();
      const newCursorPos = start + linkText.length;
      textarea.setSelectionRange(newCursorPos, newCursorPos);
    }, 0);
  };

  // 渲染高亮的预览
  const renderHighlightedContent = () => {
    if (!parsedLinks.length) {
      return <pre className="whitespace-pre-wrap font-mono text-sm">{content}</pre>;
    }

    const parts: React.ReactNode[] = [];
    let lastIndex = 0;

    parsedLinks.forEach((link, index) => {
      // 添加链接前的文本
      if (link.start > lastIndex) {
        parts.push(
          <span key={`text-${index}`}>
            {content.substring(lastIndex, link.start)}
          </span>
        );
      }

      // 添加链接
      parts.push(
        <span
          key={`link-${index}`}
          className={`cursor-pointer underline ${
            link.resolved
              ? 'text-blue-600 hover:text-blue-800'
              : 'text-red-500 hover:text-red-700'
          }`}
          onClick={() => {
            if (link.resolved && link.target && onLinkClick) {
              onLinkClick(link.target.type, link.target.id);
            }
          }}
          title={link.resolved ? `跳转到 ${link.name}` : `未找到: ${link.name}`}
        >
          {link.full_match}
        </span>
      );

      lastIndex = link.end;
    });

    // 添加剩余的文本
    if (lastIndex < content.length) {
      parts.push(
        <span key="text-end">{content.substring(lastIndex)}</span>
      );
    }

    return <pre className="whitespace-pre-wrap font-mono text-sm">{parts}</pre>;
  };

  return (
    <div className="wiki-link-editor">
      <div className="mb-2 flex items-center gap-2">
        <button
          onClick={() => insertLinkSyntax()}
          className="px-2 py-1 text-xs bg-gray-100 hover:bg-gray-200 rounded"
          title="插入章节链接"
        >
          [[章节]]
        </button>
        <button
          onClick={() => insertLinkSyntax('角色', '角色名')}
          className="px-2 py-1 text-xs bg-gray-100 hover:bg-gray-200 rounded"
          title="插入角色链接"
        >
          [[角色:]]
        </button>
        <button
          onClick={() => insertLinkSyntax('笔记', '笔记名')}
          className="px-2 py-1 text-xs bg-gray-100 hover:bg-gray-200 rounded"
          title="插入笔记链接"
        >
          [[笔记:]]
        </button>
        <div className="text-xs text-gray-500">
          {parsedLinks.length > 0 && (
            <span>
              {parsedLinks.filter((l) => l.resolved).length}/{parsedLinks.length} 个链接已解析
            </span>
          )}
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4">
        {/* 编辑区 */}
        <div>
          <textarea
            ref={textareaRef}
            value={content}
            onChange={handleTextChange}
            className="w-full h-64 p-3 border rounded-lg font-mono text-sm resize-none focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="输入内容，使用 [[链接名称]] 创建双向链接..."
          />
        </div>

        {/* 预览区 */}
        <div className="border rounded-lg p-3 bg-gray-50 overflow-auto h-64">
          <div className="text-xs text-gray-500 mb-2">预览</div>
          {renderHighlightedContent()}
        </div>
      </div>

      {/* 链接列表 */}
      {parsedLinks.length > 0 && (
        <div className="mt-4">
          <h4 className="text-sm font-semibold mb-2">检测到的链接</h4>
          <div className="space-y-1">
            {parsedLinks.map((link, index) => (
              <div
                key={index}
                className={`text-xs p-2 rounded ${
                  link.resolved ? 'bg-green-50 text-green-800' : 'bg-red-50 text-red-800'
                }`}
              >
                <span className="font-mono">{link.full_match}</span>
                <span className="ml-2">
                  {link.resolved ? '✓ 已解析' : '✗ 未找到'}
                </span>
                {link.target && (
                  <span className="ml-2 text-gray-500">
                    → {link.target.type}:{link.target.id}
                  </span>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default WikiLinkEditor;
