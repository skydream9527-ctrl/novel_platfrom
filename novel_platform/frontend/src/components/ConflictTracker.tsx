import React, { useState, useEffect } from 'react';
import {
  Conflict,
  Foreshadowing,
  getConflicts,
  createConflict,
  updateConflict,
  deleteConflict,
  getUnresolvedConflicts,
  getForeshadowing,
  createForeshadowing,
  updateForeshadowing,
  deleteForeshadowing,
  getUnresolvedForeshadowing,
} from '../api/conflicts';

interface ConflictTrackerProps {
  taskId: number;
  chapters?: Array<{ id: number; title: string }>;
  characters?: Array<{ id: number; name: string }>;
}

const CONFLICT_TYPE_LABELS: Record<string, string> = {
  external: '外部冲突',
  internal: '内部冲突',
  interpersonal: '人际关系冲突',
};

const CONFLICT_STATUS_LABELS: Record<string, string> = {
  introduced: '引入',
  developing: '发展',
  climax: '高潮',
  resolved: '已解决',
};

const CONFLICT_STATUS_COLORS: Record<string, string> = {
  introduced: 'bg-blue-100 text-blue-800',
  developing: 'bg-yellow-100 text-yellow-800',
  climax: 'bg-red-100 text-red-800',
  resolved: 'bg-green-100 text-green-800',
};

const FORESHADOWING_TYPE_LABELS: Record<string, string> = {
  plot: '情节伏笔',
  character: '角色伏笔',
  world: '世界观伏笔',
  item: '物品伏笔',
};

const FORESHADOWING_STATUS_LABELS: Record<string, string> = {
  planted: '埋设',
  hinted: '暗示',
  revealed: '揭示',
  resolved: '已回收',
};

const FORESHADOWING_STATUS_COLORS: Record<string, string> = {
  planted: 'bg-blue-100 text-blue-800',
  hinted: 'bg-yellow-100 text-yellow-800',
  revealed: 'bg-orange-100 text-orange-800',
  resolved: 'bg-green-100 text-green-800',
};

