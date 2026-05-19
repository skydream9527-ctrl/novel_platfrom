import React, { useState, useEffect } from 'react';
import {
  AttributeDefinition,
  AttributeValue,
  getAttributeDefinitions,
  getChapterAttributeValues,
  batchUpdateAttributeValues,
} from '../api/attributes';

interface AttributeEditorProps {
  taskId: number;
  chapterId: number;
  onUpdate?: () => void;
}

export const AttributeEditor: React.FC<AttributeEditorProps> = ({
  taskId,
  chapterId,
  onUpdate,
}) => {
  const [definitions, setDefinitions] = useState<AttributeDefinition[]>([]);
  const [values, setValues] = useState<AttributeValue[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);

  useEffect(() => {
    loadData();
  }, [taskId, chapterId]);

  const loadData = async () => {
    setIsLoading(true);
    try {
      const [defs, vals] = await Promise.all([
        getAttributeDefinitions(taskId),
        getChapterAttributeValues(chapterId),
      ]);
      setDefinitions(defs);
      setValues(vals);
    } catch (error) {
      console.error('Failed to load attributes:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const getValue = (definitionId: number): string => {
    const val = values.find((v) => v.definition_id === definitionId);
    return val?.value || '';
  };

  const handleChange = async (definitionId: number, value: string) => {
    setIsSaving(true);
    try {
      await batchUpdateAttributeValues([
        {
          definition_id: definitionId,
          chapter_id: chapterId,
          value: value || null,
        },
      ]);
      // 更新本地状态
      setValues((prev) => {
        const existing = prev.find((v) => v.definition_id === definitionId);
        if (existing) {
          return prev.map((v) =>
            v.definition_id === definitionId ? { ...v, value } : v
          );
        } else {
          return [
            ...prev,
            {
              id: Date.now(),
              definition_id: definitionId,
              chapter_id: chapterId,
              value,
              definition: {
                name: definitions.find((d) => d.id === definitionId)?.name || '',
                field_type: definitions.find((d) => d.id === definitionId)?.field_type || '',
                options: definitions.find((d) => d.id === definitionId)?.options || null,
              },
            },
          ];
        }
      });
      onUpdate?.();
    } catch (error) {
      console.error('Failed to update attribute:', error);
    } finally {
      setIsSaving(false);
    }
  };

  const renderInput = (definition: AttributeDefinition) => {
    const value = getValue(definition.id);

    switch (definition.field_type) {
      case 'text':
        return (
          <input
            type="text"
            value={value}
            onChange={(e) => handleChange(definition.id, e.target.value)}
            className="w-full px-2 py-1 border rounded text-sm"
            placeholder={`输入${definition.name}`}
          />
        );

      case 'number':
        return (
          <input
            type="number"
            value={value}
            onChange={(e) => handleChange(definition.id, e.target.value)}
            className="w-full px-2 py-1 border rounded text-sm"
            placeholder={`输入${definition.name}`}
          />
        );

      case 'select':
        return (
          <select
            value={value}
            onChange={(e) => handleChange(definition.id, e.target.value)}
            className="w-full px-2 py-1 border rounded text-sm"
          >
            <option value="">请选择</option>
            {definition.options?.map((option) => (
              <option key={option} value={option}>
                {option}
              </option>
            ))}
          </select>
        );

      case 'multi_select':
        const selectedValues = value ? value.split(',') : [];
        return (
          <div className="space-y-1">
            {definition.options?.map((option) => (
              <label key={option} className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={selectedValues.includes(option)}
                  onChange={(e) => {
                    const newValues = e.target.checked
                      ? [...selectedValues, option]
                      : selectedValues.filter((v) => v !== option);
                    handleChange(definition.id, newValues.join(','));
                  }}
                  className="rounded"
                />
                <span className="text-sm">{option}</span>
              </label>
            ))}
          </div>
        );

      case 'date':
        return (
          <input
            type="date"
            value={value}
            onChange={(e) => handleChange(definition.id, e.target.value)}
            className="w-full px-2 py-1 border rounded text-sm"
          />
        );

      case 'checkbox':
        return (
          <label className="flex items-center gap-2">
            <input
              type="checkbox"
              checked={value === 'true'}
              onChange={(e) => handleChange(definition.id, e.target.checked ? 'true' : 'false')}
              className="rounded"
            />
            <span className="text-sm">{definition.name}</span>
          </label>
        );

      case 'url':
        return (
          <input
            type="url"
            value={value}
            onChange={(e) => handleChange(definition.id, e.target.value)}
            className="w-full px-2 py-1 border rounded text-sm"
            placeholder="https://..."
          />
        );

      default:
        return (
          <input
            type="text"
            value={value}
            onChange={(e) => handleChange(definition.id, e.target.value)}
            className="w-full px-2 py-1 border rounded text-sm"
          />
        );
    }
  };

  if (isLoading) {
    return (
      <div className="attribute-editor p-4">
        <div className="text-center text-gray-500">加载中...</div>
      </div>
    );
  }

  if (definitions.length === 0) {
    return (
      <div className="attribute-editor p-4">
        <div className="text-center text-gray-500 text-sm">
          暂无自定义属性
        </div>
      </div>
    );
  }

  return (
    <div className="attribute-editor">
      <div className="flex items-center justify-between mb-3">
        <h4 className="text-sm font-semibold">自定义属性</h4>
        {isSaving && (
          <span className="text-xs text-gray-400">保存中...</span>
        )}
      </div>

      <div className="space-y-3">
        {definitions.map((definition) => (
          <div key={definition.id}>
            <label className="block text-xs text-gray-500 mb-1">
              {definition.name}
            </label>
            {renderInput(definition)}
          </div>
        ))}
      </div>
    </div>
  );
};

export default AttributeEditor;
