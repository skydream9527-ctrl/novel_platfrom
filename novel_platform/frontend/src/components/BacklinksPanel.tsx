import React, { useState, useEffect } from 'react';
import { Backlink, getBacklinks } from '../api/links';

interface BacklinksPanelProps {
  taskId: number;
  targetType: string; // chapter / note / character / source
  targetId: number;
  onLinkClick?: (type: string, id: number) => void;
}

export const BacklinksPanel: React.FC<BacklinksPanelProps> = ({
  taskId,
  targetType,
  targetId,
  onLinkClick,
}) => {
  const [backlinks, setBacklinks] = useState<Backlink[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  // 加载反向链接
  useEffect(() => {
    loadBacklinks();
  }, [taskId, targetType, targetId]);

  const loadBacklinks = async () => {
    setIsLoading(true);
    try {
      const data = await getBacklinks(targetType, targetId, taskId);
      setBacklinks(data);
    } catch (error) {
      console.error('Failed to load backlinks:', error);
    } finally {
      setIsLoading(false);
    }
  };

  // 获取内容类型图标
  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'chapter':
        return '📄';
      case 'note':
        return '📝';
      case 'character':
        return '👤';
      case 'source':
        return '📎';
      default:
        return '📌';
    }
  };

  // 获取内容类型名称
  const getTypeName = (type: string) => {
    switch (type) {
      case 'chapter':
        return '章节';
      case 'note':
        return '笔记';
      case 'character':
        return '角色';
      case 'source':
        return '素材';
      default:
        return type;
    }
  };

  if (isLoading) {
    return (
      <div className="backlinks-panel p-4">
        <div className="text-center text-gray-500">加载中...</div>
      </div>
    );
  }

  return (
    <div className="backlinks-panel">
      <h3 className="text-sm font-semibold mb-3 flex items-center gap-2">
        <svg className="w-4 h-4 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
        </svg>
        被引用于 ({backlinks.length})
      </h3>

      {backlinks.length === 0 ? (
        <div className="text-center text-gray-500 text-sm py-4">
          暂无内容引用此项
        </div>
      ) : (
        <div className="space-y-2">
          {backlinks.map((backlink) => (
            <div
              key={backlink.link_id}
              className="flex items-start gap-2 p-2 bg-gray-50 rounded-lg cursor-pointer hover:bg-gray-100"
              onClick={() => onLinkClick?.(backlink.source_type, backlink.source_id)}
            >
              <span className="text-lg">{getTypeIcon(backlink.source_type)}</span>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <span className="text-sm font-medium truncate">
                    {backlink.source_title}
                  </span>
                  <span className="text-xs text-gray-500 px-1 py-0.5 bg-gray-200 rounded">
                    {getTypeName(backlink.source_type)}
                  </span>
                </div>
                {backlink.anchor_text && (
                  <div className="text-xs text-gray-500 mt-1 truncate">
                    "{backlink.anchor_text}"
                  </div>
                )}
                <div className="text-xs text-gray-400 mt-1">
                  {new Date(backlink.created_at).toLocaleDateString()}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* 刷新按钮 */}
      <button
        onClick={loadBacklinks}
        className="mt-3 w-full text-xs text-gray-500 hover:text-gray-700 py-1"
      >
        刷新
      </button>
    </div>
  );
};

export default BacklinksPanel;
