import React, { useState, useEffect } from 'react';
import {
  WorldbuildingCategory,
  WorldbuildingEntry,
  getCategories,
  createCategory,
  updateCategory,
  deleteCategory,
  createPresetCategories,
  getEntries,
  createEntry,
  updateEntry,
  deleteEntry,
  searchEntries,
} from '../api/worldbuilding';

interface WorldbuildingPanelProps {
  taskId: number;
  characters?: Array<{ id: number; name: string }>;
  onEntryClick?: (entry: WorldbuildingEntry) => void;
}

export const WorldbuildingPanel: React.FC<WorldbuildingPanelProps> = ({
  taskId,
  characters = [],
  onEntryClick,
}) => {
  const [categories, setCategories] = useState<WorldbuildingCategory[]>([]);
  const [entries, setEntries] = useState<WorldbuildingEntry[]>([]);
  const [selectedCategory, setSelectedCategory] = useState<WorldbuildingCategory | null>(null);
  const [selectedEntry, setSelectedEntry] = useState<WorldbuildingEntry | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isEditingCategory, setIsEditingCategory] = useState(false);
  const [isEditingEntry, setIsEditingEntry] = useState(false);
  const [isCreatingEntry, setIsCreatingEntry] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');

  // 分类表单
  const [categoryForm, setCategoryForm] = useState({
    name: '',
    icon: '📁',
    description: '',
  });

  // 条目表单
  const [entryForm, setEntryForm] = useState({
    title: '',
    content: '',
    attributes: {} as Record<string, any>,
    related_entries: [] as number[],
    related_characters: [] as number[],
  });

  // 加载数据
  useEffect(() => {
    loadData();
  }, [taskId]);

  const loadData = async () => {
    setIsLoading(true);
    try {
      const cats = await getCategories(taskId);
      setCategories(cats);
    } catch (error) {
      console.error('Failed to load data:', error);
    } finally {
      setIsLoading(false);
    }
  };

  // 加载条目
  useEffect(() => {
    if (selectedCategory) {
      loadEntries(selectedCategory.id);
    } else {
      loadEntries();
    }
  }, [selectedCategory, taskId]);

  const loadEntries = async (categoryId?: number) => {
    try {
      const data = await getEntries(taskId, categoryId);
      setEntries(data);
    } catch (error) {
      console.error('Failed to load entries:', error);
    }
  };

  // 搜索条目
  const handleSearch = async () => {
    if (!searchQuery.trim()) {
      loadEntries(selectedCategory?.id);
      return;
    }

    try {
      const results = await searchEntries(taskId, searchQuery);
      setEntries(results);
    } catch (error) {
      console.error('Failed to search entries:', error);
    }
  };

  // 创建预设分类
  const handleCreatePresets = async () => {
    try {
      const result = await createPresetCategories(taskId);
      alert(`已创建 ${result.created} 个预设分类`);
      loadData();
    } catch (error) {
      console.error('Failed to create presets:', error);
    }
  };

  // 创建/更新分类
  const handleSaveCategory = async () => {
    if (!categoryForm.name.trim()) return;

    try {
      if (isEditingCategory && selectedCategory) {
        await updateCategory(selectedCategory.id, categoryForm);
      } else {
        await createCategory({
          task_id: taskId,
          ...categoryForm,
        });
      }
      setIsEditingCategory(false);
      setCategoryForm({ name: '', icon: '📁', description: '' });
      loadData();
    } catch (error) {
      console.error('Failed to save category:', error);
    }
  };

  // 删除分类
  const handleDeleteCategory = async (catId: number) => {
    if (!confirm('确定要删除此分类及其所有条目吗？')) return;

    try {
      await deleteCategory(catId);
      if (selectedCategory?.id === catId) {
        setSelectedCategory(null);
      }
      loadData();
    } catch (error) {
      console.error('Failed to delete category:', error);
    }
  };

  // 创建/更新条目
  const handleSaveEntry = async () => {
    if (!entryForm.title.trim()) return;

    try {
      if (isEditingEntry && selectedEntry) {
        await updateEntry(selectedEntry.id, entryForm);
      } else {
        await createEntry({
          task_id: taskId,
          category_id: selectedCategory?.id || categories[0]?.id,
          ...entryForm,
        });
      }
      setIsEditingEntry(false);
      setIsCreatingEntry(false);
      resetEntryForm();
      loadEntries(selectedCategory?.id);
    } catch (error) {
      console.error('Failed to save entry:', error);
    }
  };

  // 删除条目
  const handleDeleteEntry = async (entryId: number) => {
    if (!confirm('确定要删除此条目吗？')) return;

    try {
      await deleteEntry(entryId);
      if (selectedEntry?.id === entryId) {
        setSelectedEntry(null);
      }
      loadEntries(selectedCategory?.id);
    } catch (error) {
      console.error('Failed to delete entry:', error);
    }
  };

  // 重置表单
  const resetEntryForm = () => {
    setEntryForm({
      title: '',
      content: '',
      attributes: {},
      related_entries: [],
      related_characters: [],
    });
  };

  // 开始编辑分类
  const startEditingCategory = (category: WorldbuildingCategory) => {
    setSelectedCategory(category);
    setCategoryForm({
      name: category.name,
      icon: category.icon,
      description: category.description,
    });
    setIsEditingCategory(true);
  };

  // 开始编辑条目
  const startEditingEntry = (entry: WorldbuildingEntry) => {
    setSelectedEntry(entry);
    setEntryForm({
      title: entry.title,
      content: entry.content,
      attributes: entry.attributes,
      related_entries: entry.related_entries,
      related_characters: entry.related_characters,
    });
    setIsEditingEntry(true);
    setIsCreatingEntry(false);
  };

  // 开始创建条目
  const startCreatingEntry = () => {
    resetEntryForm();
    setIsCreatingEntry(true);
    setIsEditingEntry(false);
  };

  // 取消编辑
  const cancelEditing = () => {
    setIsEditingCategory(false);
    setIsEditingEntry(false);
    setIsCreatingEntry(false);
    resetEntryForm();
  };

  if (isLoading) {
    return (
      <div className="worldbuilding-panel p-4">
        <div className="text-center text-gray-500">加载中...</div>
      </div>
    );
  }

  return (
    <div className="worldbuilding-panel flex">
      {/* 左侧：分类树 */}
      <div className="w-48 border-r pr-4">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold">世界观</h3>
          <button
            onClick={handleCreatePresets}
            className="px-2 py-1 text-xs bg-gray-200 rounded hover:bg-gray-300"
            title="创建预设分类"
          >
            预设
          </button>
        </div>

        <div className="space-y-1">
          <div
            className={`flex items-center gap-2 px-2 py-1 cursor-pointer rounded ${
              !selectedCategory ? 'bg-blue-100' : 'hover:bg-gray-100'
            }`}
            onClick={() => setSelectedCategory(null)}
          >
            <span>📁</span>
            <span className="text-sm">全部</span>
          </div>

          {categories.map((cat) => (
            <div
              key={cat.id}
              className={`flex items-center justify-between px-2 py-1 cursor-pointer rounded ${
                selectedCategory?.id === cat.id ? 'bg-blue-100' : 'hover:bg-gray-100'
              }`}
              onClick={() => setSelectedCategory(cat)}
            >
              <div className="flex items-center gap-2">
                <span>{cat.icon}</span>
                <span className="text-sm">{cat.name}</span>
                <span className="text-xs text-gray-400">{cat.entries_count}</span>
              </div>
              <div className="flex gap-1">
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    startEditingCategory(cat);
                  }}
                  className="p-1 text-gray-400 hover:text-gray-600 opacity-0 group-hover:opacity-100"
                >
                  ✏️
                </button>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    handleDeleteCategory(cat.id);
                  }}
                  className="p-1 text-gray-400 hover:text-red-600 opacity-0 group-hover:opacity-100"
                >
                  🗑️
                </button>
              </div>
            </div>
          ))}

          <button
            onClick={() => {
              setCategoryForm({ name: '', icon: '📁', description: '' });
              setIsEditingCategory(true);
            }}
            className="w-full px-2 py-1 text-sm text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded"
          >
            + 添加分类
          </button>
        </div>
      </div>

      {/* 中间：条目列表 */}
      <div className="flex-1 px-4">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold">
            {selectedCategory ? selectedCategory.name : '全部条目'}
          </h3>
          <div className="flex gap-2">
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
              className="px-2 py-1 border rounded text-sm w-40"
              placeholder="搜索条目..."
            />
            <button
              onClick={startCreatingEntry}
              className="px-3 py-1 text-sm bg-blue-500 text-white rounded hover:bg-blue-600"
            >
              + 新建条目
            </button>
          </div>
        </div>

        {/* 条目列表 */}
        <div className="space-y-2 max-h-[500px] overflow-y-auto">
          {entries.length === 0 ? (
            <div className="text-center text-gray-500 py-8">
              暂无条目
            </div>
          ) : (
            entries.map((entry) => (
              <div
                key={entry.id}
                className={`p-3 border rounded-lg cursor-pointer ${
                  selectedEntry?.id === entry.id ? 'border-blue-300 bg-blue-50' : 'hover:bg-gray-50'
                }`}
                onClick={() => {
                  setSelectedEntry(entry);
                  onEntryClick?.(entry);
                }}
              >
                <div className="flex items-center justify-between mb-1">
                  <div className="flex items-center gap-2">
                    {entry.category && <span>{entry.category.icon}</span>}
                    <span className="font-medium">{entry.title}</span>
                  </div>
                  <div className="flex gap-1">
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        startEditingEntry(entry);
                      }}
                      className="p-1 text-gray-400 hover:text-gray-600"
                    >
                      ✏️
                    </button>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        handleDeleteEntry(entry.id);
                      }}
                      className="p-1 text-gray-400 hover:text-red-600"
                    >
                      🗑️
                    </button>
                  </div>
                </div>
                {entry.content && (
                  <p className="text-sm text-gray-500 line-clamp-2">{entry.content}</p>
                )}
              </div>
            ))
          )}
        </div>
      </div>

      {/* 右侧：编辑面板 */}
      {(isEditingCategory || isEditingEntry || isCreatingEntry) && (
        <div className="w-80 border-l pl-4">
          {isEditingCategory ? (
            <div className="p-3 bg-gray-50 rounded-lg">
              <h4 className="text-sm font-medium mb-3">编辑分类</h4>
              <div className="space-y-3">
                <div>
                  <label className="block text-xs text-gray-500 mb-1">名称</label>
                  <input
                    type="text"
                    value={categoryForm.name}
                    onChange={(e) =>
                      setCategoryForm((prev) => ({ ...prev, name: e.target.value }))
                    }
                    className="w-full px-2 py-1 border rounded text-sm"
                  />
                </div>
                <div>
                  <label className="block text-xs text-gray-500 mb-1">图标</label>
                  <input
                    type="text"
                    value={categoryForm.icon}
                    onChange={(e) =>
                      setCategoryForm((prev) => ({ ...prev, icon: e.target.value }))
                    }
                    className="w-full px-2 py-1 border rounded text-sm"
                  />
                </div>
                <div>
                  <label className="block text-xs text-gray-500 mb-1">描述</label>
                  <textarea
                    value={categoryForm.description}
                    onChange={(e) =>
                      setCategoryForm((prev) => ({ ...prev, description: e.target.value }))
                    }
                    className="w-full px-2 py-1 border rounded text-sm resize-none"
                    rows={2}
                  />
                </div>
                <div className="flex gap-2">
                  <button
                    onClick={handleSaveCategory}
                    className="px-3 py-1 text-sm bg-blue-500 text-white rounded hover:bg-blue-600"
                  >
                    保存
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
          ) : (
            <div className="p-3 bg-gray-50 rounded-lg">
              <h4 className="text-sm font-medium mb-3">
                {isEditingEntry ? '编辑条目' : '新建条目'}
              </h4>
              <div className="space-y-3">
                <div>
                  <label className="block text-xs text-gray-500 mb-1">标题</label>
                  <input
                    type="text"
                    value={entryForm.title}
                    onChange={(e) =>
                      setEntryForm((prev) => ({ ...prev, title: e.target.value }))
                    }
                    className="w-full px-2 py-1 border rounded text-sm"
                  />
                </div>
                <div>
                  <label className="block text-xs text-gray-500 mb-1">内容</label>
                  <textarea
                    value={entryForm.content}
                    onChange={(e) =>
                      setEntryForm((prev) => ({ ...prev, content: e.target.value }))
                    }
                    className="w-full px-2 py-1 border rounded text-sm resize-none"
                    rows={4}
                  />
                </div>
                <div>
                  <label className="block text-xs text-gray-500 mb-1">关联角色</label>
                  <div className="flex flex-wrap gap-1">
                    {characters.map((char) => (
                      <label
                        key={char.id}
                        className={`flex items-center gap-1 px-2 py-1 text-xs rounded cursor-pointer ${
                          entryForm.related_characters.includes(char.id)
                            ? 'bg-blue-100 text-blue-800'
                            : 'bg-gray-100 text-gray-600'
                        }`}
                      >
                        <input
                          type="checkbox"
                          checked={entryForm.related_characters.includes(char.id)}
                          onChange={(e) => {
                            const newChars = e.target.checked
                              ? [...entryForm.related_characters, char.id]
                              : entryForm.related_characters.filter((id) => id !== char.id);
                            setEntryForm((prev) => ({ ...prev, related_characters: newChars }));
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
                    onClick={handleSaveEntry}
                    className="px-3 py-1 text-sm bg-blue-500 text-white rounded hover:bg-blue-600"
                  >
                    {isEditingEntry ? '保存' : '创建'}
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
        </div>
      )}
    </div>
  );
};

export default WorldbuildingPanel;
