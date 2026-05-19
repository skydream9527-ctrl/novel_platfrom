import React, { useState, useEffect } from 'react';
import {
  Comment,
  CommentStats,
  getChapterComments,
  createComment,
  updateComment,
  deleteComment,
  resolveComment,
  getCommentStats,
} from '../api/comments';

interface CommentPanelProps {
  taskId: number;
  chapterId: number;
  onCommentClick?: (comment: Comment) => void;
}

const COMMENT_TYPE_ICONS: Record<string, string> = {
  general: '💬',
  suggestion: '💡',
  issue: '⚠️',
  praise: '👍',
  ai: '🤖',
};

const COMMENT_TYPE_LABELS: Record<string, string> = {
  general: '通用评论',
  suggestion: '修改建议',
  issue: '问题标记',
  praise: '好的表达',
  ai: 'AI 评论',
};

export const CommentPanel: React.FC<CommentPanelProps> = ({
  taskId,
  chapterId,
  onCommentClick,
}) => {
  const [comments, setComments] = useState<Comment[]>([]);
  const [stats, setStats] = useState<CommentStats | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isCreating, setIsCreating] = useState(false);
  const [editingComment, setEditingComment] = useState<Comment | null>(null);
  const [filterType, setFilterType] = useState<string>('');
  const [filterStatus, setFilterStatus] = useState<string>('');

  // 表单状态
  const [formData, setFormData] = useState({
    content: '',
    comment_type: 'general',
    selection_start: 0,
    selection_end: 0,
    selected_text: '',
  });

  // 加载评论
  useEffect(() => {
    loadComments();
  }, [chapterId, filterType, filterStatus]);

  const loadComments = async () => {
    setIsLoading(true);
    try {
      const [commentsData, statsData] = await Promise.all([
        getChapterComments(chapterId, filterStatus || undefined, filterType || undefined),
        getCommentStats(chapterId),
      ]);
      setComments(commentsData);
      setStats(statsData);
    } catch (error) {
      console.error('Failed to load comments:', error);
    } finally {
      setIsLoading(false);
    }
  };

  // 创建评论
  const handleCreate = async () => {
    if (!formData.content.trim()) return;

    try {
      await createComment({
        task_id: taskId,
        chapter_id: chapterId,
        content: formData.content,
        comment_type: formData.comment_type,
        selection_start: formData.selection_start || undefined,
        selection_end: formData.selection_end || undefined,
        selected_text: formData.selected_text || undefined,
      });
      setIsCreating(false);
      resetForm();
      loadComments();
    } catch (error) {
      console.error('Failed to create comment:', error);
    }
  };

  // 更新评论
  const handleUpdate = async () => {
    if (!editingComment || !formData.content.trim()) return;

    try {
      await updateComment(editingComment.id, {
        content: formData.content,
        comment_type: formData.comment_type,
      });
      setEditingComment(null);
      resetForm();
      loadComments();
    } catch (error) {
      console.error('Failed to update comment:', error);
    }
  };

  // 删除评论
  const handleDelete = async (commentId: number) => {
    if (!confirm('确定要删除此评论吗？')) return;

    try {
      await deleteComment(commentId);
      loadComments();
    } catch (error) {
      console.error('Failed to delete comment:', error);
    }
  };

  // 标记为已解决
  const handleResolve = async (commentId: number) => {
    try {
      await resolveComment(commentId);
      loadComments();
    } catch (error) {
      console.error('Failed to resolve comment:', error);
    }
  };

  // 重置表单
  const resetForm = () => {
    setFormData({
      content: '',
      comment_type: 'general',
      selection_start: 0,
      selection_end: 0,
      selected_text: '',
    });
  };

  // 开始编辑
  const startEditing = (comment: Comment) => {
    setEditingComment(comment);
    setFormData({
      content: comment.content,
      comment_type: comment.comment_type,
      selection_start: comment.selection_start || 0,
      selection_end: comment.selection_end || 0,
      selected_text: comment.selected_text || '',
    });
    setIsCreating(false);
  };

  // 取消编辑
  const cancelEditing = () => {
    setEditingComment(null);
    setIsCreating(false);
    resetForm();
  };

  // 渲染评论
  const renderComment = (comment: Comment, isReply: boolean = false) => (
    <div
      key={comment.id}
      className={`p-3 rounded-lg ${isReply ? 'ml-6 bg-gray-50' : 'bg-white border'}`}
    >
      <div className="flex items-start justify-between mb-2">
        <div className="flex items-center gap-2">
          <span className="text-sm">
            {COMMENT_TYPE_ICONS[comment.comment_type] || '💬'}
          </span>
          <span className="text-sm font-medium">
            {comment.author?.name || '未知用户'}
          </span>
          <span className="text-xs text-gray-400">
            {new Date(comment.created_at).toLocaleString()}
          </span>
          {comment.status === 'resolved' && (
            <span className="px-1.5 py-0.5 text-xs bg-green-100 text-green-800 rounded">
              已解决
            </span>
          )}
        </div>
        <div className="flex gap-1">
          {comment.status === 'open' && (
            <button
              onClick={() => handleResolve(comment.id)}
              className="p-1 text-gray-400 hover:text-green-600"
              title="标记为已解决"
            >
              ✓
            </button>
          )}
          <button
            onClick={() => startEditing(comment)}
            className="p-1 text-gray-400 hover:text-gray-600"
            title="编辑"
          >
            ✏️
          </button>
          <button
            onClick={() => handleDelete(comment.id)}
            className="p-1 text-gray-400 hover:text-red-600"
            title="删除"
          >
            🗑️
          </button>
        </div>
      </div>

      {/* 选中的文本 */}
      {comment.selected_text && (
        <div className="mb-2 p-2 bg-yellow-50 border-l-2 border-yellow-400 text-sm text-gray-600">
          "{comment.selected_text}"
        </div>
      )}

      {/* 评论内容 */}
      <div className="text-sm text-gray-700">{comment.content}</div>

      {/* 回复 */}
      {comment.replies && comment.replies.length > 0 && (
        <div className="mt-3 space-y-2">
          {comment.replies.map((reply) => renderComment(reply, true))}
        </div>
      )}
    </div>
  );

  if (isLoading) {
    return (
      <div className="comment-panel p-4">
        <div className="text-center text-gray-500">加载中...</div>
      </div>
    );
  }

  return (
    <div className="comment-panel">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold">评论</h3>
        <button
          onClick={() => setIsCreating(true)}
          className="px-3 py-1 text-sm bg-blue-500 text-white rounded hover:bg-blue-600"
        >
          + 添加评论
        </button>
      </div>

      {/* 统计信息 */}
      {stats && (
        <div className="flex gap-4 mb-4 text-sm">
          <span>总评论: {stats.total}</span>
          <span>未解决: {stats.open}</span>
          <span>已解决: {stats.resolved}</span>
        </div>
      )}

      {/* 筛选器 */}
      <div className="flex gap-2 mb-4">
        <select
          value={filterType}
          onChange={(e) => setFilterType(e.target.value)}
          className="px-2 py-1 border rounded text-sm"
        >
          <option value="">全部类型</option>
          {Object.entries(COMMENT_TYPE_LABELS).map(([value, label]) => (
            <option key={value} value={value}>
              {label}
            </option>
          ))}
        </select>
        <select
          value={filterStatus}
          onChange={(e) => setFilterStatus(e.target.value)}
          className="px-2 py-1 border rounded text-sm"
        >
          <option value="">全部状态</option>
          <option value="open">未解决</option>
          <option value="resolved">已解决</option>
        </select>
      </div>

      {/* 创建/编辑表单 */}
      {(isCreating || editingComment) && (
        <div className="mb-4 p-3 bg-gray-50 rounded-lg">
          <h4 className="text-sm font-medium mb-2">
            {editingComment ? '编辑评论' : '添加评论'}
          </h4>
          <div className="space-y-3">
            <div>
              <label className="block text-xs text-gray-500 mb-1">评论类型</label>
              <select
                value={formData.comment_type}
                onChange={(e) =>
                  setFormData((prev) => ({ ...prev, comment_type: e.target.value }))
                }
                className="w-full px-2 py-1 border rounded text-sm"
              >
                {Object.entries(COMMENT_TYPE_LABELS).map(([value, label]) => (
                  <option key={value} value={value}>
                    {COMMENT_TYPE_ICONS[value]} {label}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-xs text-gray-500 mb-1">评论内容</label>
              <textarea
                value={formData.content}
                onChange={(e) =>
                  setFormData((prev) => ({ ...prev, content: e.target.value }))
                }
                className="w-full px-2 py-1 border rounded text-sm resize-none"
                rows={3}
                placeholder="输入评论内容..."
              />
            </div>
            <div className="flex gap-2">
              <button
                onClick={editingComment ? handleUpdate : handleCreate}
                className="px-3 py-1 text-sm bg-blue-500 text-white rounded hover:bg-blue-600"
              >
                {editingComment ? '保存' : '发布'}
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

      {/* 评论列表 */}
      <div className="space-y-3 max-h-[500px] overflow-y-auto">
        {comments.length === 0 ? (
          <div className="text-center text-gray-500 py-8">
            暂无评论
          </div>
        ) : (
          comments.map((comment) => renderComment(comment))
        )}
      </div>
    </div>
  );
};

export default CommentPanel;
