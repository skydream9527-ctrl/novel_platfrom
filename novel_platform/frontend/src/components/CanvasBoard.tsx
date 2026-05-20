import { useState, useRef, useEffect, useCallback } from "react";
import client from "../api/client";

interface CanvasCard {
  id: number;
  title: string;
  content: string;
  card_type: string;
  x: number;
  y: number;
  width: number;
  height: number;
  color: string;
}

interface CanvasConnection {
  id: number;
  source_card_id: number;
  target_card_id: number;
  label: string;
  connection_type: string;
}

interface CanvasData {
  cards: CanvasCard[];
  connections: CanvasConnection[];
}

interface Props {
  taskId: number;
}

const CARD_COLORS = [
  "#ffffff", "#fef3c7", "#dbeafe", "#dcfce7", "#fce7f3",
  "#f3e8ff", "#e0e7ff", "#cffafe", "#d1fae5",
];

const CARD_TYPES = [
  { key: "note", label: "笔记", icon: "📝" },
  { key: "scene", label: "场景", icon: "🎬" },
  { key: "character", label: "角色", icon: "👤" },
  { key: "event", label: "事件", icon: "⚡" },
  { key: "idea", label: "灵感", icon: "💡" },
];

export default function CanvasBoard({ taskId }: Props) {
  const [cards, setCards] = useState<CanvasCard[]>([]);
  const [connections, setConnections] = useState<CanvasConnection[]>([]);
  const [selectedCard, setSelectedCard] = useState<number | null>(null);
  const [dragging, setDragging] = useState<{ id: number; offsetX: number; offsetY: number } | null>(null);
  const [connecting, setConnecting] = useState<{ sourceId: number; mouseX: number; mouseY: number } | null>(null);
  const [showAddCard, setShowAddCard] = useState(false);
  const [newCard, setNewCard] = useState({ title: "", content: "", card_type: "note", color: "#ffffff" });
  const [editingCard, setEditingCard] = useState<CanvasCard | null>(null);
  const canvasRef = useRef<HTMLDivElement>(null);
  const [canvasOffset, setCanvasOffset] = useState({ x: 0, y: 0 });
  const [zoom, setZoom] = useState(1);

  useEffect(() => {
    loadCanvas();
  }, [taskId]);

  const loadCanvas = async () => {
    try {
      const res = await client.get(`/canvas/by-task/${taskId}`);
      setCards(res.data.cards);
      setConnections(res.data.connections);
    } catch {
      setCards([]);
      setConnections([]);
    }
  };

  const handleAddCard = async () => {
    if (!newCard.title.trim()) return;
    const res = await client.post("/canvas/cards", {
      task_id: taskId,
      ...newCard,
      x: 100 + Math.random() * 300,
      y: 100 + Math.random() * 300,
    });
    setCards((prev) => [...prev, res.data]);
    setShowAddCard(false);
    setNewCard({ title: "", content: "", card_type: "note", color: "#ffffff" });
  };

  const handleUpdateCard = async (cardId: number, updates: Partial<CanvasCard>) => {
    await client.patch(`/canvas/cards/${cardId}`, updates);
    setCards((prev) => prev.map((c) => (c.id === cardId ? { ...c, ...updates } : c)));
  };

  const handleDeleteCard = async (cardId: number) => {
    await client.delete(`/canvas/cards/${cardId}`);
    setCards((prev) => prev.filter((c) => c.id !== cardId));
    setConnections((prev) => prev.filter((conn) => conn.source_card_id !== cardId && conn.target_card_id !== cardId));
    if (selectedCard === cardId) setSelectedCard(null);
  };

  const handleAddConnection = async (sourceId: number, targetId: number) => {
    const res = await client.post("/canvas/connections", {
      task_id: taskId,
      source_card_id: sourceId,
      target_card_id: targetId,
      label: "",
      connection_type: "related",
    });
    setConnections((prev) => [...prev, res.data]);
  };

  const handleDeleteConnection = async (connId: number) => {
    await client.delete(`/canvas/connections/${connId}`);
    setConnections((prev) => prev.filter((c) => c.id !== connId));
  };

  const handleMouseDown = (e: React.MouseEvent, cardId: number) => {
    e.stopPropagation();
    const card = cards.find((c) => c.id === cardId);
    if (!card) return;

    if (e.shiftKey) {
      // Start connecting
      setConnecting({ sourceId: cardId, mouseX: e.clientX, mouseY: e.clientY });
    } else {
      // Start dragging
      const rect = canvasRef.current?.getBoundingClientRect();
      if (!rect) return;
      setDragging({
        id: cardId,
        offsetX: (e.clientX - rect.left) / zoom - card.x,
        offsetY: (e.clientY - rect.top) / zoom - card.y,
      });
    }
    setSelectedCard(cardId);
  };

  const handleMouseMove = useCallback((e: React.MouseEvent) => {
    if (dragging) {
      const rect = canvasRef.current?.getBoundingClientRect();
      if (!rect) return;
      const x = (e.clientX - rect.left) / zoom - dragging.offsetX;
      const y = (e.clientY - rect.top) / zoom - dragging.offsetY;
      setCards((prev) => prev.map((c) => (c.id === dragging.id ? { ...c, x, y } : c)));
    }
    if (connecting) {
      setConnecting((prev) => prev ? { ...prev, mouseX: e.clientX, mouseY: e.clientY } : null);
    }
  }, [dragging, connecting, zoom]);

  const handleMouseUp = useCallback((e: React.MouseEvent) => {
    if (dragging) {
      const card = cards.find((c) => c.id === dragging.id);
      if (card) {
        handleUpdateCard(dragging.id, { x: card.x, y: card.y });
      }
      setDragging(null);
    }
    if (connecting) {
      // Find target card
      const targetCard = cards.find((c) => {
        const rect = canvasRef.current?.getBoundingClientRect();
        if (!rect) return false;
        const mouseX = (e.clientX - rect.left) / zoom;
        const mouseY = (e.clientY - rect.top) / zoom;
        return mouseX >= c.x && mouseX <= c.x + c.width && mouseY >= c.y && mouseY <= c.y + c.height && c.id !== connecting.sourceId;
      });
      if (targetCard) {
        handleAddConnection(connecting.sourceId, targetCard.id);
      }
      setConnecting(null);
    }
  }, [dragging, connecting, cards, zoom]);

  const getCardCenter = (card: CanvasCard) => ({
    x: card.x + card.width / 2,
    y: card.y + card.height / 2,
  });

  const renderConnections = () => {
    return connections.map((conn) => {
      const source = cards.find((c) => c.id === conn.source_card_id);
      const target = cards.find((c) => c.id === conn.target_card_id);
      if (!source || !target) return null;

      const start = getCardCenter(source);
      const end = getCardCenter(target);

      return (
        <g key={conn.id}>
          <line
            x1={start.x}
            y1={start.y}
            x2={end.x}
            y2={end.y}
            stroke="#94a3b8"
            strokeWidth={2}
            strokeDasharray={conn.connection_type === "causes" ? "5,5" : "none"}
          />
          {conn.label && (
            <text
              x={(start.x + end.x) / 2}
              y={(start.y + end.y) / 2 - 8}
              textAnchor="middle"
              fill="#64748b"
              fontSize={12}
            >
              {conn.label}
            </text>
          )}
          <circle
            cx={(start.x + end.x) / 2}
            cy={(start.y + end.y) / 2}
            r={8}
            fill="#ef4444"
            stroke="white"
            strokeWidth={2}
            style={{ cursor: "pointer" }}
            onClick={() => handleDeleteConnection(conn.id)}
          />
          <text
            x={(start.x + end.x) / 2}
            y={(start.y + end.y) / 2 + 4}
            textAnchor="middle"
            fill="white"
            fontSize={10}
            fontWeight="bold"
          >
            ×
          </text>
        </g>
      );
    });
  };

  const renderConnectingLine = () => {
    if (!connecting) return null;
    const source = cards.find((c) => c.id === connecting.sourceId);
    if (!source) return null;
    const start = getCardCenter(source);
    const rect = canvasRef.current?.getBoundingClientRect();
    if (!rect) return null;
    const endX = (connecting.mouseX - rect.left) / zoom;
    const endY = (connecting.mouseY - rect.top) / zoom;

    return (
      <line
        x1={start.x}
        y1={start.y}
        x2={endX}
        y2={endY}
        stroke="#3b82f6"
        strokeWidth={2}
        strokeDasharray="5,5"
      />
    );
  };

  return (
    <div style={{ width: "100%", height: "100%", position: "relative", overflow: "hidden" }}>
      {/* Toolbar */}
      <div style={{
        position: "absolute",
        top: 12,
        left: 12,
        zIndex: 10,
        display: "flex",
        gap: 8,
        background: "var(--color-bg)",
        padding: "8px 12px",
        borderRadius: 8,
        boxShadow: "0 2px 8px rgba(0,0,0,0.1)",
      }}>
        <button className="btn-primary" onClick={() => setShowAddCard(true)} style={{ fontSize: 13, padding: "6px 12px" }}>
          + 添加卡片
        </button>
        <button className="btn-text" onClick={() => setZoom((z) => Math.min(2, z + 0.1))} style={{ fontSize: 13 }}>
          🔍+
        </button>
        <button className="btn-text" onClick={() => setZoom((z) => Math.max(0.5, z - 0.1))} style={{ fontSize: 13 }}>
          🔍-
        </button>
        <span style={{ fontSize: 12, color: "var(--color-text-secondary)", alignSelf: "center" }}>
          Shift+拖拽连线
        </span>
      </div>

      {/* Canvas */}
      <div
        ref={canvasRef}
        style={{
          width: "100%",
          height: "100%",
          background: "var(--color-bg-secondary)",
          backgroundImage: "radial-gradient(circle, #ddd 1px, transparent 1px)",
          backgroundSize: "20px 20px",
          transform: `scale(${zoom})`,
          transformOrigin: "0 0",
        }}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onClick={() => setSelectedCard(null)}
      >
        {/* Connections SVG */}
        <svg style={{ position: "absolute", top: 0, left: 0, width: "100%", height: "100%", pointerEvents: "none" }}>
          {renderConnections()}
          {renderConnectingLine()}
        </svg>

        {/* Cards */}
        {cards.map((card) => (
          <div
            key={card.id}
            style={{
              position: "absolute",
              left: card.x,
              top: card.y,
              width: card.width,
              minHeight: card.height,
              background: card.color,
              border: selectedCard === card.id ? "2px solid #3b82f6" : "1px solid #e2e8f0",
              borderRadius: 8,
              padding: 12,
              cursor: dragging?.id === card.id ? "grabbing" : "grab",
              boxShadow: selectedCard === card.id ? "0 4px 12px rgba(59,130,246,0.3)" : "0 2px 4px rgba(0,0,0,0.1)",
              zIndex: selectedCard === card.id ? 10 : 1,
            }}
            onMouseDown={(e) => handleMouseDown(e, card.id)}
            onDoubleClick={() => setEditingCard(card)}
          >
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 8 }}>
              <span style={{ fontSize: 12 }}>
                {CARD_TYPES.find((t) => t.key === card.card_type)?.icon || "📝"}
              </span>
              <button
                onClick={(e) => { e.stopPropagation(); handleDeleteCard(card.id); }}
                style={{ background: "none", border: "none", cursor: "pointer", fontSize: 14, color: "#94a3b8" }}
              >
                ×
              </button>
            </div>
            <div style={{ fontWeight: 600, fontSize: 14, marginBottom: 4 }}>{card.title}</div>
            {card.content && (
              <div style={{ fontSize: 12, color: "var(--color-text-secondary)", overflow: "hidden", textOverflow: "ellipsis", display: "-webkit-box", WebkitLineClamp: 3, WebkitBoxOrient: "vertical" }}>
                {card.content}
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Add Card Modal */}
      {showAddCard && (
        <div className="modal-overlay" onClick={() => setShowAddCard(false)}>
          <div className="modal-card" onClick={(e) => e.stopPropagation()} style={{ width: 400 }}>
            <h3>添加卡片</h3>
            <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
              <input
                placeholder="卡片标题"
                value={newCard.title}
                onChange={(e) => setNewCard((prev) => ({ ...prev, title: e.target.value }))}
                autoFocus
              />
              <textarea
                placeholder="卡片内容（可选）"
                value={newCard.content}
                onChange={(e) => setNewCard((prev) => ({ ...prev, content: e.target.value }))}
                rows={3}
              />
              <div>
                <label style={{ fontSize: 13, color: "var(--color-text-secondary)", marginBottom: 4, display: "block" }}>类型</label>
                <div style={{ display: "flex", gap: 8 }}>
                  {CARD_TYPES.map((t) => (
                    <button
                      key={t.key}
                      type="button"
                      className={newCard.card_type === t.key ? "active" : ""}
                      onClick={() => setNewCard((prev) => ({ ...prev, card_type: t.key }))}
                      style={{ fontSize: 12, padding: "4px 8px" }}
                    >
                      {t.icon} {t.label}
                    </button>
                  ))}
                </div>
              </div>
              <div>
                <label style={{ fontSize: 13, color: "var(--color-text-secondary)", marginBottom: 4, display: "block" }}>颜色</label>
                <div style={{ display: "flex", gap: 8 }}>
                  {CARD_COLORS.map((color) => (
                    <div
                      key={color}
                      onClick={() => setNewCard((prev) => ({ ...prev, color }))}
                      style={{
                        width: 28,
                        height: 28,
                        background: color,
                        border: newCard.color === color ? "2px solid #3b82f6" : "1px solid #e2e8f0",
                        borderRadius: 4,
                        cursor: "pointer",
                      }}
                    />
                  ))}
                </div>
              </div>
            </div>
            <div className="modal-actions">
              <button className="btn-cancel" onClick={() => setShowAddCard(false)}>取消</button>
              <button className="btn-save" onClick={handleAddCard}>添加</button>
            </div>
          </div>
        </div>
      )}

      {/* Edit Card Modal */}
      {editingCard && (
        <div className="modal-overlay" onClick={() => setEditingCard(null)}>
          <div className="modal-card" onClick={(e) => e.stopPropagation()} style={{ width: 400 }}>
            <h3>编辑卡片</h3>
            <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
              <input
                placeholder="卡片标题"
                value={editingCard.title}
                onChange={(e) => setEditingCard((prev) => prev ? { ...prev, title: e.target.value } : null)}
              />
              <textarea
                placeholder="卡片内容"
                value={editingCard.content}
                onChange={(e) => setEditingCard((prev) => prev ? { ...prev, content: e.target.value } : null)}
                rows={4}
              />
              <div>
                <label style={{ fontSize: 13, color: "var(--color-text-secondary)", marginBottom: 4, display: "block" }}>类型</label>
                <div style={{ display: "flex", gap: 8 }}>
                  {CARD_TYPES.map((t) => (
                    <button
                      key={t.key}
                      type="button"
                      className={editingCard.card_type === t.key ? "active" : ""}
                      onClick={() => setEditingCard((prev) => prev ? { ...prev, card_type: t.key } : null)}
                      style={{ fontSize: 12, padding: "4px 8px" }}
                    >
                      {t.icon} {t.label}
                    </button>
                  ))}
                </div>
              </div>
              <div>
                <label style={{ fontSize: 13, color: "var(--color-text-secondary)", marginBottom: 4, display: "block" }}>颜色</label>
                <div style={{ display: "flex", gap: 8 }}>
                  {CARD_COLORS.map((color) => (
                    <div
                      key={color}
                      onClick={() => setEditingCard((prev) => prev ? { ...prev, color } : null)}
                      style={{
                        width: 28,
                        height: 28,
                        background: color,
                        border: editingCard.color === color ? "2px solid #3b82f6" : "1px solid #e2e8f0",
                        borderRadius: 4,
                        cursor: "pointer",
                      }}
                    />
                  ))}
                </div>
              </div>
            </div>
            <div className="modal-actions">
              <button className="btn-cancel" onClick={() => setEditingCard(null)}>取消</button>
              <button className="btn-save" onClick={() => {
                if (editingCard) {
                  handleUpdateCard(editingCard.id, {
                    title: editingCard.title,
                    content: editingCard.content,
                    card_type: editingCard.card_type,
                    color: editingCard.color,
                  });
                  setEditingCard(null);
                }
              }}>保存</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