export const ConflictTracker: React.FC<ConflictTrackerProps> = ({
  taskId,
  chapters = [],
  characters = [],
}) => {
  const [activeTab, setActiveTab] = useState<'conflicts' | 'foreshadowing'>('conflicts');
  const [conflicts, setConflicts] = useState<Conflict[]>([]);
  const [foreshadowing, setForeshadowing] = useState<Foreshadowing[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isEditingConflict, setIsEditingConflict] = useState(false);
  const [isEditingForeshadowing, setIsEditingForeshadowing] = useState(false);
  const [selectedConflict, setSelectedConflict] = useState<Conflict | null>(null);
  const [selectedForeshadowing, setSelectedForeshadowing] = useState<Foreshadowing | null>(null);

  // 冲突表单
  const [conflictForm, setConflictForm] = useState({
    title: '',
    description: '',
    conflict_type: 'external',
    priority: 'medium',
    introduced_chapter_id: null as number | null,
    related_characters: [] as number[],
  });

  // 伏笔表单
  const [foreshadowingForm, setForeshadowingForm] = useState({
    title: '',
    description: '',
    foreshadowing_type: 'plot',
    planted_chapter_id: null as number | null,
    hints: [] as Array<{ chapter_id: number; description: string }>,
  });

  // 加载数据
  useEffect(() => {
    loadData();
  }, [taskId]);

  const loadData = async () => {
    setIsLoading(true);
    try {
      const [conflictsData, foreshadowingData] = await Promise.all([
        getConflicts(taskId),
        getForeshadowing(taskId),
      ]);
      setConflicts(conflictsData);
      setForeshadowing(foreshadowingData);
    } catch (error) {
      console.error('Failed to load data:', error);
    } finally {
      setIsLoading(false);
    }
  };

  // 保存冲突
  const handleSaveConflict = async () => {
    if (!conflictForm.title.trim()) return;

    const conflictData = {
      ...conflictForm,
      introduced_chapter_id: conflictForm.introduced_chapter_id ?? undefined,
    };

    try {
      if (isEditingConflict && selectedConflict) {
        await updateConflict(selectedConflict.id, conflictData);
      } else {
        await createConflict({
          task_id: taskId,
          ...conflictData,
        });
      }
      setIsEditingConflict(false);
      resetConflictForm();
      loadData();
    } catch (error) {
      console.error('Failed to save conflict:', error);
    }
  };

  // 删除冲突
  const handleDeleteConflict = async (conflictId: number) => {
    if (!confirm('确定要删除此冲突吗？')) return;

    try {
      await deleteConflict(conflictId);
      if (selectedConflict?.id === conflictId) {
        setSelectedConflict(null);
      }
      loadData();
    } catch (error) {
      console.error('Failed to delete conflict:', error);
    }
  };

  // 更新冲突状态
  const handleUpdateConflictStatus = async (conflictId: number, status: string) => {
    try {
      await updateConflict(conflictId, { status });
      loadData();
    } catch (error) {
      console.error('Failed to update conflict status:', error);
    }
  };

  // 保存伏笔
  const handleSaveForeshadowing = async () => {
    if (!foreshadowingForm.title.trim()) return;

    const fsData = {
      ...foreshadowingForm,
      planted_chapter_id: foreshadowingForm.planted_chapter_id ?? undefined,
    };

    try {
      if (isEditingForeshadowing && selectedForeshadowing) {
        await updateForeshadowing(selectedForeshadowing.id, fsData);
      } else {
        await createForeshadowing({
          task_id: taskId,
          ...fsData,
        });
      }
      setIsEditingForeshadowing(false);
      resetForeshadowingForm();
      loadData();
    } catch (error) {
      console.error('Failed to save foreshadowing:', error);
    }
  };

  // 删除伏笔
  const handleDeleteForeshadowing = async (fsId: number) => {
    if (!confirm('确定要删除此伏笔吗？')) return;

    try {
      await deleteForeshadowing(fsId);
      if (selectedForeshadowing?.id === fsId) {
        setSelectedForeshadowing(null);
      }
      loadData();
    } catch (error) {
      console.error('Failed to delete foreshadowing:', error);
    }
  };

  // 更新伏笔状态
  const handleUpdateForeshadowingStatus = async (fsId: number, status: string) => {
    try {
      await updateForeshadowing(fsId, { status });
      loadData();
    } catch (error) {
      console.error('Failed to update foreshadowing status:', error);
    }
  };

  // 重置表单
  const resetConflictForm = () => {
    setConflictForm({
      title: '',
      description: '',
      conflict_type: 'external',
      priority: 'medium',
      introduced_chapter_id: null,
      related_characters: [],
    });
  };

  const resetForeshadowingForm = () => {
    setForeshadowingForm({
      title: '',
      description: '',
      foreshadowing_type: 'plot',
      planted_chapter_id: null,
      hints: [],
    });
  };

  // 开始编辑冲突
  const startEditingConflict = (conflict: Conflict) => {
    setSelectedConflict(conflict);
    setConflictForm({
      title: conflict.title,
      description: conflict.description,
      conflict_type: conflict.conflict_type,
      priority: conflict.priority,
      introduced_chapter_id: conflict.introduced_chapter?.id || null,
      related_characters: conflict.characters.map((c) => c.id),
    });
    setIsEditingConflict(true);
  };

  // 开始编辑伏笔
  const startEditingForeshadowing = (fs: Foreshadowing) => {
    setSelectedForeshadowing(fs);
    setForeshadowingForm({
      title: fs.title,
      description: fs.description,
      foreshadowing_type: fs.foreshadowing_type,
      planted_chapter_id: fs.planted_chapter?.id || null,
      hints: fs.hints,
    });
    setIsEditingForeshadowing(true);
  };

  // 取消编辑
  const cancelEditing = () => {
    setIsEditingConflict(false);
    setIsEditingForeshadowing(false);
    resetConflictForm();
    resetForeshadowingForm();
  };

  if (isLoading) {
    return (
      <div className="conflict-tracker p-4">
        <div className="text-center text-gray-500">加载中...</div>
      </div>
    );
  }

  return (
    <div className="conflict-tracker">
      <div className="flex items-center justify-between mb-4">
        <div className="flex gap-4">
          <button
            className={`px-3 py-1 text-sm rounded ${
              activeTab === 'conflicts' ? 'bg-blue-500 text-white' : 'bg-gray-200'
            }`}
            onClick={() => setActiveTab('conflicts')}
          >
            冲突追踪
          </button>
          <button
            className={`px-3 py-1 text-sm rounded ${
              activeTab === 'foreshadowing' ? 'bg-blue-500 text-white' : 'bg-gray-200'
            }`}
            onClick={() => setActiveTab('foreshadowing')}
          >
            伏笔追踪
          </button>
        </div>
      </div>

      {/* 冲突追踪 */}
      {activeTab === 'conflicts' && (
        <div>
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold">冲突追踪</h3>
            <button
              onClick={() => {
                resetConflictForm();
                setIsEditingConflict(true);
              }}
              className="px-3 py-1 text-sm bg-blue-500 text-white rounded hover:bg-blue-600"
            >
              + 添加冲突
            </button>
          </div>

          {/* 冲突表单 */}
          {isEditingConflict && (
            <div className="mb-4 p-3 bg-gray-50 rounded-lg">
              <h4 className="text-sm font-medium mb-2">
                {selectedConflict ? '编辑冲突' : '添加冲突'}
              </h4>
              <div className="space-y-3">
                <div>
                  <label className="block text-xs text-gray-500 mb-1">标题</label>
                  <input
                    type="text"
                    value={conflictForm.title}
                    onChange={(e) =>
                      setConflictForm((prev) => ({ ...prev, title: e.target.value }))
                    }
                    className="w-full px-2 py-1 border rounded text-sm"
                  />
                </div>
                <div>
                  <label className="block text-xs text-gray-500 mb-1">描述</label>
                  <textarea
                    value={conflictForm.description}
                    onChange={(e) =>
                      setConflictForm((prev) => ({ ...prev, description: e.target.value }))
                    }
                    className="w-full px-2 py-1 border rounded text-sm resize-none"
                    rows={2}
                  />
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-xs text-gray-500 mb-1">冲突类型</label>
                    <select
                      value={conflictForm.conflict_type}
                      onChange={(e) =>
                        setConflictForm((prev) => ({ ...prev, conflict_type: e.target.value }))
                      }
                      className="w-full px-2 py-1 border rounded text-sm"
                    >
                      {Object.entries(CONFLICT_TYPE_LABELS).map(([value, label]) => (
                        <option key={value} value={value}>{label}</option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label className="block text-xs text-gray-500 mb-1">优先级</label>
                    <select
                      value={conflictForm.priority}
                      onChange={(e) =>
                        setConflictForm((prev) => ({ ...prev, priority: e.target.value }))
                      }
                      className="w-full px-2 py-1 border rounded text-sm"
                    >
                      <option value="high">高</option>
                      <option value="medium">中</option>
                      <option value="low">低</option>
                    </select>
                  </div>
                </div>
                <div>
                  <label className="block text-xs text-gray-500 mb-1">相关角色</label>
                  <div className="flex flex-wrap gap-1">
                    {characters.map((char) => (
                      <label
                        key={char.id}
                        className={`flex items-center gap-1 px-2 py-1 text-xs rounded cursor-pointer ${
                          conflictForm.related_characters.includes(char.id)
                            ? 'bg-blue-100 text-blue-800'
                            : 'bg-gray-100 text-gray-600'
                        }`}
                      >
                        <input
                          type="checkbox"
                          checked={conflictForm.related_characters.includes(char.id)}
                          onChange={(e) => {
                            const newChars = e.target.checked
                              ? [...conflictForm.related_characters, char.id]
                              : conflictForm.related_characters.filter((id) => id !== char.id);
                            setConflictForm((prev) => ({ ...prev, related_characters: newChars }));
                          }}
                          className="rounded"
                        />
                        {char.name}
                      </label>
                    ))}
                  </div>
                </div>
                <div className="flex gap-2">
                  <button
                    onClick={handleSaveConflict}
                    className="px-3 py-1 text-sm bg-blue-500 text-white rounded hover:bg-blue-600"
                  >
                    {selectedConflict ? '保存' : '创建'}
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

          {/* 冲突列表 */}
          <div className="space-y-3">
            {conflicts.length === 0 ? (
              <div className="text-center text-gray-500 py-8">暂无冲突</div>
            ) : (
              conflicts.map((conflict) => (
                <div
                  key={conflict.id}
                  className="p-3 border rounded-lg"
                >
                  <div className="flex items-start justify-between mb-2">
                    <div>
                      <div className="flex items-center gap-2 mb-1">
                        <span className="font-medium">{conflict.title}</span>
                        <span className={`px-1.5 py-0.5 text-xs rounded ${CONFLICT_STATUS_COLORS[conflict.status]}`}>
                          {CONFLICT_STATUS_LABELS[conflict.status]}
                        </span>
                        <span className="px-1.5 py-0.5 text-xs bg-gray-100 rounded">
                          {CONFLICT_TYPE_LABELS[conflict.conflict_type]}
                        </span>
                      </div>
                      {conflict.description && (
                        <p className="text-sm text-gray-500">{conflict.description}</p>
                      )}
                    </div>
                    <div className="flex gap-1">
                      <button
                        onClick={() => startEditingConflict(conflict)}
                        className="p-1 text-gray-400 hover:text-gray-600"
                      >
                        ✏️
                      </button>
                      <button
                        onClick={() => handleDeleteConflict(conflict.id)}
                        className="p-1 text-gray-400 hover:text-red-600"
                      >
                        🗑️
                      </button>
                    </div>
                  </div>

                  {/* 状态流转按钮 */}
                  <div className="flex gap-2 mt-2">
                    {conflict.status !== 'resolved' && (
                      <button
                        onClick={() => {
                          const nextStatus =
                            conflict.status === 'introduced'
                              ? 'developing'
                              : conflict.status === 'developing'
                              ? 'climax'
                              : 'resolved';
                          handleUpdateConflictStatus(conflict.id, nextStatus);
                        }}
                        className="px-2 py-1 text-xs bg-blue-100 text-blue-800 rounded hover:bg-blue-200"
                      >
                        推进到: {CONFLICT_STATUS_LABELS[
                          conflict.status === 'introduced'
                            ? 'developing'
                            : conflict.status === 'developing'
                            ? 'climax'
                            : 'resolved'
                        ]}
                      </button>
                    )}
                  </div>

                  {/* 相关角色 */}
                  {conflict.characters.length > 0 && (
                    <div className="flex flex-wrap gap-1 mt-2">
                      {conflict.characters.map((char) => (
                        <span key={char.id} className="px-1.5 py-0.5 text-xs bg-gray-100 rounded">
                          👤 {char.name}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              ))
            )}
          </div>
        </div>
      )}

      {/* 伏笔追踪 */}
      {activeTab === 'foreshadowing' && (
        <div>
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold">伏笔追踪</h3>
            <button
              onClick={() => {
                resetForeshadowingForm();
                setIsEditingForeshadowing(true);
              }}
              className="px-3 py-1 text-sm bg-blue-500 text-white rounded hover:bg-blue-600"
            >
              + 添加伏笔
            </button>
          </div>

          {/* 伏笔表单 */}
          {isEditingForeshadowing && (
            <div className="mb-4 p-3 bg-gray-50 rounded-lg">
              <h4 className="text-sm font-medium mb-2">
                {selectedForeshadowing ? '编辑伏笔' : '添加伏笔'}
              </h4>
              <div className="space-y-3">
                <div>
                  <label className="block text-xs text-gray-500 mb-1">标题</label>
                  <input
                    type="text"
                    value={foreshadowingForm.title}
                    onChange={(e) =>
                      setForeshadowingForm((prev) => ({ ...prev, title: e.target.value }))
                    }
                    className="w-full px-2 py-1 border rounded text-sm"
                  />
                </div>
                <div>
                  <label className="block text-xs text-gray-500 mb-1">描述</label>
                  <textarea
                    value={foreshadowingForm.description}
                    onChange={(e) =>
                      setForeshadowingForm((prev) => ({ ...prev, description: e.target.value }))
                    }
                    className="w-full px-2 py-1 border rounded text-sm resize-none"
                    rows={2}
                  />
                </div>
                <div>
                  <label className="block text-xs text-gray-500 mb-1">伏笔类型</label>
                  <select
                    value={foreshadowingForm.foreshadowing_type}
                    onChange={(e) =>
                      setForeshadowingForm((prev) => ({
                        ...prev,
                        foreshadowing_type: e.target.value,
                      }))
                    }
                    className="w-full px-2 py-1 border rounded text-sm"
                  >
                    {Object.entries(FORESHADOWING_TYPE_LABELS).map(([value, label]) => (
                      <option key={value} value={value}>{label}</option>
                    ))}
                  </select>
                </div>
                <div className="flex gap-2">
                  <button
                    onClick={handleSaveForeshadowing}
                    className="px-3 py-1 text-sm bg-blue-500 text-white rounded hover:bg-blue-600"
                  >
                    {selectedForeshadowing ? '保存' : '创建'}
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

          {/* 伏笔列表 */}
          <div className="space-y-3">
            {foreshadowing.length === 0 ? (
              <div className="text-center text-gray-500 py-8">暂无伏笔</div>
            ) : (
              foreshadowing.map((fs) => (
                <div
                  key={fs.id}
                  className="p-3 border rounded-lg"
                >
                  <div className="flex items-start justify-between mb-2">
                    <div>
                      <div className="flex items-center gap-2 mb-1">
                        <span className="font-medium">{fs.title}</span>
                        <span className={`px-1.5 py-0.5 text-xs rounded ${FORESHADOWING_STATUS_COLORS[fs.status]}`}>
                          {FORESHADOWING_STATUS_LABELS[fs.status]}
                        </span>
                        <span className="px-1.5 py-0.5 text-xs bg-gray-100 rounded">
                          {FORESHADOWING_TYPE_LABELS[fs.foreshadowing_type]}
                        </span>
                      </div>
                      {fs.description && (
                        <p className="text-sm text-gray-500">{fs.description}</p>
                      )}
                    </div>
                    <div className="flex gap-1">
                      <button
                        onClick={() => startEditingForeshadowing(fs)}
                        className="p-1 text-gray-400 hover:text-gray-600"
                      >
                        ✏️
                      </button>
                      <button
                        onClick={() => handleDeleteForeshadowing(fs.id)}
                        className="p-1 text-gray-400 hover:text-red-600"
                      >
                        🗑️
                      </button>
                    </div>
                  </div>

                  {/* 状态流转按钮 */}
                  <div className="flex gap-2 mt-2">
                    {fs.status !== 'resolved' && (
                      <button
                        onClick={() => {
                          const nextStatus =
                            fs.status === 'planted'
                              ? 'hinted'
                              : fs.status === 'hinted'
                              ? 'revealed'
                              : 'resolved';
                          handleUpdateForeshadowingStatus(fs.id, nextStatus);
                        }}
                        className="px-2 py-1 text-xs bg-blue-100 text-blue-800 rounded hover:bg-blue-200"
                      >
                        推进到: {FORESHADOWING_STATUS_LABELS[
                          fs.status === 'planted'
                            ? 'hinted'
                            : fs.status === 'hinted'
                            ? 'revealed'
                            : 'resolved'
                        ]}
                      </button>
                    )}
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default ConflictTracker;
