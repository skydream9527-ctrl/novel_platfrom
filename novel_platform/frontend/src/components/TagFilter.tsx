import React, { useState, useEffect } from 'react';
import { Tag, getTagsByTask } from '../api/tags';

interface TagFilterProps {
  taskId: number;
  onFilterChange: (selectedTagIds: number[]) => void;
  selectedTagIds?: number[];
}

export const TagFilter: React.FC<TagFilterProps> = ({
  taskId,
  onFilterChange,
  selectedTagIds = [],
}) => {
  const [tags, setTags] = useState<Tag[]>([]);
  const [isOpen, setIsOpen] = useState(false);

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

  // 切换标签选择
  const toggleTag = (tagId: number) => {
    const newSelected = selectedTagIds.includes(tagId)
      ? selectedTagIds.filter((id) => id !== tagId)
      : [...selectedTagIds, tagId];
    onFilterChange(newSelected);
  };

  // 清除所有筛选
  const clearFilter = () => {
    onFilterChange([]);
  };

  // 获取选中的标签
  const selectedTags = tags.filter((tag) => selectedTagIds.includes(tag.id));

  return (
    <div className="tag-filter">
      <div className="flex items-center gap-2">
        <button
          onClick={() => setIsOpen(!isOpen)}
          className={`inline-flex items-center gap-1 px-2 py-1 text-sm border rounded ${
            selectedTagIds.length > 0
              ? 'bg-blue-50 border-blue-300 text-blue-700'
              : 'bg-white border-gray-300 text-gray-700'
          } hover:bg-gray-50`}
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z" />
          </svg>
          标签筛选
          {selectedTagIds.length > 0 && (
            <span className="ml-1 px-1.5 py-0.5 text-xs bg-blue-100 rounded-full">
              {selectedTagIds.length}
            </span>
          )}
        </button>

        {selectedTagIds.length > 0 && (
          <button
            onClick={clearFilter}
            className="text-xs text-gray-500 hover:text-gray-700"
          >
            清除
          </button>
        )}
      </div>

      {/* 已选标签显示 */}
      {selectedTags.length > 0 && (
        <div className="flex flex-wrap gap-1 mt-2">
          {selectedTags.map((tag) => (
            <span
              key={tag.id}
              className="inline-flex items-center gap-1 px-2 py-0.5 text-xs rounded-full"
              style={{
                backgroundColor: tag.color ? `${tag.color}20` : '#f3f4f6',
                color: tag.color || '#374151',
              }}
            >
              <span
                className="w-1.5 h-1.5 rounded-full"
                style={{ backgroundColor: tag.color || '#6b7280' }}
              />
              {tag.name}
              <button
                onClick={() => toggleTag(tag.id)}
                className="ml-0.5 hover:opacity-70"
              >
                ×
              </button>
            </span>
          ))}
        </div>
      )}

      {/* 标签选择下拉框 */}
      {isOpen && (
        <div className="absolute z-10 mt-1 w-56 bg-white border rounded-lg shadow-lg">
          <div className="p-2">
            <div className="text-xs text-gray-500 mb-2">选择标签筛选内容</div>
            <div className="space-y-1 max-h-48 overflow-y-auto">
              {tags.map((tag) => {
                const isSelected = selectedTagIds.includes(tag.id);
                return (
                  <div
                    key={tag.id}
                    className={`flex items-center gap-2 px-2 py-1.5 cursor-pointer rounded hover:bg-gray-50 ${
                      isSelected ? 'bg-blue-50' : ''
                    }`}
                    onClick={() => toggleTag(tag.id)}
                  >
                    <div
                      className={`w-4 h-4 border rounded flex items-center justify-center ${
                        isSelected ? 'bg-blue-500 border-blue-500' : 'border-gray-300'
                      }`}
                    >
                      {isSelected && (
                        <svg className="w-3 h-3 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                        </svg>
                      )}
                    </div>
                    <div
                      className="w-2.5 h-2.5 rounded-full"
                      style={{ backgroundColor: tag.color || '#6b7280' }}
                    />
                    <span className="text-sm flex-1">{tag.name}</span>
                    <span className="text-xs text-gray-400">{tag.usage_count}</span>
                  </div>
                );
              })}
              {tags.length === 0 && (
                <div className="text-center text-gray-500 text-sm py-2">
                  暂无标签
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default TagFilter;
