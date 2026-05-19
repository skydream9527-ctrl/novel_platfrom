import React, { useState, useEffect } from 'react';
import { Tag, getTagsByTask, getContentTags, assignTag, unassignTag } from '../api/tags';

interface TagSelectorProps {
  taskId: number;
  contentType: string; // chapter / note / source
  contentId: number;
  onChange?: () => void;
}

export const TagSelector: React.FC<TagSelectorProps> = ({
  taskId,
  contentType,
  contentId,
  onChange,
}) => {
  const [allTags, setAllTags] = useState<Tag[]>([]);
  const [contentTags, setContentTags] = useState<Tag[]>([]);
  const [isOpen, setIsOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');

  // 加载所有标签和内容标签
  useEffect(() => {
    loadData();
  }, [taskId, contentType, contentId]);

  const loadData = async () => {
    try {
      const [tags, cTags] = await Promise.all([
        getTagsByTask(taskId),
        getContentTags(contentType, contentId),
      ]);
      setAllTags(tags);
      setContentTags(cTags);
    } catch (error) {
      console.error('Failed to load tags:', error);
    }
  };

  // 切换标签关联
  const toggleTag = async (tag: Tag) => {
    const isAssigned = contentTags.some((t) => t.id === tag.id);

    try {
      if (isAssigned) {
        await unassignTag({
          tag_id: tag.id,
          content_type: contentType,
          content_id: contentId,
        });
      } else {
        await assignTag({
          tag_id: tag.id,
          content_type: contentType,
          content_id: contentId,
        });
      }
      loadData();
      onChange?.();
    } catch (error) {
      console.error('Failed to toggle tag:', error);
    }
  };

  // 过滤标签
  const filteredTags = allTags.filter((tag) =>
    tag.name.toLowerCase().includes(searchQuery.toLowerCase())
  );

  // 移除标签
  const removeTag = async (tag: Tag) => {
    try {
      await unassignTag({
        tag_id: tag.id,
        content_type: contentType,
        content_id: contentId,
      });
      loadData();
      onChange?.();
    } catch (error) {
      console.error('Failed to remove tag:', error);
    }
  };

  return (
    <div className="tag-selector">
      {/* 已选标签显示 */}
      <div className="flex flex-wrap gap-1 mb-2">
        {contentTags.map((tag) => (
          <span
            key={tag.id}
            className="inline-flex items-center gap-1 px-2 py-1 text-xs rounded-full"
            style={{
              backgroundColor: tag.color ? `${tag.color}20` : '#f3f4f6',
              color: tag.color || '#374151',
            }}
          >
            <span
              className="w-2 h-2 rounded-full"
              style={{ backgroundColor: tag.color || '#6b7280' }}
            />
            {tag.name}
            <button
              onClick={() => removeTag(tag)}
              className="ml-1 hover:opacity-70"
            >
              ×
            </button>
          </span>
        ))}
        <button
          onClick={() => setIsOpen(!isOpen)}
          className="inline-flex items-center gap-1 px-2 py-1 text-xs text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-full"
        >
          + 添加标签
        </button>
      </div>

      {/* 标签选择下拉框 */}
      {isOpen && (
        <div className="absolute z-10 mt-1 w-64 bg-white border rounded-lg shadow-lg">
          <div className="p-2">
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full px-2 py-1 border rounded text-sm"
              placeholder="搜索标签..."
              autoFocus
            />
          </div>
          <div className="max-h-48 overflow-y-auto">
            {filteredTags.map((tag) => {
              const isAssigned = contentTags.some((t) => t.id === tag.id);
              return (
                <div
                  key={tag.id}
                  className={`flex items-center gap-2 px-3 py-2 cursor-pointer hover:bg-gray-50 ${
                    isAssigned ? 'bg-blue-50' : ''
                  }`}
                  onClick={() => toggleTag(tag)}
                >
                  <div
                    className="w-3 h-3 rounded-full"
                    style={{ backgroundColor: tag.color || '#6b7280' }}
                  />
                  <span className="text-sm flex-1">{tag.name}</span>
                  {isAssigned && (
                    <svg className="w-4 h-4 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                  )}
                </div>
              );
            })}
            {filteredTags.length === 0 && (
              <div className="px-3 py-2 text-sm text-gray-500">
                {searchQuery ? '未找到匹配的标签' : '暂无标签'}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default TagSelector;
