import React, { useState, useEffect } from 'react';
import { Tag, getTagsByTask, createTag, updateTag, deleteTag } from '../api/tags';

interface TagManagerProps {
  taskId: number;
  onTagSelect?: (tag: Tag) => void;
  selectedTagId?: number;
}

const PRESET_COLORS = [
  '#ef4444', '#f97316', '#f59e0b', '#eab308',
  '#84cc16', '#22c55e', '#10b981', '#14b8a6',
  '#06b6d4', '#0ea5e9', '#3b82f6', '#6366f1',
  '#8b5cf6', '#a855f7', '#d946ef', '#ec4899',
];

export const TagManager: React.FC<TagManagerProps> = ({
  taskId,
  onTagSelect,
  selectedTagId,
}) => {
  const [tags, setTags] = useState<Tag[]>([]);
  const [isCreating, setIsCreating] = useState(false);
  const [editingTag, setEditingTag] = useState<Tag | null>(null);
  const [newTagName, setNewTagName] = useState('');
  const [newTagColor, setNewTagColor] = useState(PRESET_COLORS[0]);

  // 加载标签列表
  useEffect(() => {
    loadTags();
  }, [taskId]);

  const loadTags = async () => {
    try {
      const data = await getTagsByTask(taskId);
      setTags(data);
    } catch (error) {
      console.error('Failed to load tags:', error);
    }
  };

  // 创建标签
  const handleCreate = async () => {
    if (!newTagName.trim()) return;

    try {
      await createTag({
        task_id: taskId,
        name: newTagName.trim(),
        color: newTagColor,
      });
      setNewTagName('');
      setIsCreating(false);
      loadTags();
    } catch (error) {
      console.error('Failed to create tag:', error);
    }
  };

  // 更新标签
  const handleUpdate = async () => {
    if (!editingTag || !newTagName.trim()) return;

    try {
      await updateTag(editingTag.id, {
        name: newTagName.trim(),
        color: newTagColor,
      });
      setEditingTag(null);
      setNewTagName('');
      loadTags();
    } catch (error) {
      console.error('Failed to update tag:', error);
    }
  };

  // 删除标签
  const handleDelete = async (tagId: number) => {
    if (!confirm('确定要删除这个标签吗？')) return;

    try {
      await deleteTag(tagId);
      loadTags();
    } catch (error) {
      console.error('Failed to delete tag:', error);
    }
  };

  // 开始编辑标签
  const startEditing = (tag: Tag) => {
    setEditingTag(tag);
    setNewTagName(tag.name);
    setNewTagColor(tag.color || PRESET_COLORS[0]);
    setIsCreating(false);
  };

  // 取消编辑
  const cancelEditing = () => {
    setEditingTag(null);
    setNewTagName('');
    setIsCreating(false);
  };

  return (
    <div className="tag-manager">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold">标签管理</h3>
        <button
          onClick={() => {
            setIsCreating(true);
            setEditingTag(null);
            setNewTagName('');
            setNewTagColor(PRESET_COLORS[0]);
          }}
          className="px-3 py-1 text-sm bg-blue-500 text-white rounded hover:bg-blue-600"
        >
          + 新建标签
        </button>
      </div>

      {/* 创建/编辑表单 */}
      {(isCreating || editingTag) && (
        <div className="mb-4 p-3 bg-gray-50 rounded-lg">
          <h4 className="text-sm font-medium mb-2">
            {editingTag ? '编辑标签' : '创建新标签'}
          </h4>
          <div className="space-y-3">
            <div>
              <label className="block text-xs text-gray-500 mb-1">标签名称</label>
              <input
                type="text"
                value={newTagName}
                onChange={(e) => setNewTagName(e.target.value)}
                className="w-full px-2 py-1 border rounded text-sm"
                placeholder="输入标签名称"
              />
            </div>
            <div>
              <label className="block text-xs text-gray-500 mb-1">标签颜色</label>
              <div className="flex flex-wrap gap-2">
                {PRESET_COLORS.map((color) => (
                  <button
                    key={color}
                    onClick={() => setNewTagColor(color)}
                    className={`w-6 h-6 rounded-full border-2 ${
                      newTagColor === color ? 'border-gray-800' : 'border-transparent'
                    }`}
                    style={{ backgroundColor: color }}
                  />
                ))}
              </div>
            </div>
            <div className="flex gap-2">
              <button
                onClick={editingTag ? handleUpdate : handleCreate}
                className="px-3 py-1 text-sm bg-blue-500 text-white rounded hover:bg-blue-600"
              >
                {editingTag ? '保存' : '创建'}
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

      {/* 标签列表 */}
      <div className="space-y-2">
        {tags.map((tag) => (
          <div
            key={tag.id}
            className={`flex items-center justify-between p-2 rounded-lg cursor-pointer ${
              selectedTagId === tag.id ? 'bg-blue-50 border border-blue-200' : 'bg-white border'
            }`}
            onClick={() => onTagSelect?.(tag)}
          >
            <div className="flex items-center gap-2">
              <div
                className="w-3 h-3 rounded-full"
                style={{ backgroundColor: tag.color || '#6b7280' }}
              />
              <span className="text-sm font-medium">{tag.name}</span>
              <span className="text-xs text-gray-500">
                {tag.usage_count} 个内容
              </span>
            </div>
            <div className="flex gap-1">
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  startEditing(tag);
                }}
                className="p-1 text-gray-400 hover:text-gray-600"
                title="编辑"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                </svg>
              </button>
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  handleDelete(tag.id);
                }}
                className="p-1 text-gray-400 hover:text-red-600"
                title="删除"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                </svg>
              </button>
            </div>
          </div>
        ))}

        {tags.length === 0 && (
          <div className="text-center text-gray-500 text-sm py-4">
            暂无标签，点击上方按钮创建
          </div>
        )}
      </div>
    </div>
  );
};

export default TagManager;
