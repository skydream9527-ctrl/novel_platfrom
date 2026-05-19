import React, { useState, useEffect, useRef } from 'react';
import {
  Annotation,
  getAnnotations,
  createAnnotation,
  deleteAnnotation,
} from '../api/conflicts';

interface ReviewModeProps {
  taskId: number;
  chapterId: number;
  content: string;
  onExit?: () => void;
}

const ANNOTATION_TYPE_LABELS: Record<string, string> = {
  highlight: '高亮',
  underline: '下划线',
  strikethrough: '删除线',
  wavy: '波浪线',
  margin_note: '边注',
};

const ANNOTATION_COLORS = [
  '#fef08a', '#fde68a', '#fcd34d', '#fbbf24',
  '#bfdbfe', '#93c5fd', '#60a5fa', '#3b82f6',
  '#bbf7d0', '#86efac', '#4ade80', '#22c55e',
  '#fecaca', '#fca5a5', '#f87171', '#ef4444',
];

export const ReviewMode: React.FC<ReviewModeProps> = ({
  taskId,
  chapterId,
  content,
  onExit,
}) => {
  const [annotations, setAnnotations] = useState<Annotation[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [selectedText, setSelectedText] = useState('');
  const [selectionStart, setSelectionStart] = useState(0);
  const [selectionEnd, setSelectionEnd] = useState(0);
  const [showAnnotationMenu, setShowAnnotationMenu] = useState(false);
  const [menuPosition, setMenuPosition] = useState({ x: 0, y: 0 });
  const [annotationType, setAnnotationType] = useState('highlight');
  const [annotationColor, setAnnotationColor] = useState('#fef08a');
  const [note, setNote] = useState('');
  const [suggestion, setSuggestion] = useState('');
  const [showNoteInput, setShowNoteInput] = useState(false);
  const contentRef = useRef<HTMLDivElement>(null);

  // 加载标注
  useEffect(() => {
    loadAnnotations();
  }, [chapterId]);

  const loadAnnotations = async () => {
    setIsLoading(true);
    try {
      const data = await getAnnotations(chapterId);
      setAnnotations(data);
    } catch (error) {
      console.error('Failed to load annotations:', error);
    } finally {
      setIsLoading(false);
    }
  };

  // 处理文本选择
  const handleTextSelect = () => {
    const selection = window.getSelection();
    if (!selection || selection.isCollapsed) {
      setShowAnnotationMenu(false);
      return;
    }

    const range = selection.getRangeAt(0);
    const selectedText = selection.toString().trim();

    if (!selectedText) {
      setShowAnnotationMenu(false);
      return;
    }

    // 计算选择位置
    const contentElement = contentRef.current;
    if (!contentElement) return;

    const preSelectionRange = range.cloneRange();
    preSelectionRange.selectNodeContents(contentElement);
    preSelectionRange.setEnd(range.startContainer, range.startOffset);
    const start = preSelectionRange.toString().length;

    setSelectedText(selectedText);
    setSelectionStart(start);
    setSelectionEnd(start + selectedText.length);

    // 显示标注菜单
    const rect = range.getBoundingClientRect();
    setMenuPosition({
      x: rect.left + rect.width / 2,
      y: rect.top - 10,
    });
    setShowAnnotationMenu(true);
    setShowNoteInput(false);
    setNote('');
    setSuggestion('');
  };

  // 创建标注
  const handleCreateAnnotation = async () => {
    try {
      await createAnnotation({
        task_id: taskId,
        chapter_id: chapterId,
        annotation_type: annotationType,
        color: annotationColor,
        selection_start: selectionStart,
        selection_end: selectionEnd,
        selected_text: selectedText,
        note: note || undefined,
        suggestion: suggestion || undefined,
      });
      setShowAnnotationMenu(false);
      setSelectedText('');
      loadAnnotations();
    } catch (error) {
      console.error('Failed to create annotation:', error);
    }
  };

  // 删除标注
  const handleDeleteAnnotation = async (annotationId: number) => {
    try {
      await deleteAnnotation(annotationId);
      loadAnnotations();
    } catch (error) {
      console.error('Failed to delete annotation:', error);
    }
  };

  // 渲染带标注的内容
  const renderContentWithAnnotations = () => {
    if (!content) return null;

    // 按位置排序标注
    const sortedAnnotations = [...annotations].sort(
      (a, b) => a.selection_start - b.selection_start
    );

    const parts: React.ReactNode[] = [];
    let lastIndex = 0;

    sortedAnnotations.forEach((ann, index) => {
      // 添加标注前的文本
      if (ann.selection_start > lastIndex) {
        parts.push(
          <span key={`text-${index}`}>
            {content.substring(lastIndex, ann.selection_start)}
          </span>
        );
      }

      // 添加标注文本
      const annotationStyle: React.CSSProperties = {};
      switch (ann.annotation_type) {
        case 'highlight':
          annotationStyle.backgroundColor = ann.color || '#fef08a';
          break;
        case 'underline':
          annotationStyle.textDecoration = 'underline';
          annotationStyle.textDecorationColor = ann.color || '#000';
          break;
        case 'strikethrough':
          annotationStyle.textDecoration = 'line-through';
          annotationStyle.textDecorationColor = ann.color || '#000';
          break;
        case 'wavy':
          annotationStyle.textDecoration = 'underline wavy';
          annotationStyle.textDecorationColor = ann.color || '#000';
          break;
        case 'margin_note':
          annotationStyle.borderLeft = `3px solid ${ann.color || '#3b82f6'}`;
          annotationStyle.paddingLeft = '4px';
          break;
      }

      parts.push(
        <span
          key={`ann-${ann.id}`}
          style={annotationStyle}
          className="cursor-pointer relative group"
          title={ann.note || ann.suggestion || ''}
        >
          {content.substring(ann.selection_start, ann.selection_end)}
          {/* 标注指示器 */}
          {(ann.note || ann.suggestion) && (
            <span className="absolute -top-1 -right-1 w-2 h-2 bg-blue-500 rounded-full" />
          )}
          {/* 删除按钮 */}
          <button
            onClick={(e) => {
              e.stopPropagation();
              handleDeleteAnnotation(ann.id);
            }}
            className="absolute -top-2 -right-2 w-4 h-4 bg-red-500 text-white rounded-full text-xs opacity-0 group-hover:opacity-100 flex items-center justify-center"
          >
            ×
          </button>
        </span>
      );

      lastIndex = ann.selection_end;
    });

    // 添加剩余文本
    if (lastIndex < content.length) {
      parts.push(
        <span key="text-end">{content.substring(lastIndex)}</span>
      );
    }

    return parts;
  };

  // 统计信息
  const stats = {
    total: annotations.length,
    highlights: annotations.filter((a) => a.annotation_type === 'highlight').length,
    suggestions: annotations.filter((a) => a.suggestion).length,
    notes: annotations.filter((a) => a.note).length,
  };

  // 阅读时间估算
  const wordCount = content ? content.length : 0;
  const readingTime = Math.ceil(wordCount / 500); // 假设每分钟500字

  if (isLoading) {
    return (
      <div className="review-mode p-4">
        <div className="text-center text-gray-500">加载中...</div>
      </div>
    );
  }

  return (
    <div className="review-mode">
      {/* 顶部工具栏 */}
      <div className="flex items-center justify-between p-4 bg-gray-50 border-b">
        <div className="flex items-center gap-4">
          <h3 className="text-lg font-semibold">审阅模式</h3>
          <div className="text-sm text-gray-500">
            字数: {wordCount} | 预计阅读时间: {readingTime} 分钟
          </div>
        </div>
        <div className="flex items-center gap-4">
          <div className="flex gap-2 text-sm">
            <span>标注: {stats.total}</span>
            <span>高亮: {stats.highlights}</span>
            <span>建议: {stats.suggestions}</span>
          </div>
          <button
            onClick={onExit}
            className="px-3 py-1 text-sm bg-gray-200 rounded hover:bg-gray-300"
          >
            退出审阅
          </button>
        </div>
      </div>

      {/* 内容区域 */}
      <div className="flex">
        {/* 主内容 */}
        <div className="flex-1 p-8 max-w-3xl mx-auto">
          <div
            ref={contentRef}
            className="prose prose-lg max-w-none leading-relaxed"
            onMouseUp={handleTextSelect}
            style={{
              fontSize: '18px',
              lineHeight: '1.8',
              fontFamily: 'Georgia, serif',
            }}
          >
            {renderContentWithAnnotations()}
          </div>
        </div>

        {/* 右侧标注列表 */}
        <div className="w-64 border-l p-4 bg-gray-50">
          <h4 className="text-sm font-semibold mb-3">标注列表</h4>
          <div className="space-y-2 max-h-[600px] overflow-y-auto">
            {annotations.map((ann) => (
              <div
                key={ann.id}
                className="p-2 bg-white rounded border text-sm"
              >
                <div className="flex items-center gap-2 mb-1">
                  <span
                    className="w-3 h-3 rounded"
                    style={{ backgroundColor: ann.color || '#fef08a' }}
                  />
                  <span className="text-xs text-gray-500">
                    {ANNOTATION_TYPE_LABELS[ann.annotation_type]}
                  </span>
                </div>
                {ann.selected_text && (
                  <p className="text-xs text-gray-600 line-clamp-2">
                    "{ann.selected_text}"
                  </p>
                )}
                {ann.note && (
                  <p className="text-xs text-blue-600 mt-1">📝 {ann.note}</p>
                )}
                {ann.suggestion && (
                  <p className="text-xs text-green-600 mt-1">💡 {ann.suggestion}</p>
                )}
              </div>
            ))}
            {annotations.length === 0 && (
              <div className="text-center text-gray-500 text-sm py-4">
                暂无标注
              </div>
            )}
          </div>
        </div>
      </div>

      {/* 标注菜单 */}
      {showAnnotationMenu && (
        <div
          className="fixed bg-white border rounded-lg shadow-lg p-3 z-50"
          style={{
            left: menuPosition.x,
            top: menuPosition.y,
            transform: 'translate(-50%, -100%)',
          }}
        >
          <div className="mb-2">
            <label className="block text-xs text-gray-500 mb-1">标注类型</label>
            <div className="flex gap-1">
              {Object.entries(ANNOTATION_TYPE_LABELS).map(([value, label]) => (
                <button
                  key={value}
                  onClick={() => setAnnotationType(value)}
                  className={`px-2 py-1 text-xs rounded ${
                    annotationType === value
                      ? 'bg-blue-500 text-white'
                      : 'bg-gray-100 hover:bg-gray-200'
                  }`}
                >
                  {label}
                </button>
              ))}
            </div>
          </div>

          <div className="mb-2">
            <label className="block text-xs text-gray-500 mb-1">颜色</label>
            <div className="flex flex-wrap gap-1">
              {ANNOTATION_COLORS.map((color) => (
                <button
                  key={color}
                  onClick={() => setAnnotationColor(color)}
                  className={`w-5 h-5 rounded border ${
                    annotationColor === color ? 'border-gray-800' : 'border-transparent'
                  }`}
                  style={{ backgroundColor: color }}
                />
              ))}
            </div>
          </div>

          <div className="mb-2">
            <button
              onClick={() => setShowNoteInput(!showNoteInput)}
              className="text-xs text-blue-500 hover:text-blue-700"
            >
              {showNoteInput ? '收起' : '添加备注/建议'}
            </button>
          </div>

          {showNoteInput && (
            <div className="mb-2 space-y-2">
              <div>
                <label className="block text-xs text-gray-500 mb-1">备注</label>
                <input
                  type="text"
                  value={note}
                  onChange={(e) => setNote(e.target.value)}
                  className="w-full px-2 py-1 border rounded text-xs"
                  placeholder="添加备注..."
                />
              </div>
              <div>
                <label className="block text-xs text-gray-500 mb-1">修改建议</label>
                <input
                  type="text"
                  value={suggestion}
                  onChange={(e) => setSuggestion(e.target.value)}
                  className="w-full px-2 py-1 border rounded text-xs"
                  placeholder="添加修改建议..."
                />
              </div>
            </div>
          )}

          <div className="flex gap-2">
            <button
              onClick={handleCreateAnnotation}
              className="px-3 py-1 text-xs bg-blue-500 text-white rounded hover:bg-blue-600"
            >
              添加标注
            </button>
            <button
              onClick={() => setShowAnnotationMenu(false)}
              className="px-3 py-1 text-xs bg-gray-200 rounded hover:bg-gray-300"
            >
              取消
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default ReviewMode;
