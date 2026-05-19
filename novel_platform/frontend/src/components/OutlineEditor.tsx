import React, { useState, useEffect, useCallback } from 'react';
import {
  OutlineNode,
  getOutline,
  createOutlineNode,
  updateOutlineNode,
  deleteOutlineNode,
  moveOutlineNode,
  linkChapter,
  unlinkChapter,
} from '../api/outline';

interface OutlineEditorProps {
  taskId: number;
  chapters?: Array<{ id: number; title: string }>;
  onNodeSelect?: (node: OutlineNode) => void;
  onChapterClick?: (chapterId: number) => void;
}

const NODE_TYPE_ICONS: Record<string, string> = {
  root: '📚',
  act: '📖',
  chapter: '📄',
  scene: '🎬',
  node: '💡',
};

const NODE_TYPE_LABELS: Record<string, string> = {
  root: '根节点',
  act: '幕/卷',
  chapter: '章节',
  scene: '场景',
  node: '普通节点',
};

export const OutlineEditor: React.FC<OutlineEditorProps> = ({
  taskId,
  chapters = [],
  onNodeSelect,
  onChapterClick,
}) => {
  const [outline, setOutline] = useState<OutlineNode[]>([]);
  const [selectedNode, setSelectedNode] = useState<OutlineNode | null>(null);
  const [isEditing, setIsEditing] = useState(false);
  const [editTitle, setEditTitle] = useState('');
  const [editSummary, setEditSummary] = useState('');
  const [editNodeType, setEditNodeType] = useState('node');
  const [isLoading, setIsLoading] = useState(true);
  const [isCreating, setIsCreating] = useState(false);
  const [newNodeParentId, setNewNodeParentId] = useState<number | null>(null);

  // 加载大纲
  useEffect(() => {
    loadOutline();
  }, [taskId]);

  const loadOutline = async () => {
    setIsLoading(true);
    try {
      const data = await getOutline(taskId);
      setOutline(data);
    } catch (error) {
      console.error('Failed to load outline:', error);
    } finally {
      setIsLoading(false);
    }
  };

  // 创建节点
  const handleCreate = async () => {
    if (!editTitle.trim()) return;

    try {
      await createOutlineNode({
        task_id: taskId,
        parent_id: newNodeParentId ?? undefined,
        title: editTitle.trim(),
        summary: editSummary,
        node_type: editNodeType,
      });
      setIsCreating(false);
      setEditTitle('');
      setEditSummary('');
      setEditNodeType('node');
      loadOutline();
    } catch (error) {
      console.error('Failed to create node:', error);
    }
  };

  // 更新节点
  const handleUpdate = async () => {
    if (!selectedNode || !editTitle.trim()) return;

    try {
      await updateOutlineNode(selectedNode.id, {
        title: editTitle.trim(),
        summary: editSummary,
        node_type: editNodeType,
      });
      setIsEditing(false);
      loadOutline();
    } catch (error) {
      console.error('Failed to update node:', error);
    }
  };

  // 删除节点
  const handleDelete = async (nodeId: number) => {
    if (!confirm('确定要删除此节点及其所有子节点吗？')) return;

    try {
      await deleteOutlineNode(nodeId);
      if (selectedNode?.id === nodeId) {
        setSelectedNode(null);
      }
      loadOutline();
    } catch (error) {
      console.error('Failed to delete node:', error);
    }
  };

  // 切换折叠状态
  const toggleCollapse = async (node: OutlineNode) => {
    try {
      await updateOutlineNode(node.id, {
        is_collapsed: !node.is_collapsed,
      });
      loadOutline();
    } catch (error) {
      console.error('Failed to toggle collapse:', error);
    }
  };

  // 关联章节
  const handleLinkChapter = async (nodeId: number, chapterId: number) => {
    try {
      await linkChapter(nodeId, chapterId);
      loadOutline();
    } catch (error) {
      console.error('Failed to link chapter:', error);
    }
  };

  // 取消关联章节
  const handleUnlinkChapter = async (nodeId: number) => {
    try {
      await unlinkChapter(nodeId);
      loadOutline();
    } catch (error) {
      console.error('Failed to unlink chapter:', error);
    }
  };

  // 开始编辑
  const startEditing = (node: OutlineNode) => {
    setSelectedNode(node);
    setEditTitle(node.title);
    setEditSummary(node.summary);
    setEditNodeType(node.node_type);
    setIsEditing(true);
    setIsCreating(false);
  };

  // 开始创建子节点
  const startCreating = (parentId: number | null = null) => {
    setNewNodeParentId(parentId);
    setEditTitle('');
    setEditSummary('');
    setEditNodeType('node');
    setIsCreating(true);
    setIsEditing(false);
  };

  // 取消编辑
  const cancelEditing = () => {
    setIsEditing(false);
    setIsCreating(false);
    setEditTitle('');
    setEditSummary('');
  };

  // 渲染树节点
  const renderTreeNode = (node: OutlineNode, depth: number = 0) => {
    const hasChildren = node.children && node.children.length > 0;
    const isSelected = selectedNode?.id === node.id;

    return (
      <div key={node.id} className="outline-tree-node">
        <div
          className={`flex items-center gap-1 px-2 py-1 cursor-pointer rounded ${
            isSelected ? 'bg-blue-100' : 'hover:bg-gray-100'
          }`}
          style={{ paddingLeft: `${depth * 20 + 8}px` }}
          onClick={() => {
            setSelectedNode(node);
            onNodeSelect?.(node);
          }}
        >
          {/* 折叠按钮 */}
          {hasChildren ? (
            <button
              onClick={(e) => {
                e.stopPropagation();
                toggleCollapse(node);
              }}
              className="w-4 h-4 flex items-center justify-center text-gray-500"
            >
              {node.is_collapsed ? '▶' : '▼'}
            </button>
          ) : (
            <div className="w-4" />
          )}

          {/* 节点图标 */}
          <span className="text-sm">
            {NODE_TYPE_ICONS[node.node_type] || '💡'}
          </span>

          {/* 节点标题 */}
          <span className="flex-1 text-sm truncate">{node.title}</span>

          {/* 章节关联指示 */}
          {node.chapter_id && (
            <span
              className="text-xs text-blue-500 cursor-pointer"
              onClick={(e) => {
                e.stopPropagation();
                onChapterClick?.(node.chapter_id!);
              }}
            >
              📎
            </span>
          )}

          {/* 操作按钮 */}
          <div className="flex gap-1 opacity-0 group-hover:opacity-100">
            <button
              onClick={(e) => {
                e.stopPropagation();
                startCreating(node.id);
              }}
              className="p-1 text-gray-400 hover:text-gray-600"
              title="添加子节点"
            >
              +
            </button>
            <button
              onClick={(e) => {
                e.stopPropagation();
                startEditing(node);
              }}
              className="p-1 text-gray-400 hover:text-gray-600"
              title="编辑"
            >
              ✏️
            </button>
            <button
              onClick={(e) => {
                e.stopPropagation();
                handleDelete(node.id);
              }}
              className="p-1 text-gray-400 hover:text-red-600"
              title="删除"
            >
              🗑️
            </button>
          </div>
        </div>

        {/* 子节点 */}
        {hasChildren && !node.is_collapsed && (
          <div>
            {node.children.map((child) => renderTreeNode(child, depth + 1))}
          </div>
        )}
      </div>
    );
  };

  if (isLoading) {
    return (
      <div className="outline-editor p-4">
        <div className="text-center text-gray-500">加载中...</div>
      </div>
    );
  }

  return (
    <div className="outline-editor flex">
      {/* 左侧：大纲树 */}
      <div className="flex-1 border-r pr-4">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold">大纲</h3>
          <button
            onClick={() => startCreating(null)}
            className="px-3 py-1 text-sm bg-blue-500 text-white rounded hover:bg-blue-600"
          >
            + 添加根节点
          </button>
        </div>

        {/* 大纲树 */}
        <div className="outline-tree max-h-[500px] overflow-y-auto">
          {outline.length === 0 ? (
            <div className="text-center text-gray-500 py-8">
              暂无大纲节点，点击上方按钮创建
            </div>
          ) : (
            outline.map((node) => renderTreeNode(node))
          )}
        </div>
      </div>

      {/* 右侧：编辑面板 */}
      <div className="w-80 pl-4">
        {(isEditing || isCreating) && (
          <div className="p-3 bg-gray-50 rounded-lg">
            <h4 className="text-sm font-medium mb-3">
              {isEditing ? '编辑节点' : '创建新节点'}
            </h4>
            <div className="space-y-3">
              <div>
                <label className="block text-xs text-gray-500 mb-1">节点类型</label>
                <select
                  value={editNodeType}
                  onChange={(e) => setEditNodeType(e.target.value)}
                  className="w-full px-2 py-1 border rounded text-sm"
                >
                  {Object.entries(NODE_TYPE_LABELS).map(([value, label]) => (
                    <option key={value} value={value}>
                      {NODE_TYPE_ICONS[value]} {label}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-xs text-gray-500 mb-1">标题</label>
                <input
                  type="text"
                  value={editTitle}
                  onChange={(e) => setEditTitle(e.target.value)}
                  className="w-full px-2 py-1 border rounded text-sm"
                  placeholder="输入节点标题"
                />
              </div>
              <div>
                <label className="block text-xs text-gray-500 mb-1">摘要</label>
                <textarea
                  value={editSummary}
                  onChange={(e) => setEditSummary(e.target.value)}
                  className="w-full px-2 py-1 border rounded text-sm resize-none"
                  rows={3}
                  placeholder="输入节点摘要"
                />
              </div>
              <div className="flex gap-2">
                <button
                  onClick={isEditing ? handleUpdate : handleCreate}
                  className="px-3 py-1 text-sm bg-blue-500 text-white rounded hover:bg-blue-600"
                >
                  {isEditing ? '保存' : '创建'}
                </button>
                <button
                  onClick={cancelEditing}
                  className="px-3 py-1 text-sm bg-gray-200 rounded hover:bg-gray-300"
                >
                  取消
                </button>
              </div>
            </div>
          </div>
        )}

        {/* 节点详情 */}
        {selectedNode && !isEditing && !isCreating && (
          <div className="p-3 bg-gray-50 rounded-lg">
            <h4 className="text-sm font-medium mb-2">
              {NODE_TYPE_ICONS[selectedNode.node_type]} {selectedNode.title}
            </h4>
            <div className="text-xs text-gray-500 mb-2">
              类型: {NODE_TYPE_LABELS[selectedNode.node_type]}
            </div>
            {selectedNode.summary && (
              <div className="text-sm text-gray-600 mb-3">
                {selectedNode.summary}
              </div>
            )}

            {/* 章节关联 */}
            <div className="mb-3">
              <label className="block text-xs text-gray-500 mb-1">关联章节</label>
              {selectedNode.chapter_id ? (
                <div className="flex items-center gap-2">
                  <span className="text-sm">
                    {chapters.find((c) => c.id === selectedNode.chapter_id)?.title || '未知章节'}
                  </span>
                  <button
                    onClick={() => handleUnlinkChapter(selectedNode.id)}
                    className="text-xs text-red-500 hover:text-red-700"
                  >
                    取消关联
                  </button>
                </div>
              ) : (
                <select
                  onChange={(e) => {
                    if (e.target.value) {
                      handleLinkChapter(selectedNode.id, parseInt(e.target.value));
                    }
                  }}
                  className="w-full px-2 py-1 border rounded text-sm"
                >
                  <option value="">选择章节</option>
                  {chapters.map((chapter) => (
                    <option key={chapter.id} value={chapter.id}>
                      {chapter.title}
                    </option>
                  ))}
                </select>
              )}
            </div>

            {/* 操作按钮 */}
            <div className="flex gap-2">
              <button
                onClick={() => startEditing(selectedNode)}
                className="px-3 py-1 text-sm bg-blue-500 text-white rounded hover:bg-blue-600"
              >
                编辑
              </button>
              <button
                onClick={() => startCreating(selectedNode.id)}
                className="px-3 py-1 text-sm bg-gray-200 rounded hover:bg-gray-300"
              >
                添加子节点
              </button>
              <button
                onClick={() => handleDelete(selectedNode.id)}
                className="px-3 py-1 text-sm bg-red-100 text-red-600 rounded hover:bg-red-200"
              >
                删除
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default OutlineEditor;
