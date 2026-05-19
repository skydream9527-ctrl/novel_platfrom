import React, { useState, useEffect, useRef } from 'react';
import {
  TimelineEvent,
  TimelineConflict,
  getTimeline,
  createTimelineEvent,
  updateTimelineEvent,
  deleteTimelineEvent,
  moveTimelineEvent,
  generateFromChapters,
  checkConflicts,
} from '../api/timeline';

interface TimelineEditorProps {
  taskId: number;
  chapters?: Array<{ id: number; title: string }>;
  characters?: Array<{ id: number; name: string }>;
  onEventClick?: (event: TimelineEvent) => void;
  onChapterClick?: (chapterId: number) => void;
}

const EVENT_TYPE_COLORS: Record<string, string> = {
  scene: '#3b82f6',
  plot: '#22c55e',
  background: '#6b7280',
  flashback: '#f97316',
};

const EVENT_TYPE_LABELS: Record<string, string> = {
  scene: '主线场景',
  plot: '情节节点',
  background: '背景事件',
  flashback: '回忆/闪回',
};

export const TimelineEditor: React.FC<TimelineEditorProps> = ({
  taskId,
  chapters = [],
  characters = [],
  onEventClick,
  onChapterClick,
}) => {
  const [events, setEvents] = useState<TimelineEvent[]>([]);
  const [selectedEvent, setSelectedEvent] = useState<TimelineEvent | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isEditing, setIsEditing] = useState(false);
  const [isCreating, setIsCreating] = useState(false);
  const [conflicts, setConflicts] = useState<TimelineConflict[]>([]);
  const [showConflicts, setShowConflicts] = useState(false);
  const timelineRef = useRef<HTMLDivElement>(null);

  // 表单状态
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    event_type: 'scene',
    story_date: '',
    story_date_order: 0,
    duration: '',
    location: '',
    characters: [] as number[],
    is_milestone: false,
    chapter_id: null as number | null,
  });

  // 加载时间线
  useEffect(() => {
    loadTimeline();
  }, [taskId]);

  const loadTimeline = async () => {
    setIsLoading(true);
    try {
      const data = await getTimeline(taskId);
      setEvents(data);
    } catch (error) {
      console.error('Failed to load timeline:', error);
    } finally {
      setIsLoading(false);
    }
  };

  // 创建事件
  const handleCreate = async () => {
    if (!formData.title.trim()) return;

    try {
      await createTimelineEvent({
        task_id: taskId,
        ...formData,
        chapter_id: formData.chapter_id ?? undefined,
      });
      setIsCreating(false);
      resetForm();
      loadTimeline();
    } catch (error) {
      console.error('Failed to create event:', error);
    }
  };

  // 更新事件
  const handleUpdate = async () => {
    if (!selectedEvent || !formData.title.trim()) return;

    try {
      await updateTimelineEvent(selectedEvent.id, {
        ...formData,
        chapter_id: formData.chapter_id ?? undefined,
      });
      setIsEditing(false);
      resetForm();
      loadTimeline();
    } catch (error) {
      console.error('Failed to update event:', error);
    }
  };

  // 删除事件
  const handleDelete = async (eventId: number) => {
    if (!confirm('确定要删除此事件吗？')) return;

    try {
      await deleteTimelineEvent(eventId);
      if (selectedEvent?.id === eventId) {
        setSelectedEvent(null);
      }
      loadTimeline();
    } catch (error) {
      console.error('Failed to delete event:', error);
    }
  };

  // 从章节生成
  const handleGenerateFromChapters = async () => {
    try {
      const result = await generateFromChapters(taskId);
      alert(`已生成 ${result.created} 个事件`);
      loadTimeline();
    } catch (error) {
      console.error('Failed to generate from chapters:', error);
    }
  };

  // 检查冲突
  const handleCheckConflicts = async () => {
    try {
      const result = await checkConflicts(taskId);
      setConflicts(result.conflicts);
      setShowConflicts(true);
    } catch (error) {
      console.error('Failed to check conflicts:', error);
    }
  };

  // 重置表单
  const resetForm = () => {
    setFormData({
      title: '',
      description: '',
      event_type: 'scene',
      story_date: '',
      story_date_order: 0,
      duration: '',
      location: '',
      characters: [],
      is_milestone: false,
      chapter_id: null,
    });
  };

  // 开始编辑
  const startEditing = (event: TimelineEvent) => {
    setSelectedEvent(event);
    setFormData({
      title: event.title,
      description: event.description,
      event_type: event.event_type,
      story_date: event.story_date,
      story_date_order: event.story_date_order,
      duration: event.duration,
      location: event.location,
      characters: event.characters.map((c) => c.id),
      is_milestone: event.is_milestone,
      chapter_id: event.chapter_id,
    });
    setIsEditing(true);
    setIsCreating(false);
  };

  // 开始创建
  const startCreating = () => {
    resetForm();
    setFormData((prev) => ({
      ...prev,
      story_date_order: events.length,
    }));
    setIsCreating(true);
    setIsEditing(false);
  };

  // 取消编辑
  const cancelEditing = () => {
    setIsEditing(false);
    setIsCreating(false);
    resetForm();
  };

  // 切换角色选择
  const toggleCharacter = (characterId: number) => {
    setFormData((prev) => ({
      ...prev,
      characters: prev.characters.includes(characterId)
        ? prev.characters.filter((id) => id !== characterId)
        : [...prev.characters, characterId],
    }));
  };

  // 渲染时间线事件
  const renderEvent = (event: TimelineEvent, index: number) => {
    const isSelected = selectedEvent?.id === event.id;
    const color = EVENT_TYPE_COLORS[event.event_type] || '#6b7280';

    return (
      <div
        key={event.id}
        className={`relative flex items-start gap-4 p-4 cursor-pointer rounded-lg transition-all ${
          isSelected
            ? 'bg-blue-50 border-2 border-blue-300'
            : 'hover:bg-gray-50 border-2 border-transparent'
        }`}
        onClick={() => {
          setSelectedEvent(event);
          onEventClick?.(event);
        }}
      >
        {/* 时间线连接线 */}
        {index > 0 && (
          <div
            className="absolute left-6 top-0 w-0.5 h-4"
            style={{ backgroundColor: color }}
          />
        )}

        {/* 事件节点 */}
        <div
          className="relative z-10 w-12 h-12 rounded-full flex items-center justify-center text-white text-lg font-bold"
          style={{ backgroundColor: color }}
        >
          {event.is_milestone ? '⭐' : EVENT_TYPE_LABELS[event.event_type]?.[0] || '●'}
        </div>

        {/* 事件内容 */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <h4 className="text-sm font-semibold truncate">{event.title}</h4>
            {event.is_milestone && (
              <span className="px-1.5 py-0.5 text-xs bg-yellow-100 text-yellow-800 rounded">
                里程碑
              </span>
            )}
          </div>

          {event.description && (
            <p className="text-xs text-gray-500 mb-2 line-clamp-2">
              {event.description}
            </p>
          )}

          <div className="flex flex-wrap gap-2 text-xs text-gray-400">
            {event.story_date && (
              <span>📅 {event.story_date}</span>
            )}
            {event.location && (
              <span>📍 {event.location}</span>
            )}
            {event.duration && (
              <span>⏱️ {event.duration}
              </span>
            )}
            {event.chapter && (
              <span
                className="text-blue-500 cursor-pointer hover:underline"
                onClick={(e) => {
                  e.stopPropagation();
                  onChapterClick?.(event.chapter!.id);
                }}
              >
                📄 {event.chapter.title}
              </span>
            )}
          </div>

          {/* 角色列表 */}
          {event.characters.length > 0 && (
            <div className="flex flex-wrap gap-1 mt-2">
              {event.characters.map((char) => (
                <span
                  key={char.id}
                  className="px-1.5 py-0.5 text-xs bg-gray-100 rounded"
                >
                  👤 {char.name}
                </span>
              ))}
            </div>
          )}
        </div>

        {/* 操作按钮 */}
        <div className="flex gap-1 opacity-0 group-hover:opacity-100">
          <button
            onClick={(e) => {
              e.stopPropagation();
              startEditing(event);
            }}
            className="p-1 text-gray-400 hover:text-gray-600"
            title="编辑"
          >
            ✏️
          </button>
          <button
            onClick={(e) => {
              e.stopPropagation();
              handleDelete(event.id);
            }}
            className="p-1 text-gray-400 hover:text-red-600"
            title="删除"
          >
            🗑️
          </button>
        </div>
      </div>
    );
  };

  if (isLoading) {
    return (
      <div className="timeline-editor p-4">
        <div className="text-center text-gray-500">加载中...</div>
      </div>
    );
  }

  return (
    <div className="timeline-editor">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold">时间线</h3>
        <div className="flex gap-2">
          <button
            onClick={handleGenerateFromChapters}
            className="px-3 py-1 text-sm bg-gray-200 rounded hover:bg-gray-300"
          >
            从章节生成
          </button>
          <button
            onClick={handleCheckConflicts}
            className="px-3 py-1 text-sm bg-yellow-100 text-yellow-800 rounded hover:bg-yellow-200"
          >
            检查冲突
          </button>
          <button
            onClick={startCreating}
            className="px-3 py-1 text-sm bg-blue-500 text-white rounded hover:bg-blue-600"
          >
            + 添加事件
          </button>
        </div>
      </div>

      {/* 冲突提示 */}
      {showConflicts && conflicts.length > 0 && (
        <div className="mb-4 p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
          <div className="flex items-center justify-between mb-2">
            <h4 className="text-sm font-semibold text-yellow-800">
              发现 {conflicts.length} 个冲突
            </h4>
            <button
              onClick={() => setShowConflicts(false)}
              className="text-yellow-600 hover:text-yellow-800"
            >
              ✕
            </button>
          </div>
          <div className="space-y-2">
            {conflicts.map((conflict, index) => (
              <div key={index} className="text-xs text-yellow-700">
                ⚠️ {conflict.description}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 编辑/创建表单 */}
      {(isEditing || isCreating) && (
        <div className="mb-4 p-4 bg-gray-50 rounded-lg">
          <h4 className="text-sm font-medium mb-3">
            {isEditing ? '编辑事件' : '创建新事件'}
          </h4>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs text-gray-500 mb-1">标题 *</label>
              <input
                type="text"
                value={formData.title}
                onChange={(e) =>
                  setFormData((prev) => ({ ...prev, title: e.target.value }))
                }
                className="w-full px-2 py-1 border rounded text-sm"
                placeholder="事件标题"
              />
            </div>
            <div>
              <label className="block text-xs text-gray-500 mb-1">事件类型</label>
              <select
                value={formData.event_type}
                onChange={(e) =>
                  setFormData((prev) => ({ ...prev, event_type: e.target.value }))
                }
                className="w-full px-2 py-1 border rounded text-sm"
              >
                {Object.entries(EVENT_TYPE_LABELS).map(([value, label]) => (
                  <option key={value} value={value}>
                    {label}
                  </option>
                ))}
              </select>
            </div>
            <div className="col-span-2">
              <label className="block text-xs text-gray-500 mb-1">描述</label>
              <textarea
                value={formData.description}
                onChange={(e) =>
                  setFormData((prev) => ({ ...prev, description: e.target.value }))
                }
                className="w-full px-2 py-1 border rounded text-sm resize-none"
                rows={2}
                placeholder="事件描述"
              />
            </div>
            <div>
              <label className="block text-xs text-gray-500 mb-1">故事日期</label>
              <input
                type="text"
                value={formData.story_date}
                onChange={(e) =>
                  setFormData((prev) => ({ ...prev, story_date: e.target.value }))
                }
                className="w-full px-2 py-1 border rounded text-sm"
                placeholder="如：第三天下午"
              />
            </div>
            <div>
              <label className="block text-xs text-gray-500 mb-1">地点</label>
              <input
                type="text"
                value={formData.location}
                onChange={(e) =>
                  setFormData((prev) => ({ ...prev, location: e.target.value }))
                }
                className="w-full px-2 py-1 border rounded text-sm"
                placeholder="事件地点"
              />
            </div>
            <div>
              <label className="block text-xs text-gray-500 mb-1">持续时长</label>
              <input
                type="text"
                value={formData.duration}
                onChange={(e) =>
                  setFormData((prev) => ({ ...prev, duration: e.target.value }))
                }
                className="w-full px-2 py-1 border rounded text-sm"
                placeholder="如：2小时"
              />
            </div>
            <div>
              <label className="block text-xs text-gray-500 mb-1">关联章节</label>
              <select
                value={formData.chapter_id || ''}
                onChange={(e) =>
                  setFormData((prev) => ({
                    ...prev,
                    chapter_id: e.target.value ? parseInt(e.target.value) : null,
                  }))
                }
                className="w-full px-2 py-1 border rounded text-sm"
              >
                <option value="">无</option>
                {chapters.map((chapter) => (
                  <option key={chapter.id} value={chapter.id}>
                    {chapter.title}
                  </option>
                ))}
              </select>
            </div>
            <div className="col-span-2">
              <label className="block text-xs text-gray-500 mb-1">出场角色</label>
              <div className="flex flex-wrap gap-2">
                {characters.map((char) => (
                  <label
                    key={char.id}
                    className={`flex items-center gap-1 px-2 py-1 text-xs rounded cursor-pointer ${
                      formData.characters.includes(char.id)
                        ? 'bg-blue-100 text-blue-800'
                        : 'bg-gray-100 text-gray-600'
                    }`}
                  >
                    <input
                      type="checkbox"
                      checked={formData.characters.includes(char.id)}
                      onChange={() => toggleCharacter(char.id)}
                      className="rounded"
                    />
                    {char.name}
                  </label>
                ))}
              </div>
            </div>
            <div className="col-span-2">
              <label className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={formData.is_milestone}
                  onChange={(e) =>
                    setFormData((prev) => ({
                      ...prev,
                      is_milestone: e.target.checked,
                    }))
                  }
                  className="rounded"
                />
                <span className="text-sm">标记为里程碑</span>
              </label>
            </div>
          </div>
          <div className="flex gap-2 mt-3">
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
      )}

      {/* 时间线 */}
      <div ref={timelineRef} className="space-y-2 max-h-[600px] overflow-y-auto">
        {events.length === 0 ? (
          <div className="text-center text-gray-500 py-8">
            暂无时间线事件，点击上方按钮创建
          </div>
        ) : (
          events.map((event, index) => renderEvent(event, index))
        )}
      </div>

      {/* 图例 */}
      <div className="flex gap-4 mt-4 text-xs">
        {Object.entries(EVENT_TYPE_COLORS).map(([type, color]) => (
          <div key={type} className="flex items-center gap-1">
            <div
              className="w-3 h-3 rounded-full"
              style={{ backgroundColor: color }}
            />
            <span>{EVENT_TYPE_LABELS[type]}</span>
          </div>
        ))}
      </div>
    </div>
  );
};

export default TimelineEditor;
