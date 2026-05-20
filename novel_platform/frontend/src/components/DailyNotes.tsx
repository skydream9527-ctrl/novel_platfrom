import { useState, useEffect } from "react";
import client from "../api/client";

interface DailyNote {
  id: number;
  date: string;
  content: string;
  mood: string;
  word_count: number;
  created_at: string;
}

interface Props {
  taskId?: number;
}

const MOODS = [
  { key: "happy", label: "开心", icon: "😊" },
  { key: "neutral", label: "平静", icon: "😐" },
  { key: "sad", label: "难过", icon: "😢" },
  { key: "inspired", label: "灵感", icon: "💡" },
  { key: "tired", label: "疲惫", icon: "😴" },
  { key: "excited", label: "兴奋", icon: "🎉" },
];

export default function DailyNotes({ taskId }: Props) {
  const [notes, setNotes] = useState<DailyNote[]>([]);
  const [todayNote, setTodayNote] = useState<DailyNote | null>(null);
  const [content, setContent] = useState("");
  const [mood, setMood] = useState("");
  const [loading, setLoading] = useState(false);
  const [selectedDate, setSelectedDate] = useState<string | null>(null);

  const today = new Date().toISOString().split("T")[0];

  useEffect(() => {
    loadNotes();
  }, []);

  const loadNotes = async () => {
    try {
      const res = await client.get("/daily-notes/");
      setNotes(res.data);
      const today = res.data.find((n: DailyNote) => n.date === new Date().toISOString().split("T")[0]);
      if (today) {
        setTodayNote(today);
        setContent(today.content);
        setMood(today.mood);
      }
    } catch {
      setNotes([]);
    }
  };

  const saveNote = async () => {
    setLoading(true);
    try {
      if (todayNote) {
        await client.patch(`/daily-notes/${todayNote.id}`, { content, mood });
      } else {
        const res = await client.post("/daily-notes/", { content, mood, date: today });
        setTodayNote(res.data);
      }
      loadNotes();
    } catch {
      alert("保存失败");
    } finally {
      setLoading(false);
    }
  };

  const getWeekDates = () => {
    const dates = [];
    const now = new Date();
    for (let i = 6; i >= 0; i--) {
      const d = new Date(now);
      d.setDate(d.getDate() - i);
      dates.push(d.toISOString().split("T")[0]);
    }
    return dates;
  };

  const getNoteForDate = (date: string) => notes.find((n) => n.date === date);

  return (
    <div style={{ padding: 16, maxWidth: 800, margin: "0 auto" }}>
      <h2 style={{ marginBottom: 24 }}>每日笔记</h2>

      {/* Week overview */}
      <div style={{ display: "flex", gap: 8, marginBottom: 24 }}>
        {getWeekDates().map((date) => {
          const note = getNoteForDate(date);
          const isToday = date === today;
          const isSelected = date === selectedDate;
          return (
            <div
              key={date}
              onClick={() => {
                setSelectedDate(date);
                if (note) {
                  setContent(note.content);
                  setMood(note.mood);
                } else {
                  setContent("");
                  setMood("");
                }
              }}
              style={{
                flex: 1,
                padding: 12,
                background: isToday ? "var(--color-primary)" : isSelected ? "var(--color-primary-light)" : "var(--color-bg-secondary)",
                color: isToday ? "white" : "var(--color-text)",
                borderRadius: 8,
                textAlign: "center",
                cursor: "pointer",
              }}
            >
              <div style={{ fontSize: 12, marginBottom: 4 }}>
                {new Date(date).toLocaleDateString("zh-CN", { weekday: "short" })}
              </div>
              <div style={{ fontSize: 18, fontWeight: 600 }}>
                {new Date(date).getDate()}
              </div>
              {note && (
                <div style={{ fontSize: 16, marginTop: 4 }}>
                  {MOODS.find((m) => m.key === note.mood)?.icon || ""}
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Editor */}
      <div style={{ background: "var(--color-bg-secondary)", borderRadius: 12, padding: 24 }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
          <h3 style={{ margin: 0 }}>
            {selectedDate || today}
            {selectedDate === today || !selectedDate ? " (今天)" : ""}
          </h3>
          <div style={{ display: "flex", gap: 8 }}>
            {MOODS.map((m) => (
              <button
                key={m.key}
                onClick={() => setMood(m.key)}
                style={{
                  background: mood === m.key ? "var(--color-primary)" : "transparent",
                  border: "none",
                  borderRadius: 4,
                  padding: "4px 8px",
                  cursor: "pointer",
                  fontSize: 16,
                }}
                title={m.label}
              >
                {m.icon}
              </button>
            ))}
          </div>
        </div>

        <textarea
          value={content}
          onChange={(e) => setContent(e.target.value)}
          placeholder="今天写了什么？有什么灵感？记录下来..."
          style={{
            width: "100%",
            minHeight: 200,
            padding: 16,
            borderRadius: 8,
            border: "1px solid var(--color-border)",
            background: "var(--color-bg)",
            fontSize: 14,
            lineHeight: 1.8,
            resize: "vertical",
          }}
        />

        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginTop: 12 }}>
          <span style={{ fontSize: 13, color: "var(--color-text-secondary)" }}>
            {content.length} 字
          </span>
          <button className="btn-save" onClick={saveNote} disabled={loading}>
            {loading ? "保存中..." : "保存"}
          </button>
        </div>
      </div>

      {/* History */}
      {notes.length > 0 && (
        <div style={{ marginTop: 32 }}>
          <h3 style={{ marginBottom: 16 }}>历史笔记</h3>
          <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
            {notes.slice(0, 10).map((note) => (
              <div
                key={note.id}
                onClick={() => {
                  setSelectedDate(note.date);
                  setContent(note.content);
                  setMood(note.mood);
                }}
                style={{
                  padding: 16,
                  background: "var(--color-bg-secondary)",
                  borderRadius: 8,
                  cursor: "pointer",
                }}
              >
                <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 8 }}>
                  <span style={{ fontWeight: 600 }}>
                    {MOODS.find((m) => m.key === note.mood)?.icon} {note.date}
                  </span>
                  <span style={{ fontSize: 13, color: "var(--color-text-secondary)" }}>
                    {note.word_count} 字
                  </span>
                </div>
                <div style={{ fontSize: 13, color: "var(--color-text-secondary)", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                  {note.content.slice(0, 100)}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
