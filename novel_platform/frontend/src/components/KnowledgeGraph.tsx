import React, { useState, useEffect, useCallback, useRef } from 'react';
import { GraphData, GraphNode, GraphEdge, getGraph, getNeighbors } from '../api/graph';

interface KnowledgeGraphProps {
  taskId: number;
  onNodeClick?: (node: GraphNode) => void;
}

const NODE_COLORS: Record<string, string> = {
  chapter: '#3b82f6',
  character: '#22c55e',
  note: '#eab308',
  source: '#a855f7',
  tag: '#6b7280',
};

const NODE_ICONS: Record<string, string> = {
  chapter: '📄',
  character: '👤',
  note: '📝',
  source: '📎',
  tag: '🏷️',
};

export const KnowledgeGraph: React.FC<KnowledgeGraphProps> = ({
  taskId,
  onNodeClick,
}) => {
  const [graphData, setGraphData] = useState<GraphData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null);
  const [filterType, setFilterType] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [nodePositions, setNodePositions] = useState<
    Map<string, { x: number; y: number }>
  >(new Map());

  // 加载图数据
  useEffect(() => {
    loadGraph();
  }, [taskId, filterType]);

  const loadGraph = async () => {
    setIsLoading(true);
    try {
      const data = await getGraph(taskId, filterType || undefined);
      setGraphData(data);

      // 初始化节点位置
      const positions = new Map<string, { x: number; y: number }>();
      const centerX = 400;
      const centerY = 300;
      const radius = 200;

      data.nodes.forEach((node, index) => {
        const angle = (2 * Math.PI * index) / data.nodes.length;
        positions.set(node.id, {
          x: centerX + radius * Math.cos(angle),
          y: centerY + radius * Math.sin(angle),
        });
      });

      setNodePositions(positions);
    } catch (error) {
      console.error('Failed to load graph:', error);
    } finally {
      setIsLoading(false);
    }
  };

  // 绘制图
  useEffect(() => {
    if (!graphData || !canvasRef.current) return;

    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // 清空画布
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // 绘制边
    graphData.edges.forEach((edge) => {
      const sourcePos = nodePositions.get(edge.source);
      const targetPos = nodePositions.get(edge.target);
      if (!sourcePos || !targetPos) return;

      ctx.beginPath();
      ctx.moveTo(sourcePos.x, sourcePos.y);
      ctx.lineTo(targetPos.x, targetPos.y);

      // 根据边类型设置样式
      switch (edge.type) {
        case 'reference':
          ctx.strokeStyle = '#3b82f6';
          ctx.lineWidth = 2;
          break;
        case 'appearance':
          ctx.strokeStyle = '#22c55e';
          ctx.lineWidth = 1.5;
          ctx.setLineDash([5, 5]);
          break;
        case 'tag':
          ctx.strokeStyle = '#6b7280';
          ctx.lineWidth = 1;
          ctx.setLineDash([3, 3]);
          break;
        default:
          ctx.strokeStyle = '#d1d5db';
          ctx.lineWidth = 1;
      }

      ctx.stroke();
      ctx.setLineDash([]);

      // 绘制边标签
      if (edge.label) {
        const midX = (sourcePos.x + targetPos.x) / 2;
        const midY = (sourcePos.y + targetPos.y) / 2;
        ctx.font = '10px Arial';
        ctx.fillStyle = '#6b7280';
        ctx.textAlign = 'center';
        ctx.fillText(edge.label, midX, midY - 5);
      }
    });

    // 绘制节点
    graphData.nodes.forEach((node) => {
      const pos = nodePositions.get(node.id);
      if (!pos) return;

      const isSelected = selectedNode?.id === node.id;
      const nodeSize = isSelected ? 25 : 20;

      // 绘制节点背景
      ctx.beginPath();
      ctx.arc(pos.x, pos.y, nodeSize, 0, 2 * Math.PI);
      ctx.fillStyle = NODE_COLORS[node.type] || '#6b7280';
      ctx.fill();

      if (isSelected) {
        ctx.strokeStyle = '#000';
        ctx.lineWidth = 2;
        ctx.stroke();
      }

      // 绘制节点图标
      ctx.font = '16px Arial';
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      ctx.fillText(NODE_ICONS[node.type] || '📌', pos.x, pos.y);

      // 绘制节点标签
      ctx.font = '12px Arial';
      ctx.fillStyle = '#000';
      ctx.textAlign = 'center';
      ctx.textBaseline = 'top';
      ctx.fillText(node.label, pos.x, pos.y + nodeSize + 5);
    });
  }, [graphData, nodePositions, selectedNode]);

  // 处理节点点击
  const handleCanvasClick = (e: React.MouseEvent<HTMLCanvasElement>) => {
    if (!graphData) return;

    const canvas = canvasRef.current;
    if (!canvas) return;

    const rect = canvas.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;

    // 检查是否点击了节点
    for (const node of graphData.nodes) {
      const pos = nodePositions.get(node.id);
      if (!pos) continue;

      const distance = Math.sqrt((x - pos.x) ** 2 + (y - pos.y) ** 2);
      if (distance <= 20) {
        setSelectedNode(node);
        onNodeClick?.(node);
        return;
      }
    }

    setSelectedNode(null);
  };

  // 过滤节点
  const filteredNodes = graphData?.nodes.filter((node) =>
    node.label.toLowerCase().includes(searchQuery.toLowerCase())
  );

  if (isLoading) {
    return (
      <div className="knowledge-graph p-4">
        <div className="text-center text-gray-500">加载中...</div>
      </div>
    );
  }

  if (!graphData) {
    return (
      <div className="knowledge-graph p-4">
        <div className="text-center text-gray-500">暂无数据</div>
      </div>
    );
  }

  return (
    <div className="knowledge-graph">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold">知识图谱</h3>
        <div className="flex items-center gap-2">
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="px-2 py-1 border rounded text-sm w-40"
            placeholder="搜索节点..."
          />
          <select
            value={filterType || ''}
            onChange={(e) => setFilterType(e.target.value || null)}
            className="px-2 py-1 border rounded text-sm"
          >
            <option value="">全部类型</option>
            <option value="chapter">章节</option>
            <option value="character">角色</option>
            <option value="note">笔记</option>
            <option value="source">素材</option>
            <option value="tag">标签</option>
          </select>
        </div>
      </div>

      {/* 统计信息 */}
      <div className="flex gap-4 mb-4 text-sm">
        <span>节点: {graphData.stats.total_nodes}</span>
        <span>关系: {graphData.stats.total_edges}</span>
        <span>章节: {graphData.stats.chapters}</span>
        <span>角色: {graphData.stats.characters}</span>
        <span>笔记: {graphData.stats.notes}</span>
      </div>

      {/* 图谱画布 */}
      <div className="border rounded-lg overflow-hidden">
        <canvas
          ref={canvasRef}
          width={800}
          height={600}
          onClick={handleCanvasClick}
          className="cursor-pointer"
        />
      </div>

      {/* 图例 */}
      <div className="flex gap-4 mt-4 text-xs">
        {Object.entries(NODE_COLORS).map(([type, color]) => (
          <div key={type} className="flex items-center gap-1">
            <div
              className="w-3 h-3 rounded-full"
              style={{ backgroundColor: color }}
            />
            <span>{type === 'chapter' ? '章节' : type === 'character' ? '角色' : type === 'note' ? '笔记' : type === 'source' ? '素材' : '标签'}</span>
          </div>
        ))}
      </div>

      {/* 选中节点详情 */}
      {selectedNode && (
        <div className="mt-4 p-3 bg-gray-50 rounded-lg">
          <h4 className="font-semibold mb-2">
            {NODE_ICONS[selectedNode.type]} {selectedNode.label}
          </h4>
          <div className="text-sm text-gray-600">
            类型: {selectedNode.type}
          </div>
          {selectedNode.data && (
            <div className="mt-2 text-sm">
              {Object.entries(selectedNode.data).map(([key, value]) => (
                <div key={key}>
                  <span className="text-gray-500">{key}: </span>
                  <span>{String(value)}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* 节点列表 */}
      {searchQuery && filteredNodes && filteredNodes.length > 0 && (
        <div className="mt-4">
          <h4 className="text-sm font-semibold mb-2">搜索结果</h4>
          <div className="space-y-1 max-h-40 overflow-y-auto">
            {filteredNodes.map((node) => (
              <div
                key={node.id}
                className="flex items-center gap-2 p-2 hover:bg-gray-50 cursor-pointer rounded"
                onClick={() => {
                  setSelectedNode(node);
                  onNodeClick?.(node);
                }}
              >
                <span>{NODE_ICONS[node.type]}</span>
                <span className="text-sm">{node.label}</span>
                <span className="text-xs text-gray-400">{node.type}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default KnowledgeGraph;
