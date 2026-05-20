import { useEffect, useState, useRef, useCallback, useMemo } from "react";
import { useParams, useNavigate } from "react-router-dom";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import client from "../api/client";
import { TYPE_LABELS } from "../constants";
import "./WorkspacePage.css";

interface Chapter {
  id: number;
  title: string;
  content: string;
  order_index: number;
  version: number;
  updated_at: string;
}

interface TaskDetail {
  id: number;
  title: string;
  type: string;
  description: string;
  directory_path: string | null;
  chapters: Chapter[];
  conversation_id: number;
}

interface ConversationItem {
  id: number;
  title: string;
  created_at: string;
}

interface Message {
  id?: number;
  role: "user" | "assistant" | "system";
  content: string;
  created_at?: string;
}

interface SourceItem {
  id: number;
  name: string;
  type: string;
  word_count: number;
  usage_count?: number;
  summary?: string;
  keywords?: string;
  created_at: string;
}

interface SearchResult {
  type: string;
  id: number;
  title: string;
  snippet: string;
  field: string;
}

interface VersionItem {
  id: number;
  version: number;
  title: string;
  created_at: string;
}

interface CharacterItem {
  id: number;
  name: string;
  role: string;
  appearance: string;
  personality: string;
  backstory: string;
  relationships: string;
}

interface NoteItem {
  id: number;
  title: string;
  content: string;
  category_id: number | null;
  created_at: string;
  updated_at: string;
}

interface CategoryItem {
  id: number;
  name: string;
  icon: string;
  sort_order: number;
}

interface ToolCallState {
  call_id: string;
  tool: string;
  label: string;
  args: Record<string, unknown>;
  status: "running" | "success" | "error";
  result?: Record<string, unknown>;
}

const SOURCE_ICONS: Record<string, string> = {
  text: "📝",
  file: "📄",
  url: "🔗",
  chapter: "📖",
};

const AI_ACTIONS = [
  { key: "continue", label: "续写", icon: "✍️" },
  { key: "rewrite", label: "改写", icon: "🔄" },
  { key: "expand", label: "扩写", icon: "📖" },
  { key: "shorten", label: "缩写", icon: "✂️" },
  { key: "polish", label: "润色", icon: "✨" },
  { key: "dialogue", label: "生成对话", icon: "💬" },
  { key: "translate_en", label: "翻译英文", icon: "🇬🇧" },
  { key: "translate_ja", label: "翻译日文", icon: "🇯🇵" },
];

const AI_GENERATE_TYPES = [
  { key: "outline", label: "故事大纲", icon: "📋" },
  { key: "character_map", label: "角色关系", icon: "🕸️" },
  { key: "timeline", label: "时间线", icon: "📅" },
  { key: "faq", label: "FAQ", icon: "❓" },
  { key: "chapter_summary", label: "章节摘要", icon: "📝" },
];

export default function WorkspacePage() {
  const { taskId } = useParams<{ taskId: string }>();
  const navigate = useNavigate();
  const [task, setTask] = useState<TaskDetail | null>(null);
  const [chapters, setChapters] = useState<Chapter[]>([]);
  const [activeChapter, setActiveChapter] = useState<Chapter | null>(null);
  const [editContent, setEditContent] = useState("");
  const [editTitle, setEditTitle] = useState("");
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [streaming, setStreaming] = useState(false);
  const [streamContent, setStreamContent] = useState("");
  const wsRef = useRef<WebSocket | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const editorRef = useRef<HTMLTextAreaElement>(null);

  const [sidebarTab, setSidebarTab] = useState<"chapters" | "sources" | "characters" | "notes">("chapters");

  const [sources, setSources] = useState<SourceItem[]>([]);
  const [showSourceModal, setShowSourceModal] = useState(false);
  const [sourceImportTab, setSourceImportTab] = useState<"text" | "url" | "file">("text");
  const [sourceName, setSourceName] = useState("");
  const [sourceContent, setSourceContent] = useState("");
  const [sourceUrl, setSourceUrl] = useState("");

  const [showVersionModal, setShowVersionModal] = useState(false);
  const [versions, setVersions] = useState<VersionItem[]>([]);

  const [summary, setSummary] = useState("");
  const [summaryLoading, setSummaryLoading] = useState(false);

  const [searchQuery, setSearchQuery] = useState("");
  const searchRef = useRef<HTMLInputElement>(null);

  const [showExportModal, setShowExportModal] = useState(false);

  const [showAiMenu, setShowAiMenu] = useState(false);
  const [aiLoading, setAiLoading] = useState(false);

  const [characters, setCharacters] = useState<CharacterItem[]>([]);
  const [showCharModal, setShowCharModal] = useState(false);
  const [editingChar, setEditingChar] = useState<CharacterItem | null>(null);
  const [charName, setCharName] = useState("");
  const [charRole, setCharRole] = useState("");
  const [charAppearance, setCharAppearance] = useState("");
  const [charPersonality, setCharPersonality] = useState("");
  const [charBackstory, setCharBackstory] = useState("");
  const [charRelationships, setCharRelationships] = useState("");

  const [notes, setNotes] = useState<NoteItem[]>([]);
  const [showNoteModal, setShowNoteModal] = useState(false);
  const [editingNote, setEditingNote] = useState<NoteItem | null>(null);
  const [noteTitle, setNoteTitle] = useState("");
  const [noteContent, setNoteContent] = useState("");
  const [noteCategoryId, setNoteCategoryId] = useState<number | null>(null);

  const [categories, setCategories] = useState<CategoryItem[]>([]);
  const [expandedCats, setExpandedCats] = useState<Set<number>>(new Set());
  const [showNewCatModal, setShowNewCatModal] = useState(false);
  const [newCatName, setNewCatName] = useState("");
  const [newCatIcon, setNewCatIcon] = useState("📁");

  const [showAiSaveModal, setShowAiSaveModal] = useState(false);
  const [aiSaveContent, setAiSaveContent] = useState("");
  const [aiSaveTitle, setAiSaveTitle] = useState("");
  const [aiSaveCategoryId, setAiSaveCategoryId] = useState<number | null>(null);
  const [aiSaveToast, setAiSaveToast] = useState("");

  const [sourceFile, setSourceFile] = useState<File | null>(null);
  const [citationPopover, setCitationPopover] = useState<{ text: string; x: number; y: number } | null>(null);
  const [showSourceDetail, setShowSourceDetail] = useState<SourceItem | null>(null);
  const [sourceDetailContent, setSourceDetailContent] = useState<string>("");
  const [showGenerateMenu, setShowGenerateMenu] = useState(false);
  const [generateLoading, setGenerateLoading] = useState(false);
  const [generateResult, setGenerateResult] = useState("");
  const [showGenerateModal, setShowGenerateModal] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const [toolCalls, setToolCalls] = useState<ToolCallState[]>([]);
  const [searchResults, setSearchResults] = useState<SearchResult[]>([]);
  const [searchLoading, setSearchLoading] = useState(false);
  const [showSearchPanel, setShowSearchPanel] = useState(false);
  const [recommendResult, setRecommendResult] = useState("");
  const [showRecommendModal, setShowRecommendModal] = useState(false);
  const [recommendLoading, setRecommendLoading] = useState(false);
  const [chapterView, setChapterView] = useState<"list" | "timeline" | "outline">("list");
  const [showGraphModal, setShowGraphModal] = useState(false);
  const [chapterOutline, setChapterOutline] = useState<{ level: number; title: string; line: number }[]>([]);
  const [showStatsModal, setShowStatsModal] = useState(false);
  const [writingGoal, setWritingGoal] = useState<number>(() => {
    const saved = localStorage.getItem("writingGoal");
    return saved ? parseInt(saved) : 1000;
  });
  const [dailyWordCount, setDailyWordCount] = useState<number>(0);
  const [showReminder, setShowReminder] = useState(false);
  const [reminderMessage, setReminderMessage] = useState("");
  const [showDiffModal, setShowDiffModal] = useState(false);
  const [diffVersion1, setDiffVersion1] = useState<number | null>(null);
  const [diffVersion2, setDiffVersion2] = useState<number | null>(null);
  const [diffContent, setDiffContent] = useState<{ v1: string; v2: string } | null>(null);

  const [availableModels, setAvailableModels] = useState<string[]>([]);
  const [selectedModel, setSelectedModel] = useState<string>("");
  const [conversations, setConversations] = useState<ConversationItem[]>([]);
  const [activeConversationId, setActiveConversationId] = useState<number | null>(null);
  const [showConversationList, setShowConversationList] = useState(false);

  useEffect(() => {
    if (!taskId) return;
    client.get(`/tasks/${taskId}`).then((res) => {
      setTask(res.data);
      if (res.data.chapters.length > 0) {
        loadChapter(res.data.chapters[0].id);
      }
    });
    client.get(`/chapters/by-task/${taskId}`).then((res) => setChapters(res.data));
    client.get(`/sources/by-task/${taskId}`).then((res) => setSources(res.data));
    client.get(`/characters/by-task/${taskId}`).then((res) => setCharacters(res.data));
    client.get(`/notes/by-task/${taskId}`).then((res) => setNotes(res.data));
    client.get(`/categories/by-task/${taskId}`).then((res) => {
      setCategories(res.data);
      if (res.data.length > 0) setExpandedCats(new Set([res.data[0].id]));
    });
    client.get("/ai/models").then((res) => {
      setAvailableModels(res.data.models);
      setSelectedModel(res.data.default);
    });
    // Load conversations
    client.get(`/conversations/by-task/${taskId}`).then((res) => {
      setConversations(res.data);
      if (res.data.length > 0) {
        setActiveConversationId(res.data[0].id);
      }
    });
  }, [taskId]);

  const refreshData = () => {
    if (!taskId) return;
    client.get(`/chapters/by-task/${taskId}`).then((res) => setChapters(res.data));
    client.get(`/characters/by-task/${taskId}`).then((res) => setCharacters(res.data));
    client.get(`/notes/by-task/${taskId}`).then((res) => setNotes(res.data));
    client.get(`/sources/by-task/${taskId}`).then((res) => setSources(res.data));
  };

  useEffect(() => {
    if (!activeConversationId) return;
    client.get(`/conversations/${activeConversationId}/messages`).then((res) => setMessages(res.data));
  }, [activeConversationId]);

  const createConversation = async () => {
    if (!taskId) return;
    const res = await client.post("/conversations/", { task_id: Number(taskId), title: `对话 ${conversations.length + 1}` });
    setConversations((prev) => [{ id: res.data.id, title: res.data.title, created_at: res.data.created_at }, ...prev]);
    setActiveConversationId(res.data.id);
    setMessages([]);
    setShowConversationList(false);
  };

  const deleteConversation = async (convId: number) => {
    if (!confirm("确认删除此对话？")) return;
    await client.delete(`/conversations/${convId}`);
    setConversations((prev) => prev.filter((c) => c.id !== convId));
    if (activeConversationId === convId) {
      const remaining = conversations.filter((c) => c.id !== convId);
      if (remaining.length > 0) {
        setActiveConversationId(remaining[0].id);
      } else {
        setActiveConversationId(null);
        setMessages([]);
      }
    }
  };

  const renameConversation = async (convId: number, newTitle: string) => {
    await client.patch(`/conversations/${convId}`, { title: newTitle });
    setConversations((prev) => prev.map((c) => (c.id === convId ? { ...c, title: newTitle } : c)));
  };

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, streamContent]);

  const loadChapter = async (chapterId: number) => {
    const res = await client.get(`/chapters/${chapterId}`);
    setActiveChapter(res.data);
    setEditContent(res.data.content);
    setEditTitle(res.data.title);
    setSummary("");
  };

  const saveChapter = async () => {
    if (!activeChapter) return;
    await client.patch(`/chapters/${activeChapter.id}`, {
      title: editTitle,
      content: editContent,
    });
    const res = await client.get(`/chapters/by-task/${taskId}`);
    setChapters(res.data);
  };

  // Auto-save with debounce
  const autoSaveTimerRef = useRef<NodeJS.Timeout | null>(null);
  const [autoSaveStatus, setAutoSaveStatus] = useState<"idle" | "saving" | "saved" | "error">("idle");

  const triggerAutoSave = useCallback(() => {
    if (!activeChapter) return;
    if (autoSaveTimerRef.current) {
      clearTimeout(autoSaveTimerRef.current);
    }
    setAutoSaveStatus("idle");
    autoSaveTimerRef.current = setTimeout(async () => {
      setAutoSaveStatus("saving");
      try {
        await client.patch(`/chapters/${activeChapter.id}`, {
          title: editTitle,
          content: editContent,
        });
        setAutoSaveStatus("saved");
        setTimeout(() => setAutoSaveStatus("idle"), 2000);
      } catch {
        setAutoSaveStatus("error");
        setTimeout(() => setAutoSaveStatus("idle"), 3000);
      }
    }, 1500); // 1.5 second debounce
  }, [activeChapter, editTitle, editContent]);

  // Cleanup timer on unmount
  useEffect(() => {
    return () => {
      if (autoSaveTimerRef.current) {
        clearTimeout(autoSaveTimerRef.current);
      }
    };
  }, []);

  const addChapter = async () => {
    if (!taskId) return;
    const res = await client.post("/chapters/", {
      task_id: Number(taskId),
      title: `第${chapters.length + 1}章`,
    });
    const chapRes = await client.get(`/chapters/by-task/${taskId}`);
    setChapters(chapRes.data);
    loadChapter(res.data.id);
  };

  const handleAddSource = async () => {
    if (!taskId) return;
    let sourceId: number | null = null;
    if (sourceImportTab === "file" && sourceFile) {
      const formData = new FormData();
      formData.append("task_id", String(taskId));
      formData.append("name", sourceName || sourceFile.name.replace(/\.[^.]+$/, ""));
      formData.append("file", sourceFile);
      const res = await client.post("/sources/upload", formData, { headers: { "Content-Type": "multipart/form-data" } });
      sourceId = res.data.id;
    } else if (sourceImportTab === "url") {
      const res = await client.post("/sources/fetch-url", { task_id: Number(taskId), url: sourceUrl, name: sourceName || sourceUrl });
      sourceId = res.data.id;
    } else {
      const res = await client.post("/sources/", { task_id: Number(taskId), name: sourceName || "未命名素材", type: "text", content: sourceContent });
      sourceId = res.data.id;
    }
    setShowSourceModal(false);
    setSourceName("");
    setSourceContent("");
    setSourceUrl("");
    setSourceFile(null);
    const res = await client.get(`/sources/by-task/${taskId}`);
    setSources(res.data);
    // Auto-generate summary for the new source
    if (sourceId) {
      try {
        await client.post("/ai/source-summary", { source_id: sourceId });
        const updatedRes = await client.get(`/sources/by-task/${taskId}`);
        setSources(updatedRes.data);
      } catch {
        // Summary generation failed silently
      }
    }
  };

  const handleDeleteSource = async (sourceId: number) => {
    await client.delete(`/sources/${sourceId}`);
    const res = await client.get(`/sources/by-task/${taskId}`);
    setSources(res.data);
  };

  const openVersionHistory = async () => {
    if (!activeChapter) return;
    const res = await client.get(`/chapters/${activeChapter.id}/versions`);
    setVersions(res.data);
    setShowVersionModal(true);
  };

  const restoreVersion = async (version: number) => {
    if (!activeChapter) return;
    await client.post(`/chapters/${activeChapter.id}/restore/${version}`);
    setShowVersionModal(false);
    loadChapter(activeChapter.id);
    const res = await client.get(`/chapters/by-task/${taskId}`);
    setChapters(res.data);
  };

  const openDiffView = async (v1: number, v2: number) => {
    if (!activeChapter) return;
    setDiffVersion1(v1);
    setDiffVersion2(v2);
    try {
      const [res1, res2] = await Promise.all([
        client.get(`/chapters/${activeChapter.id}/versions/${v1}`),
        client.get(`/chapters/${activeChapter.id}/versions/${v2}`),
      ]);
      setDiffContent({ v1: res1.data.content, v2: res2.data.content });
      setShowDiffModal(true);
    } catch {
      alert("加载版本内容失败");
    }
  };

  const renderDiff = (text1: string, text2: string) => {
    const lines1 = text1.split("\n");
    const lines2 = text2.split("\n");
    const maxLen = Math.max(lines1.length, lines2.length);
    const result: { line1: string; line2: string; changed: boolean }[] = [];

    for (let i = 0; i < maxLen; i++) {
      const l1 = lines1[i] || "";
      const l2 = lines2[i] || "";
      result.push({ line1: l1, line2: l2, changed: l1 !== l2 });
    }
    return result;
  };

  // Writing statistics
  const totalWordCount = useMemo(() => {
    return chapters.reduce((sum, ch) => sum + (ch.content?.length || 0), 0);
  }, [chapters]);

  const chapterStats = useMemo(() => {
    return chapters.map((ch) => ({
      id: ch.id,
      title: ch.title,
      wordCount: ch.content?.length || 0,
      version: ch.version,
    }));
  }, [chapters]);

  const goalProgress = useMemo(() => {
    return Math.min(100, Math.round((dailyWordCount / writingGoal) * 100));
  }, [dailyWordCount, writingGoal]);

  // Track daily word count and check reminders
  useEffect(() => {
    const today = new Date().toISOString().split("T")[0];
    const savedDate = localStorage.getItem("lastWritingDate");
    const savedCount = localStorage.getItem("dailyWordCount");

    if (savedDate === today && savedCount) {
      setDailyWordCount(parseInt(savedCount));
    } else {
      setDailyWordCount(0);
      localStorage.setItem("lastWritingDate", today);
      localStorage.setItem("dailyWordCount", "0");
    }

    // Check if we should show a reminder
    const lastReminder = localStorage.getItem("lastReminderDate");
    const reminderEnabled = localStorage.getItem("reminderEnabled") !== "false";

    if (reminderEnabled && lastReminder !== today) {
      const hour = new Date().getHours();
      // Show reminder in the evening if no writing done today
      if (hour >= 18 && (!savedCount || parseInt(savedCount) === 0)) {
        setReminderMessage("今天还没有写作哦！坚持每天写作，让创意不断涌现。");
        setShowReminder(true);
        localStorage.setItem("lastReminderDate", today);
      }
    }
  }, []);

  // Update daily word count when content changes
  useEffect(() => {
    if (activeChapter) {
      const originalLength = activeChapter.content?.length || 0;
      const currentLength = editContent.length;
      const diff = currentLength - originalLength;
      if (diff > 0) {
        setDailyWordCount((prev) => {
          const newCount = prev + diff;
          localStorage.setItem("dailyWordCount", String(newCount));
          return newCount;
        });
      }
    }
  }, [editContent]);

  const generateSummary = async () => {
    if (!activeChapter) return;
    setSummaryLoading(true);
    try {
      const res = await client.post("/summaries/chapter", { chapter_id: activeChapter.id });
      setSummary(res.data.summary);
    } catch {
      setSummary("摘要生成失败");
    } finally {
      setSummaryLoading(false);
    }
  };

  const handleAiAction = async (action: string) => {
    const textarea = editorRef.current;
    if (!textarea) return;
    const start = textarea.selectionStart;
    const end = textarea.selectionEnd;
    const selectedText = start !== end ? editContent.substring(start, end) : editContent.substring(0, 500);
    if (!selectedText.trim()) {
      alert("请先选中文本");
      return;
    }
    setShowAiMenu(false);
    setAiLoading(true);
    try {
      const res = await client.post("/ai/actions", {
        action,
        text: selectedText,
        chapter_id: activeChapter?.id,
        task_id: Number(taskId),
      });
      const result = res.data.result;
      if (start !== end) {
        const newContent = editContent.substring(0, start) + result + editContent.substring(end);
        setEditContent(newContent);
      } else {
        setEditContent(editContent + "\n\n" + result);
      }
    } catch {
      alert("AI 操作失败");
    } finally {
      setAiLoading(false);
    }
  };

  const openNewChar = () => {
    setEditingChar(null);
    setCharName("");
    setCharRole("");
    setCharAppearance("");
    setCharPersonality("");
    setCharBackstory("");
    setCharRelationships("");
    setShowCharModal(true);
  };

  const openEditChar = (c: CharacterItem) => {
    setEditingChar(c);
    setCharName(c.name);
    setCharRole(c.role);
    setCharAppearance(c.appearance);
    setCharPersonality(c.personality);
    setCharBackstory(c.backstory);
    setCharRelationships(c.relationships);
    setShowCharModal(true);
  };

  const saveCharacter = async () => {
    if (!charName.trim()) return;
    if (editingChar) {
      await client.patch(`/characters/${editingChar.id}`, {
        name: charName, role: charRole, appearance: charAppearance,
        personality: charPersonality, backstory: charBackstory, relationships: charRelationships,
      });
    } else {
      await client.post("/characters/", {
        task_id: Number(taskId), name: charName, role: charRole,
        appearance: charAppearance, personality: charPersonality,
        backstory: charBackstory, relationships: charRelationships,
      });
    }
    setShowCharModal(false);
    const res = await client.get(`/characters/by-task/${taskId}`);
    setCharacters(res.data);
  };

  const deleteCharacter = async (charId: number) => {
    if (!confirm("确认删除此角色？")) return;
    await client.delete(`/characters/${charId}`);
    const res = await client.get(`/characters/by-task/${taskId}`);
    setCharacters(res.data);
  };

  const openNewNote = (catId?: number) => {
    setEditingNote(null);
    setNoteTitle("");
    setNoteContent("");
    setNoteCategoryId(catId ?? null);
    setShowNoteModal(true);
  };

  const openEditNote = (n: NoteItem) => {
    client.get(`/notes/${n.id}`).then((res) => {
      setEditingNote(n);
      setNoteTitle(res.data.title);
      setNoteContent(res.data.content);
      setNoteCategoryId(res.data.category_id);
      setShowNoteModal(true);
    });
  };

  const saveNote = async () => {
    if (!noteTitle.trim()) return;
    if (editingNote) {
      await client.patch(`/notes/${editingNote.id}`, { title: noteTitle, content: noteContent, category_id: noteCategoryId });
    } else {
      await client.post("/notes/", { task_id: Number(taskId), title: noteTitle, content: noteContent, category_id: noteCategoryId });
    }
    setShowNoteModal(false);
    const res = await client.get(`/notes/by-task/${taskId}`);
    setNotes(res.data);
  };

  const deleteNote = async (noteId: number) => {
    if (!confirm("确认删除此文档？")) return;
    await client.delete(`/notes/${noteId}`);
    const res = await client.get(`/notes/by-task/${taskId}`);
    setNotes(res.data);
  };

  const createCategory = async () => {
    if (!newCatName.trim()) return;
    await client.post("/categories/", { task_id: Number(taskId), name: newCatName.trim(), icon: newCatIcon });
    setShowNewCatModal(false);
    setNewCatName("");
    setNewCatIcon("📁");
    const res = await client.get(`/categories/by-task/${taskId}`);
    setCategories(res.data);
  };

  const deleteCategory = async (catId: number) => {
    if (!confirm("确认删除此分类及其所有文档？")) return;
    await client.delete(`/categories/${catId}`);
    const res = await client.get(`/categories/by-task/${taskId}`);
    setCategories(res.data);
    const notesRes = await client.get(`/notes/by-task/${taskId}`);
    setNotes(notesRes.data);
  };

  const toggleCatExpanded = (catId: number) => {
    setExpandedCats((prev) => {
      const next = new Set(prev);
      if (next.has(catId)) next.delete(catId);
      else next.add(catId);
      return next;
    });
  };

  // AI save to file
  const openAiSave = (content: string) => {
    const now = new Date();
    const ts = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, "0")}-${String(now.getDate()).padStart(2, "0")} ${String(now.getHours()).padStart(2, "0")}:${String(now.getMinutes()).padStart(2, "0")}`;
    setAiSaveContent(content);
    setAiSaveTitle(`AI 回复 - ${ts}`);
    setAiSaveCategoryId(categories.length > 0 ? categories[0].id : null);
    setShowAiSaveModal(true);
  };

  const confirmAiSave = async () => {
    if (!aiSaveTitle.trim()) return;
    await client.post("/notes/", {
      task_id: Number(taskId),
      title: aiSaveTitle.trim(),
      content: aiSaveContent,
      category_id: aiSaveCategoryId,
    });
    setShowAiSaveModal(false);
    setAiSaveToast("已保存到文件");
    setTimeout(() => setAiSaveToast(""), 3000);
    const res = await client.get(`/notes/by-task/${taskId}`);
    setNotes(res.data);
  };

  const filteredChapters = searchQuery.trim()
    ? chapters.filter(
        (ch) =>
          ch.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
          ch.content.toLowerCase().includes(searchQuery.toLowerCase())
      )
    : chapters;

  // Extract headings from chapter content for outline view
  const extractOutline = (content: string) => {
    const lines = content.split("\n");
    const headings: { level: number; title: string; line: number }[] = [];
    lines.forEach((line, index) => {
      const match = line.match(/^(#{1,6})\s+(.+)$/);
      if (match) {
        headings.push({
          level: match[1].length,
          title: match[2].trim(),
          line: index + 1,
        });
      }
    });
    return headings;
  };

  // Update outline when active chapter changes
  useEffect(() => {
    if (activeChapter?.content) {
      setChapterOutline(extractOutline(activeChapter.content));
    } else {
      setChapterOutline([]);
    }
  }, [activeChapter?.content]);

  // Trigger auto-save when content or title changes
  useEffect(() => {
    if (activeChapter && (editContent !== activeChapter.content || editTitle !== activeChapter.title)) {
      triggerAutoSave();
    }
  }, [editContent, editTitle, activeChapter, triggerAutoSave]);

  const downloadFile = (filename: string, content: string, mimeType: string) => {
    const blob = new Blob([content], { type: mimeType });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    a.click();
    URL.revokeObjectURL(url);
  };

  const exportCurrentChapter = (format: "md" | "txt") => {
    if (!activeChapter) return;
    const ext = format === "md" ? "md" : "txt";
    const content = format === "md" ? editContent : editContent.replace(/[#*_`~\[\]]/g, "");
    downloadFile(`${editTitle}.${ext}`, content, "text/plain;charset=utf-8");
  };

  const exportAllChapters = (format: "md" | "txt") => {
    if (!task) return;
    const ext = format === "md" ? "md" : "txt";
    const allContent = chapters
      .map((ch) => {
        const content = format === "txt" ? ch.content.replace(/[#*_`~\[\]]/g, "") : ch.content;
        return `# ${ch.title}\n\n${content}`;
      })
      .join("\n\n---\n\n");
    downloadFile(`${task.title}.${ext}`, allContent, "text/plain;charset=utf-8");
  };

  const exportAsPdf = () => {
    if (!activeChapter) return;
    const printWindow = window.open("", "_blank");
    if (!printWindow) return;
    printWindow.document.write(`
      <!DOCTYPE html><html><head><meta charset="utf-8"><title>${editTitle}</title>
      <style>body{font-family:"Noto Sans SC",sans-serif;max-width:700px;margin:40px auto;padding:0 20px;line-height:1.8;color:#1f1f1f}
      h1{font-size:24px;margin-bottom:16px}h2{font-size:20px;margin:24px 0 12px}h3{font-size:16px;margin:20px 0 8px}
      p{margin-bottom:12px}hr{border:none;border-top:1px solid #ddd;margin:24px 0}</style></head>
      <body><h1>${editTitle}</h1><div id="content"></div>
      <script>document.getElementById("content").innerHTML=${JSON.stringify(editContent)}
        .replace(/^### (.+)$/gm,"<h3>$1</h3>").replace(/^## (.+)$/gm,"<h2>$1</h2>")
        .replace(/^# (.+)$/gm,"<h1>$1</h1>").replace(/^---$/gm,"<hr>")
        .replace(/\\*\\*(.+?)\\*\\*/g,"<strong>$1</strong>").replace(/\\*(.+?)\\**/g,"<em>$1</em>")
        .replace(/\\n/g,"<br>");</script>
      <script>window.print();window.onafterprint=()=>window.close();</script>
      </body></html>`);
    printWindow.document.close();
  };

  const exportCurrentChapterDocx = async () => {
    if (!activeChapter) return;
    try {
      const response = await client.get(`/chapters/${activeChapter.id}/export/docx`, { responseType: "blob" });
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const a = document.createElement("a");
      a.href = url;
      a.download = `${editTitle}.docx`;
      a.click();
      window.URL.revokeObjectURL(url);
    } catch {
      alert("DOCX 导出失败");
    }
  };

  const exportAllChaptersDocx = async () => {
    if (!taskId) return;
    try {
      const response = await client.get(`/chapters/by-task/${taskId}/export/docx`, { responseType: "blob" });
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const a = document.createElement("a");
      a.href = url;
      a.download = `${task?.title || "全部章节"}.docx`;
      a.click();
      window.URL.revokeObjectURL(url);
    } catch {
      alert("DOCX 导出失败");
    }
  };

  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      const ctrl = e.ctrlKey || e.metaKey;

      // Ctrl+S — save
      if (ctrl && e.key === "s") {
        e.preventDefault();
        saveChapter();
        return;
      }

      // Ctrl+N — new chapter
      if (ctrl && e.key === "n") {
        e.preventDefault();
        addChapter();
        return;
      }

      // Ctrl+K — focus search
      if (ctrl && e.key === "k") {
        e.preventDefault();
        searchRef.current?.focus();
        setSidebarTab("chapters");
        return;
      }

      // Ctrl+Shift+E — export current chapter
      if (ctrl && e.shiftKey && e.key === "E") {
        e.preventDefault();
        exportCurrentChapter("md");
        return;
      }

      // Ctrl+Shift+A — export all chapters
      if (ctrl && e.shiftKey && e.key === "A") {
        e.preventDefault();
        exportAllChapters("md");
        return;
      }

      // Esc — close modals
      if (e.key === "Escape") {
        setShowSourceModal(false);
        setShowVersionModal(false);
        setShowExportModal(false);
      }
    };

    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [editContent, editTitle, activeChapter, chapters, task, streaming]);

  const connectWs = useCallback(() => {
    if (!activeConversationId) return;
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const ws = new WebSocket(`${protocol}//${window.location.host}/api/v1/ws/conversations/${activeConversationId}`);

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.type === "start") {
        setStreaming(true);
        setStreamContent("");
        setToolCalls([]);
      } else if (data.type === "chunk") {
        setStreamContent((prev) => prev + data.content);
      } else if (data.type === "tool_call") {
        setToolCalls((prev) => [
          ...prev,
          { call_id: data.call_id, tool: data.tool, label: data.label, args: data.args, status: "running" },
        ]);
      } else if (data.type === "tool_result") {
        setToolCalls((prev) =>
          prev.map((tc) =>
            tc.call_id === data.call_id
              ? { ...tc, status: data.success ? "success" : "error", result: data.result }
              : tc
          )
        );
        if (data.success) {
          refreshData();
        }
      } else if (data.type === "done") {
        setStreaming(false);
        setMessages((prev) => [...prev, { role: "assistant", content: data.content }]);
        setStreamContent("");
        setToolCalls([]);
      } else if (data.type === "suggestions") {
        setSuggestions(data.suggestions);
      }
    };

    ws.onclose = () => {
      setTimeout(() => connectWs(), 3000);
    };

    wsRef.current = ws;
  }, [task?.conversation_id]);

  useEffect(() => {
    connectWs();
    return () => { wsRef.current?.close(); };
  }, [connectWs, activeConversationId]);

  const sendMessage = () => {
    if (!input.trim() || !wsRef.current || streaming) return;
    const content = input.trim();
    setMessages((prev) => [...prev, { role: "user", content }]);
    wsRef.current.send(JSON.stringify({ content, model: selectedModel || undefined }));
    setInput("");
    setSuggestions([]);
    setToolCalls([]);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  // F5: TTS
  const toggleSpeaking = () => {
    if (isSpeaking) { speechSynthesis.cancel(); setIsSpeaking(false); }
    else if (editContent) {
      const u = new SpeechSynthesisUtterance(editContent.replace(/[#*_`~\[\]]/g, ""));
      u.lang = "zh-CN"; u.onend = () => setIsSpeaking(false);
      speechSynthesis.speak(u); setIsSpeaking(true);
    }
  };

  // F2: AI Generate
  const handleGenerate = async (type: string) => {
    setShowGenerateMenu(false); setGenerateLoading(true);
    try {
      const res = await client.post("/ai/generate", { task_id: Number(taskId), type });
      setGenerateResult(res.data.result); setShowGenerateModal(true);
    } catch { setGenerateResult("生成失败"); setShowGenerateModal(true); }
    finally { setGenerateLoading(false); }
  };

  // F7: Source recommendation
  const handleRecommendSources = async () => {
    setRecommendLoading(true);
    try {
      const res = await client.post("/ai/recommend-sources", { task_id: Number(taskId) });
      setRecommendResult(res.data.result); setShowRecommendModal(true);
    } catch { setRecommendResult("推荐失败"); setShowRecommendModal(true); }
    finally { setRecommendLoading(false); }
  };

  // F8: Global search
  const handleGlobalSearch = async (query: string) => {
    if (query.length < 2) { setSearchResults([]); setShowSearchPanel(false); return; }
    setSearchLoading(true); setShowSearchPanel(true);
    try {
      const res = await client.get(`/search?q=${encodeURIComponent(query)}&task_id=${taskId}`);
      setSearchResults(res.data);
    } catch { setSearchResults([]); }
    finally { setSearchLoading(false); }
  };

  // F1: Citation - improved to open source detail modal
  const handleCitationClick = async (e: React.MouseEvent, index: number) => {
    e.preventDefault();
    if (sources[index]) {
      setShowSourceDetail(sources[index]);
      try {
        const res = await client.get(`/sources/${sources[index].id}`);
        setSourceDetailContent(res.data.content || "");
      } catch {
        setSourceDetailContent("加载失败");
      }
    }
  };

  const renderWithCitations = (text: string) => {
    const parts = text.split(/(\[\d+\])/g);
    return parts.map((part, i) => {
      const m = part.match(/^\[(\d+)\]$/);
      if (m) {
        const idx = parseInt(m[1]) - 1;
        return <span key={i} className="msg-citation" onClick={(e) => handleCitationClick(e, idx)} title={sources[idx]?.name || ""}>[{m[1]}]</span>;
      }
      return <span key={i}>{part}</span>;
    });
  };

  if (!task) return <div className="loading">加载中...</div>;

  return (
    <div className="workspace">
      {/* Top bar */}
      <header className="ws-header">
        <button className="btn-back" onClick={() => navigate("/dashboard")}>← 返回</button>
        <h1>{task.title}</h1>
        {task.directory_path && (
          <span className="ws-dir" title={task.directory_path}>📁 {task.directory_path}</span>
        )}
        <span className="ws-type">{TYPE_LABELS[task.type] || task.type}</span>
      </header>

      <div className="ws-body">
        {/* Left: Sidebar with tabs */}
        <aside className="ws-sidebar">
          <div className="sidebar-tabs">
            <button className={sidebarTab === "chapters" ? "active" : ""} onClick={() => setSidebarTab("chapters")}>章节</button>
            <button className={sidebarTab === "sources" ? "active" : ""} onClick={() => setSidebarTab("sources")}>素材</button>
            <button className={sidebarTab === "characters" ? "active" : ""} onClick={() => setSidebarTab("characters")}>设定</button>
            <button className={sidebarTab === "notes" ? "active" : ""} onClick={() => setSidebarTab("notes")}>文档</button>
          </div>

          {sidebarTab === "chapters" && (
            <>
              <div className="sidebar-header">
                <h3>章节列表</h3>
                <div style={{ display: "flex", gap: 4 }}>
                  <button className={`btn-add ${chapterView === "list" ? "active" : ""}`} onClick={() => setChapterView("list")} title="列表" style={{ fontSize: 12, width: 28, height: 28 }}>☰</button>
                  <button className={`btn-add ${chapterView === "timeline" ? "active" : ""}`} onClick={() => setChapterView("timeline")} title="时间线" style={{ fontSize: 12, width: 28, height: 28 }}>⏳</button>
                  <button className={`btn-add ${chapterView === "outline" ? "active" : ""}`} onClick={() => setChapterView("outline")} title="大纲" style={{ fontSize: 12, width: 28, height: 28 }}>📋</button>
                  <button className="btn-add" onClick={addChapter}>+</button>
                </div>
              </div>
              <div className="sidebar-search">
                <input
                  ref={searchRef}
                  placeholder="搜索全部内容... (Ctrl+K)"
                  value={searchQuery}
                  onChange={(e) => { setSearchQuery(e.target.value); handleGlobalSearch(e.target.value); }}
                  onFocus={() => searchQuery.length >= 2 && setShowSearchPanel(true)}
                />
              </div>
              {showSearchPanel && searchResults.length > 0 && (
                <div className="search-results">
                  {searchLoading && <div className="search-loading">搜索中...</div>}
                  {searchResults.map((r, i) => (
                    <div key={i} className="search-result-item" onClick={() => {
                      if (r.type === "chapter") loadChapter(r.id);
                      setShowSearchPanel(false); setSearchQuery("");
                    }}>
                      <span className="search-type-icon">{r.type === "chapter" ? "📖" : r.type === "source" ? "📄" : r.type === "note" ? "📝" : "👤"}</span>
                      <div className="search-result-info">
                        <div className="search-result-title">{r.title}</div>
                        <div className="search-result-snippet">{r.snippet}</div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
              {chapterView === "list" ? (
                <div className="chapter-list">
                  {filteredChapters.map((ch) => (
                    <div key={ch.id} className={`chapter-item ${activeChapter?.id === ch.id ? "active" : ""}`} onClick={() => loadChapter(ch.id)}>
                      <span className="chapter-title">{ch.title}</span>
                      <span className="chapter-ver">v{ch.version}</span>
                    </div>
                  ))}
                  {filteredChapters.length === 0 && (
                    <div className="chapter-empty-msg">{searchQuery ? "无匹配章节" : "暂无章节，点击 + 创建"}</div>
                  )}
                </div>
              ) : chapterView === "timeline" ? (
                <div className="timeline-view">
                  {filteredChapters.map((ch) => (
                    <div key={ch.id} className={`timeline-item ${activeChapter?.id === ch.id ? "active" : ""}`} onClick={() => loadChapter(ch.id)}>
                      <div className="timeline-dot" />
                      <div className="timeline-content">
                        <div className="timeline-title">{ch.title}</div>
                        <div className="timeline-meta">v{ch.version} · {new Date(ch.updated_at).toLocaleDateString("zh-CN")}</div>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="outline-view" style={{ padding: "8px 0" }}>
                  {!activeChapter ? (
                    <div className="chapter-empty-msg">请先选择一个章节</div>
                  ) : chapterOutline.length === 0 ? (
                    <div className="chapter-empty-msg">当前章节无标题结构</div>
                  ) : (
                    <div className="outline-list">
                      {chapterOutline.map((item, i) => (
                        <div
                          key={i}
                          className="outline-item"
                          style={{
                            paddingLeft: `${(item.level - 1) * 16 + 8}px`,
                            padding: "6px 8px 6px `${(item.level - 1) * 16 + 8}px`",
                            cursor: "pointer",
                            fontSize: item.level === 1 ? 14 : 13,
                            fontWeight: item.level === 1 ? 600 : 400,
                            color: "var(--color-text)",
                            borderRadius: 4,
                          }}
                          onClick={() => {
                            // Scroll to heading in editor
                            const textarea = editorRef.current;
                            if (textarea) {
                              const lines = editContent.split("\n");
                              let charIndex = 0;
                              for (let j = 0; j < item.line - 1; j++) {
                                charIndex += lines[j].length + 1;
                              }
                              textarea.focus();
                              textarea.setSelectionRange(charIndex, charIndex + lines[item.line - 1].length);
                            }
                          }}
                        >
                          <span style={{ color: "var(--color-text-secondary)", marginRight: 8, fontSize: 11 }}>
                            {"#".repeat(item.level)}
                          </span>
                          {item.title}
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}
              {activeChapter && (
                <>
                  {summary && (
                    <div className="summary-panel">
                      <h4>AI 摘要</h4>
                      <div style={{ whiteSpace: "pre-wrap" }}>{summary}</div>
                    </div>
                  )}
                  <button className="btn-summary" onClick={generateSummary} disabled={summaryLoading}>
                    {summaryLoading ? "生成中..." : "✨ 生成摘要"}
                  </button>
                </>
              )}
            </>
          )}

          {sidebarTab === "sources" && (
            <>
              <div className="sidebar-header">
                <h3>素材列表</h3>
                <div style={{ display: "flex", gap: 4 }}>
                  <button className="btn-add" onClick={handleRecommendSources} disabled={recommendLoading} title="AI 推荐" style={{ fontSize: 12 }}>✨</button>
                  <button className="btn-add" onClick={() => setShowSourceModal(true)}>+</button>
                </div>
              </div>
              <div className="source-list">
                {sources.map((s) => (
                  <div key={s.id} className="source-item" onClick={() => { setShowSourceDetail(s); setSourceDetailContent(s.summary || ""); }} style={{ cursor: "pointer" }}>
                    <span className="source-icon">{SOURCE_ICONS[s.type] || "📄"}</span>
                    <div className="source-info">
                      <div className="source-name">{s.name}</div>
                      <div className="source-meta">{s.word_count} 字 {s.usage_count ? `· 引用 ${s.usage_count} 次` : ""}</div>
                      {s.summary && <div className="source-summary" style={{ fontSize: 12, color: "var(--color-text-secondary)", marginTop: 4, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{s.summary.slice(0, 60)}...</div>}
                    </div>
                    <button className="source-delete" onClick={(e) => { e.stopPropagation(); handleDeleteSource(s.id); }} title="删除">×</button>
                  </div>
                ))}
                {sources.length === 0 && (
                  <div className="source-empty">暂无素材，点击 + 导入</div>
                )}
              </div>
            </>
          )}

          {sidebarTab === "characters" && (
            <>
              <div className="sidebar-header">
                <h3>角色设定</h3>
                <div style={{ display: "flex", gap: 4 }}>
                  <button className="btn-add" onClick={() => setShowGraphModal(true)} title="关系图谱" style={{ fontSize: 12 }}>🕸️</button>
                  <button className="btn-add" onClick={openNewChar}>+</button>
                </div>
              </div>
              <div className="source-list">
                {characters.map((c) => (
                  <div key={c.id} className="source-item" onClick={() => openEditChar(c)} style={{ cursor: "pointer" }}>
                    <span className="source-icon">👤</span>
                    <div className="source-info">
                      <div className="source-name">{c.name}</div>
                      <div className="source-meta">{c.role || "未设角色"}</div>
                    </div>
                    <button className="source-delete" onClick={(e) => { e.stopPropagation(); deleteCharacter(c.id); }} title="删除">×</button>
                  </div>
                ))}
                {characters.length === 0 && (
                  <div className="source-empty">暂无角色，点击 + 创建</div>
                )}
              </div>
            </>
          )}

          {sidebarTab === "notes" && (
            <>
              <div className="sidebar-header">
                <h3>文档管理</h3>
                <div style={{ display: "flex", gap: 4 }}>
                  <button className="btn-add" onClick={() => setShowNewCatModal(true)} title="新建分类" style={{ fontSize: 12 }}>📁</button>
                  <button className="btn-add" onClick={() => openNewNote()}>+</button>
                </div>
              </div>
              <div className="category-tree">
                {categories.map((cat) => {
                  const catNotes = notes.filter((n) => n.category_id === cat.id);
                  const expanded = expandedCats.has(cat.id);
                  return (
                    <div key={cat.id} className="category-folder">
                      <div className="category-header" onClick={() => toggleCatExpanded(cat.id)}>
                        <span className="category-arrow">{expanded ? "▼" : "▶"}</span>
                        <span className="category-icon">{cat.icon}</span>
                        <span className="category-name">{cat.name}</span>
                        <span className="category-count">{catNotes.length}</span>
                        <button className="category-add" onClick={(e) => { e.stopPropagation(); openNewNote(cat.id); }} title="在此分类下新建">+</button>
                        <button className="category-del" onClick={(e) => { e.stopPropagation(); deleteCategory(cat.id); }} title="删除分类">×</button>
                      </div>
                      {expanded && (
                        <div className="category-docs">
                          {catNotes.map((n) => (
                            <div key={n.id} className="doc-item" onClick={() => openEditNote(n)}>
                              <span className="doc-icon">📄</span>
                              <span className="doc-title">{n.title}</span>
                              <button className="doc-delete" onClick={(e) => { e.stopPropagation(); deleteNote(n.id); }} title="删除">×</button>
                            </div>
                          ))}
                          {catNotes.length === 0 && <div className="doc-empty">暂无文档</div>}
                        </div>
                      )}
                    </div>
                  );
                })}
                {/* Uncategorized notes */}
                {(() => {
                  const uncategorized = notes.filter((n) => !n.category_id);
                  if (uncategorized.length === 0) return null;
                  return (
                    <div className="category-folder">
                      <div className="category-header" onClick={() => toggleCatExpanded(0)}>
                        <span className="category-arrow">{expandedCats.has(0) ? "▼" : "▶"}</span>
                        <span className="category-icon">📝</span>
                        <span className="category-name">未分类</span>
                        <span className="category-count">{uncategorized.length}</span>
                      </div>
                      {expandedCats.has(0) && (
                        <div className="category-docs">
                          {uncategorized.map((n) => (
                            <div key={n.id} className="doc-item" onClick={() => openEditNote(n)}>
                              <span className="doc-icon">📄</span>
                              <span className="doc-title">{n.title}</span>
                              <button className="doc-delete" onClick={(e) => { e.stopPropagation(); deleteNote(n.id); }} title="删除">×</button>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  );
                })()}
                {categories.length === 0 && notes.length === 0 && (
                  <div className="source-empty">暂无文档，点击 + 创建</div>
                )}
              </div>
            </>
          )}
        </aside>

        {/* Center: Editor */}
        <main className="ws-editor">
          {activeChapter ? (
            <>
              <div className="editor-toolbar">
                <input
                  className="editor-title-input"
                  value={editTitle}
                  onChange={(e) => setEditTitle(e.target.value)}
                  placeholder="章节标题"
                />
                <div style={{ position: "relative" }}>
                  <button
                    className="btn-history"
                    onClick={() => setShowAiMenu(!showAiMenu)}
                    disabled={aiLoading}
                    title="AI 操作"
                  >
                    {aiLoading ? "⏳ AI 处理中..." : "🤖 AI 操作"}
                  </button>
                  {showAiMenu && (
                    <div className="ai-dropdown">
                      {AI_ACTIONS.map((a) => (
                        <button key={a.key} className="ai-dropdown-item" onClick={() => handleAiAction(a.key)}>
                          <span>{a.icon}</span> {a.label}
                        </button>
                      ))}
                    </div>
                  )}
                </div>
                <div style={{ position: "relative" }}>
                  <button className="btn-history" onClick={() => setShowGenerateMenu(!showGenerateMenu)} disabled={generateLoading} title="AI 工具">
                    {generateLoading ? "⏳ 生成中..." : "🛠️ AI 工具"}
                  </button>
                  {showGenerateMenu && (
                    <div className="ai-dropdown">
                      {AI_GENERATE_TYPES.map((a) => (
                        <button key={a.key} className="ai-dropdown-item" onClick={() => handleGenerate(a.key)}>
                          <span>{a.icon}</span> {a.label}
                        </button>
                      ))}
                    </div>
                  )}
                </div>
                <button className="btn-history" onClick={toggleSpeaking} title={isSpeaking ? "停止朗读" : "朗读"}>{isSpeaking ? "⏹️ 停止" : "🔊 朗读"}</button>
                <button className="btn-history" onClick={() => setShowExportModal(true)} title="导出">📤 导出</button>
                <button className="btn-history" onClick={() => setShowStatsModal(true)} title="统计">📊 统计</button>
                <button className="btn-history" onClick={openVersionHistory} title="历史版本">🕐 历史</button>
                <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                  {autoSaveStatus === "saving" && <span style={{ fontSize: 12, color: "var(--color-text-secondary)" }}>保存中...</span>}
                  {autoSaveStatus === "saved" && <span style={{ fontSize: 12, color: "#22c55e" }}>✓ 已自动保存</span>}
                  {autoSaveStatus === "error" && <span style={{ fontSize: 12, color: "#ef4444" }}>保存失败</span>}
                  <button className="btn-save" onClick={saveChapter}>保存</button>
                </div>
              </div>
              <div className="editor-body">
                <textarea
                  ref={editorRef}
                  className="editor-textarea"
                  value={editContent}
                  onChange={(e) => setEditContent(e.target.value)}
                  placeholder="开始写作，或在右侧与 AI 对话生成内容..."
                />
                <div className="editor-preview">
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>{editContent || "*暂无内容*"}</ReactMarkdown>
                </div>
              </div>
            </>
          ) : (
            <div className="editor-empty">
              <p>选择左侧章节开始编辑</p>
            </div>
          )}
        </main>

        {/* Right: AI Chat */}
        <aside className="ws-chat">
          <div className="chat-header">
            <div style={{ display: "flex", alignItems: "center", gap: 8, flex: 1 }}>
              <h3 style={{ margin: 0 }}>AI 创作助手</h3>
              <button
                className="btn-add"
                onClick={() => setShowConversationList(!showConversationList)}
                title="对话列表"
                style={{ fontSize: 12, width: 24, height: 24, padding: 0 }}
              >
                💬
              </button>
              <button
                className="btn-add"
                onClick={createConversation}
                title="新建对话"
                style={{ fontSize: 12, width: 24, height: 24, padding: 0 }}
              >
                +
              </button>
            </div>
            {availableModels.length > 0 && (
              <select
                className="model-selector"
                value={selectedModel}
                onChange={(e) => setSelectedModel(e.target.value)}
              >
                {availableModels.map((m) => (
                  <option key={m} value={m}>{m}</option>
                ))}
              </select>
            )}
          </div>
          {/* Conversation list dropdown */}
          {showConversationList && (
            <div className="conversation-list" style={{
              background: "var(--color-bg-secondary)",
              borderBottom: "1px solid var(--color-border)",
              maxHeight: 200,
              overflow: "auto",
            }}>
              {conversations.map((conv) => (
                <div
                  key={conv.id}
                  className={`conversation-item ${activeConversationId === conv.id ? "active" : ""}`}
                  style={{
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "space-between",
                    padding: "8px 12px",
                    cursor: "pointer",
                    background: activeConversationId === conv.id ? "var(--color-primary-light)" : "transparent",
                  }}
                  onClick={() => {
                    setActiveConversationId(conv.id);
                    setShowConversationList(false);
                  }}
                >
                  <span style={{ flex: 1, fontSize: 13, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                    {conv.title}
                  </span>
                  <button
                    className="source-delete"
                    onClick={(e) => { e.stopPropagation(); deleteConversation(conv.id); }}
                    title="删除"
                    style={{ width: 20, height: 20, fontSize: 12 }}
                  >
                    ×
                  </button>
                </div>
              ))}
              {conversations.length === 0 && (
                <div style={{ padding: "8px 12px", fontSize: 13, color: "var(--color-text-secondary)" }}>
                  暂无对话，点击 + 创建
                </div>
              )}
            </div>
          )}
          <div className="chat-messages">
            {messages.length === 0 && (
              <div className="chat-welcome">
                <p>你好！我是你的 AI 创作助手。</p>
                <p>你可以让我帮你：</p>
                <ul>
                  <li>写章节内容</li>
                  <li>设计人物设定</li>
                  <li>续写或改写</li>
                  <li>构建故事大纲</li>
                </ul>
                {sources.length > 0 && (
                  <p style={{ marginTop: 8, color: "var(--color-primary)" }}>
                    已加载 {sources.length} 个参考素材
                  </p>
                )}
              </div>
            )}
            {messages.map((msg, i) => (
              <div key={i} className={`chat-msg ${msg.role}`}>
                <div className="msg-content">
                  {msg.role === "assistant" ? (
                    <div>{renderWithCitations(msg.content)}</div>
                  ) : (
                    msg.content
                  )}
                </div>
                {msg.role === "assistant" && (
                  <button className="btn-ai-save" onClick={() => openAiSave(msg.content)} title="保存到文件">💾 保存到文件</button>
                )}
              </div>
            ))}
            {toolCalls.map((tc) => (
              <div key={tc.call_id} className={`tool-call-card ${tc.status}`}>
                <span className="tool-call-icon">
                  {tc.status === "running" ? "⏳" : tc.status === "success" ? "✅" : "❌"}
                </span>
                <span className="tool-call-label">
                  {tc.status === "running" ? `正在${tc.label}...` : tc.status === "success" ? `已${tc.label}` : `${tc.label}失败`}
                </span>
                {tc.result && !tc.result.success && (
                  <span className="tool-call-error">{String(tc.result.error || "")}</span>
                )}
              </div>
            ))}
            {streaming && (
              <div className="chat-msg assistant">
                <div className="msg-content">
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>{streamContent}</ReactMarkdown>
                  <span className="cursor-blink">|</span>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>
          {suggestions.length > 0 && (
            <div className="suggestion-chips">
              {suggestions.map((s, i) => (
                <button key={i} className="suggestion-chip" onClick={() => { setInput(s); setSuggestions([]); }}>{s}</button>
              ))}
            </div>
          )}
          <div className="chat-input-area">
            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="输入创作指令... (Enter 发送, Shift+Enter 换行)"
              rows={3}
            />
            <button className="btn-send" onClick={sendMessage} disabled={streaming || !input.trim()}>
              发送
            </button>
          </div>
        </aside>
      </div>

      {/* Source import modal */}
      {showSourceModal && (
        <div className="modal-overlay" onClick={() => setShowSourceModal(false)}>
          <div className="modal-card" onClick={(e) => e.stopPropagation()}>
            <h3>导入素材</h3>
            <div className="modal-tabs">
              <button className={sourceImportTab === "text" ? "active" : ""} onClick={() => setSourceImportTab("text")}>文本</button>
              <button className={sourceImportTab === "url" ? "active" : ""} onClick={() => setSourceImportTab("url")}>网页链接</button>
              <button className={sourceImportTab === "file" ? "active" : ""} onClick={() => setSourceImportTab("file")}>文件</button>
            </div>
            <input placeholder="素材名称" value={sourceName} onChange={(e) => setSourceName(e.target.value)} style={{ marginBottom: 12 }} />
            {sourceImportTab === "text" && <textarea placeholder="粘贴文本内容..." value={sourceContent} onChange={(e) => setSourceContent(e.target.value)} />}
            {sourceImportTab === "url" && (
              <div>
                <input placeholder="https://example.com/article 或 YouTube 链接" value={sourceUrl} onChange={(e) => setSourceUrl(e.target.value)} />
                <p style={{ fontSize: 12, color: "var(--color-text-secondary)", marginTop: 4 }}>
                  支持网页链接和 YouTube 视频（自动提取字幕）
                </p>
              </div>
            )}
            {sourceImportTab === "file" && (
              <div className="file-upload-area">
                <input type="file" accept=".txt,.md,.pdf,.docx" onChange={(e) => setSourceFile(e.target.files?.[0] || null)} />
                {sourceFile && <p style={{ fontSize: 13, color: "var(--color-text-secondary)", marginTop: 8 }}>已选择: {sourceFile.name}</p>}
              </div>
            )}
            <div className="modal-actions">
              <button className="btn-cancel" onClick={() => setShowSourceModal(false)}>取消</button>
              <button className="btn-save" onClick={handleAddSource}>导入</button>
            </div>
          </div>
        </div>
      )}

      {/* Export modal */}
      {showExportModal && (
        <div className="modal-overlay" onClick={() => setShowExportModal(false)}>
          <div className="modal-card" onClick={(e) => e.stopPropagation()}>
            <h3>导出内容</h3>
            <div className="export-options">
              <div className="export-section">
                <h4>导出当前章节</h4>
                <div className="export-btns">
                  <button className="btn-export" onClick={() => { exportCurrentChapter("md"); setShowExportModal(false); }}>Markdown (.md)</button>
                  <button className="btn-export" onClick={() => { exportCurrentChapter("txt"); setShowExportModal(false); }}>纯文本 (.txt)</button>
                  <button className="btn-export" onClick={() => { exportAsPdf(); setShowExportModal(false); }}>PDF (打印)</button>
                  <button className="btn-export" onClick={() => { exportCurrentChapterDocx(); setShowExportModal(false); }}>Word (.docx)</button>
                </div>
              </div>
              <div className="export-section">
                <h4>导出全部章节</h4>
                <div className="export-btns">
                  <button className="btn-export" onClick={() => { exportAllChapters("md"); setShowExportModal(false); }}>Markdown (.md)</button>
                  <button className="btn-export" onClick={() => { exportAllChapters("txt"); setShowExportModal(false); }}>纯文本 (.txt)</button>
                  <button className="btn-export" onClick={() => { exportAllChaptersDocx(); setShowExportModal(false); }}>Word (.docx)</button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Version history modal */}
      {showVersionModal && (
        <div className="modal-overlay" onClick={() => setShowVersionModal(false)}>
          <div className="modal-card" onClick={(e) => e.stopPropagation()}>
            <h3>历史版本</h3>
            {versions.length === 0 ? (
              <p style={{ color: "var(--color-text-secondary)", fontSize: 14 }}>暂无历史版本</p>
            ) : (
              <div className="version-list">
                {versions.map((v, idx) => (
                  <div key={v.id} className="version-item">
                    <div className="version-info">
                      <span className="version-label">v{v.version}</span>
                      <span className="version-date">{new Date(v.created_at).toLocaleString("zh-CN")}</span>
                    </div>
                    <div className="version-actions">
                      {idx < versions.length - 1 && (
                        <button className="btn-restore" onClick={() => openDiffView(versions[idx + 1].version, v.version)} style={{ marginRight: 8 }}>
                          对比
                        </button>
                      )}
                      <button className="btn-restore" onClick={() => restoreVersion(v.version)}>恢复</button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Diff modal */}
      {showDiffModal && diffContent && (
        <div className="modal-overlay" onClick={() => setShowDiffModal(false)}>
          <div className="modal-card" onClick={(e) => e.stopPropagation()} style={{ width: 900, maxWidth: "90vw", maxHeight: "80vh", overflow: "auto" }}>
            <h3>版本对比：v{diffVersion1} → v{diffVersion2}</h3>
            <div style={{ display: "flex", gap: 16, marginTop: 16 }}>
              <div style={{ flex: 1 }}>
                <h4 style={{ margin: "0 0 8px", color: "var(--color-text-secondary)" }}>v{diffVersion1}（旧版本）</h4>
                <div style={{
                  background: "var(--color-bg-secondary)",
                  padding: 12,
                  borderRadius: 8,
                  fontSize: 13,
                  lineHeight: 1.6,
                  whiteSpace: "pre-wrap",
                  maxHeight: "60vh",
                  overflow: "auto",
                }}>
                  {renderDiff(diffContent.v1, diffContent.v2).map((line, i) => (
                    <div key={i} style={{ background: line.changed ? "#fef2f2" : "transparent", padding: "2px 4px" }}>
                      {line.line1 || " "}
                    </div>
                  ))}
                </div>
              </div>
              <div style={{ flex: 1 }}>
                <h4 style={{ margin: "0 0 8px", color: "var(--color-text-secondary)" }}>v{diffVersion2}（新版本）</h4>
                <div style={{
                  background: "var(--color-bg-secondary)",
                  padding: 12,
                  borderRadius: 8,
                  fontSize: 13,
                  lineHeight: 1.6,
                  whiteSpace: "pre-wrap",
                  maxHeight: "60vh",
                  overflow: "auto",
                }}>
                  {renderDiff(diffContent.v1, diffContent.v2).map((line, i) => (
                    <div key={i} style={{ background: line.changed ? "#f0fdf4" : "transparent", padding: "2px 4px" }}>
                      {line.line2 || " "}
                    </div>
                  ))}
                </div>
              </div>
            </div>
            <div className="modal-actions" style={{ marginTop: 16 }}>
              <button className="btn-cancel" onClick={() => setShowDiffModal(false)}>关闭</button>
            </div>
          </div>
        </div>
      )}

      {/* Character modal */}
      {showCharModal && (
        <div className="modal-overlay" onClick={() => setShowCharModal(false)}>
          <div className="modal-card" onClick={(e) => e.stopPropagation()} style={{ width: 560 }}>
            <h3>{editingChar ? "编辑角色" : "新建角色"}</h3>
            <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
              <div style={{ display: "flex", gap: 12 }}>
                <input placeholder="角色名称" value={charName} onChange={(e) => setCharName(e.target.value)} style={{ flex: 1 }} />
                <input placeholder="角色定位 (如：主角/反派)" value={charRole} onChange={(e) => setCharRole(e.target.value)} style={{ flex: 1 }} />
              </div>
              <textarea placeholder="外貌描写..." value={charAppearance} onChange={(e) => setCharAppearance(e.target.value)} rows={2} />
              <textarea placeholder="性格特点..." value={charPersonality} onChange={(e) => setCharPersonality(e.target.value)} rows={2} />
              <textarea placeholder="背景故事..." value={charBackstory} onChange={(e) => setCharBackstory(e.target.value)} rows={2} />
              <textarea placeholder="人物关系..." value={charRelationships} onChange={(e) => setCharRelationships(e.target.value)} rows={2} />
            </div>
            <div className="modal-actions">
              <button className="btn-cancel" onClick={() => setShowCharModal(false)}>取消</button>
              <button className="btn-save" onClick={saveCharacter}>{editingChar ? "保存" : "创建"}</button>
            </div>
          </div>
        </div>
      )}

      {/* Note modal */}
      {showNoteModal && (
        <div className="modal-overlay" onClick={() => setShowNoteModal(false)}>
          <div className="modal-card" onClick={(e) => e.stopPropagation()} style={{ width: 560 }}>
            <h3>{editingNote ? "编辑文档" : "新建文档"}</h3>
            <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
              <input placeholder="文档标题" value={noteTitle} onChange={(e) => setNoteTitle(e.target.value)} />
              {categories.length > 0 && (
                <select value={noteCategoryId ?? ""} onChange={(e) => setNoteCategoryId(e.target.value ? Number(e.target.value) : null)}>
                  <option value="">未分类</option>
                  {categories.map((c) => <option key={c.id} value={c.id}>{c.icon} {c.name}</option>)}
                </select>
              )}
              <textarea placeholder="文档内容..." value={noteContent} onChange={(e) => setNoteContent(e.target.value)} rows={10} />
            </div>
            <div className="modal-actions">
              <button className="btn-cancel" onClick={() => setShowNoteModal(false)}>取消</button>
              <button className="btn-save" onClick={saveNote}>{editingNote ? "保存" : "创建"}</button>
            </div>
          </div>
        </div>
      )}

      {/* Generate result modal */}
      {showGenerateModal && (
        <div className="modal-overlay" onClick={() => setShowGenerateModal(false)}>
          <div className="modal-card" onClick={(e) => e.stopPropagation()} style={{ width: 640, maxHeight: "80vh", overflow: "auto" }}>
            <h3>AI 生成结果</h3>
            <div className="generate-result"><ReactMarkdown remarkPlugins={[remarkGfm]}>{generateResult}</ReactMarkdown></div>
            <div className="modal-actions">
              <button className="btn-cancel" onClick={() => setShowGenerateModal(false)}>关闭</button>
              <button className="btn-save" onClick={() => navigator.clipboard.writeText(generateResult)}>复制</button>
            </div>
          </div>
        </div>
      )}

      {/* Recommend result modal */}
      {showRecommendModal && (
        <div className="modal-overlay" onClick={() => setShowRecommendModal(false)}>
          <div className="modal-card" onClick={(e) => e.stopPropagation()} style={{ width: 560 }}>
            <h3>AI 素材推荐</h3>
            <div className="generate-result"><ReactMarkdown remarkPlugins={[remarkGfm]}>{recommendResult}</ReactMarkdown></div>
            <div className="modal-actions">
              <button className="btn-cancel" onClick={() => setShowRecommendModal(false)}>关闭</button>
            </div>
          </div>
        </div>
      )}

      {/* AI save to file modal */}
      {showAiSaveModal && (
        <div className="modal-overlay" onClick={() => setShowAiSaveModal(false)}>
          <div className="modal-card" onClick={(e) => e.stopPropagation()} style={{ width: 520 }}>
            <h3>保存 AI 回复到文件</h3>
            <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
              <input placeholder="文件标题" value={aiSaveTitle} onChange={(e) => setAiSaveTitle(e.target.value)} />
              {categories.length > 0 && (
                <select value={aiSaveCategoryId ?? ""} onChange={(e) => setAiSaveCategoryId(e.target.value ? Number(e.target.value) : null)}>
                  <option value="">未分类</option>
                  {categories.map((c) => <option key={c.id} value={c.id}>{c.icon} {c.name}</option>)}
                </select>
              )}
              <div className="ai-save-preview">{aiSaveContent.slice(0, 200)}{aiSaveContent.length > 200 ? "..." : ""}</div>
            </div>
            <div className="modal-actions">
              <button className="btn-cancel" onClick={() => setShowAiSaveModal(false)}>取消</button>
              <button className="btn-save" onClick={confirmAiSave}>确认保存</button>
            </div>
          </div>
        </div>
      )}

      {/* New category modal */}
      {showNewCatModal && (
        <div className="modal-overlay" onClick={() => setShowNewCatModal(false)}>
          <div className="modal-card" onClick={(e) => e.stopPropagation()} style={{ width: 400 }}>
            <h3>新建分类</h3>
            <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
              <input placeholder="分类名称" value={newCatName} onChange={(e) => setNewCatName(e.target.value)} autoFocus />
              <div className="icon-selector">
                <label style={{ fontSize: 13, color: "var(--color-text-secondary)" }}>图标</label>
                <div className="icon-options">
                  {["📁", "🌍", "👤", "📖", "📋", "💡", "🎯", "🗺️", "⚔️", "🏛️"].map((ic) => (
                    <button key={ic} type="button" className={newCatIcon === ic ? "active" : ""} onClick={() => setNewCatIcon(ic)}>{ic}</button>
                  ))}
                </div>
              </div>
            </div>
            <div className="modal-actions">
              <button className="btn-cancel" onClick={() => setShowNewCatModal(false)}>取消</button>
              <button className="btn-save" onClick={createCategory}>创建</button>
            </div>
          </div>
        </div>
      )}

      {/* Character graph modal - Enhanced */}
      {showGraphModal && (
        <div className="modal-overlay" onClick={() => setShowGraphModal(false)}>
          <div className="modal-card" onClick={(e) => e.stopPropagation()} style={{ width: 800, height: 600 }}>
            <h3>角色关系图谱</h3>
            <div className="graph-container" style={{ position: "relative", width: "100%", height: "calc(100% - 80px)", overflow: "auto" }}>
              {characters.length === 0 ? (
                <p style={{ color: "var(--color-text-secondary)", textAlign: "center", padding: 40 }}>暂无角色数据</p>
              ) : (
                <div style={{ position: "relative", width: "100%", height: "100%", minHeight: 400 }}>
                  {/* Central node - Main character */}
                  {characters.filter(c => c.role?.includes("主角") || c.role?.includes("main")).slice(0, 1).map((c, idx) => (
                    <div key={c.id} style={{
                      position: "absolute",
                      left: "50%",
                      top: "50%",
                      transform: "translate(-50%, -50%)",
                      background: "var(--color-primary)",
                      color: "white",
                      padding: "16px 24px",
                      borderRadius: 12,
                      textAlign: "center",
                      minWidth: 120,
                      boxShadow: "0 4px 12px rgba(0,0,0,0.15)",
                      zIndex: 2,
                    }}>
                      <div style={{ fontWeight: 700, fontSize: 16 }}>{c.name}</div>
                      <div style={{ fontSize: 12, opacity: 0.9, marginTop: 4 }}>{c.role}</div>
                    </div>
                  ))}

                  {/* Other characters in circle */}
                  {characters.filter(c => !c.role?.includes("主角") && !c.role?.includes("main")).map((c, idx, arr) => {
                    const angle = (idx / arr.length) * 2 * Math.PI - Math.PI / 2;
                    const radius = 180;
                    const centerX = 50;
                    const centerY = 50;
                    const x = centerX + radius * Math.cos(angle) * 0.8;
                    const y = centerY + radius * Math.sin(angle) * 0.6;

                    const roleColors: Record<string, string> = {
                      "反派": "#ef4444",
                      "配角": "#6b7280",
                      "导师": "#8b5cf6",
                      "盟友": "#22c55e",
                    };
                    const bgColor = roleColors[c.role || ""] || "#6b7280";

                    return (
                      <div key={c.id} style={{
                        position: "absolute",
                        left: `${x}%`,
                        top: `${y}%`,
                        transform: "translate(-50%, -50%)",
                        background: bgColor,
                        color: "white",
                        padding: "12px 16px",
                        borderRadius: 10,
                        textAlign: "center",
                        minWidth: 100,
                        boxShadow: "0 2px 8px rgba(0,0,0,0.1)",
                        zIndex: 1,
                      }}>
                        <div style={{ fontWeight: 600, fontSize: 14 }}>{c.name}</div>
                        <div style={{ fontSize: 11, opacity: 0.9, marginTop: 2 }}>{c.role || "未设定"}</div>
                        {c.relationships && (
                          <div style={{ fontSize: 10, opacity: 0.8, marginTop: 4, maxWidth: 120, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                            {c.relationships}
                          </div>
                        )}
                      </div>
                    );
                  })}

                  {/* Connection lines (SVG) */}
                  <svg style={{ position: "absolute", top: 0, left: 0, width: "100%", height: "100%", pointerEvents: "none", zIndex: 0 }}>
                    {characters.filter(c => !c.role?.includes("主角") && !c.role?.includes("main")).map((c, idx, arr) => {
                      const angle = (idx / arr.length) * 2 * Math.PI - Math.PI / 2;
                      const radius = 180;
                      const startX = 50;
                      const startY = 50;
                      const endX = 50 + radius * Math.cos(angle) * 0.8;
                      const endY = 50 + radius * Math.sin(angle) * 0.6;

                      return (
                        <line
                          key={c.id}
                          x1={`${startX}%`}
                          y1={`${startY}%`}
                          x2={`${endX}%`}
                          y2={`${endY}%`}
                          stroke="var(--color-border)"
                          strokeWidth="2"
                          strokeDasharray="4"
                        />
                      );
                    })}
                  </svg>
                </div>
              )}
            </div>
            <div className="modal-actions">
              <button className="btn-cancel" onClick={() => setShowGraphModal(false)}>关闭</button>
            </div>
          </div>
        </div>
      )}

      {/* Citation popover - kept for backward compatibility */}
      {citationPopover && (
        <div className="citation-popover-overlay" onClick={() => setCitationPopover(null)}>
          <div className="citation-popover" style={{ left: citationPopover.x, top: citationPopover.y }} onClick={(e) => e.stopPropagation()}>
            <strong>引用素材：</strong> {citationPopover.text}
          </div>
        </div>
      )}

      {/* Source detail modal - for citation click */}
      {showSourceDetail && (
        <div className="modal-overlay" onClick={() => { setShowSourceDetail(null); setSourceDetailContent(""); }}>
          <div className="modal-card" onClick={(e) => e.stopPropagation()} style={{ width: 700, maxHeight: "80vh", overflow: "auto" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
              <h3 style={{ margin: 0 }}>{showSourceDetail.name}</h3>
              <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
                <span style={{ fontSize: 13, color: "var(--color-text-secondary)" }}>
                  {SOURCE_ICONS[showSourceDetail.type] || "📄"} {showSourceDetail.type}
                </span>
                <span style={{ fontSize: 13, color: "var(--color-text-secondary)" }}>
                  {showSourceDetail.word_count} 字
                </span>
              </div>
            </div>
            <div className="source-detail-content" style={{ 
              whiteSpace: "pre-wrap", 
              lineHeight: 1.8, 
              padding: 16, 
              background: "var(--color-bg-secondary, #f5f5f5)", 
              borderRadius: 8,
              fontSize: 14,
              maxHeight: "60vh",
              overflow: "auto"
            }}>
              {sourceDetailContent || "加载中..."}
            </div>
            <div className="modal-actions" style={{ marginTop: 16 }}>
              <button className="btn-cancel" onClick={() => { setShowSourceDetail(null); setSourceDetailContent(""); }}>关闭</button>
              <button className="btn-save" onClick={() => {
                // Switch to sources tab and highlight the source
                setSidebarTab("sources");
                setShowSourceDetail(null);
                setSourceDetailContent("");
              }}>在素材列表中查看</button>
            </div>
          </div>
        </div>
      )}

      {/* Close AI menu on outside click */}
      {showAiMenu && (
        <div style={{ position: "fixed", inset: 0, zIndex: 9 }} onClick={() => setShowAiMenu(false)} />
      )}
      {showGenerateMenu && (
        <div style={{ position: "fixed", inset: 0, zIndex: 9 }} onClick={() => setShowGenerateMenu(false)} />
      )}

      {/* Toast notification */}
      {aiSaveToast && (
        <div className="toast-notification">{aiSaveToast}</div>
      )}

      {/* Writing reminder notification */}
      {showReminder && (
        <div className="modal-overlay" onClick={() => setShowReminder(false)}>
          <div className="modal-card" onClick={(e) => e.stopPropagation()} style={{ width: 400, textAlign: "center" }}>
            <div style={{ fontSize: 48, marginBottom: 16 }}>✍️</div>
            <h3 style={{ marginBottom: 8 }}>写作提醒</h3>
            <p style={{ color: "var(--color-text-secondary)", marginBottom: 24 }}>{reminderMessage}</p>
            <div style={{ display: "flex", gap: 12, justifyContent: "center" }}>
              <button className="btn-cancel" onClick={() => setShowReminder(false)}>稍后提醒</button>
              <button className="btn-save" onClick={() => {
                setShowReminder(false);
                // Focus on editor
                const textarea = editorRef.current;
                if (textarea) textarea.focus();
              }}>开始写作</button>
            </div>
            <div style={{ marginTop: 16 }}>
              <label style={{ fontSize: 12, color: "var(--color-text-secondary)", cursor: "pointer" }}>
                <input
                  type="checkbox"
                  defaultChecked={localStorage.getItem("reminderEnabled") !== "false"}
                  onChange={(e) => localStorage.setItem("reminderEnabled", String(e.target.checked))}
                  style={{ marginRight: 4 }}
                />
                启用每日提醒
              </label>
            </div>
          </div>
        </div>
      )}

      {/* Writing statistics modal */}
      {showStatsModal && (
        <div className="modal-overlay" onClick={() => setShowStatsModal(false)}>
          <div className="modal-card" onClick={(e) => e.stopPropagation()} style={{ width: 600 }}>
            <h3>写作统计</h3>
            <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>
              {/* Overall stats */}
              <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 16 }}>
                <div style={{ textAlign: "center", padding: 16, background: "var(--color-bg-secondary)", borderRadius: 8 }}>
                  <div style={{ fontSize: 24, fontWeight: 700, color: "var(--color-primary)" }}>{chapters.length}</div>
                  <div style={{ fontSize: 13, color: "var(--color-text-secondary)" }}>总章节数</div>
                </div>
                <div style={{ textAlign: "center", padding: 16, background: "var(--color-bg-secondary)", borderRadius: 8 }}>
                  <div style={{ fontSize: 24, fontWeight: 700, color: "var(--color-primary)" }}>{totalWordCount.toLocaleString()}</div>
                  <div style={{ fontSize: 13, color: "var(--color-text-secondary)" }}>总字数</div>
                </div>
                <div style={{ textAlign: "center", padding: 16, background: "var(--color-bg-secondary)", borderRadius: 8 }}>
                  <div style={{ fontSize: 24, fontWeight: 700, color: "var(--color-primary)" }}>{sources.length}</div>
                  <div style={{ fontSize: 13, color: "var(--color-text-secondary)" }}>素材数量</div>
                </div>
              </div>

              {/* Daily goal */}
              <div style={{ padding: 16, background: "var(--color-bg-secondary)", borderRadius: 8 }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 8 }}>
                  <h4 style={{ margin: 0 }}>今日写作目标</h4>
                  <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                    <input
                      type="number"
                      value={writingGoal}
                      onChange={(e) => {
                        const val = parseInt(e.target.value) || 1000;
                        setWritingGoal(val);
                        localStorage.setItem("writingGoal", String(val));
                      }}
                      style={{ width: 80, padding: "4px 8px", borderRadius: 4, border: "1px solid var(--color-border)" }}
                    />
                    <span style={{ fontSize: 13, color: "var(--color-text-secondary)" }}>字</span>
                  </div>
                </div>
                <div style={{ marginBottom: 8 }}>
                  <div style={{ display: "flex", justifyContent: "space-between", fontSize: 13, marginBottom: 4 }}>
                    <span>已完成: {dailyWordCount} 字</span>
                    <span>{goalProgress}%</span>
                  </div>
                  <div style={{ height: 8, background: "var(--color-border)", borderRadius: 4, overflow: "hidden" }}>
                    <div style={{ height: "100%", width: `${goalProgress}%`, background: goalProgress >= 100 ? "#22c55e" : "var(--color-primary)", borderRadius: 4, transition: "width 0.3s" }} />
                  </div>
                </div>
                {goalProgress >= 100 && (
                  <div style={{ textAlign: "center", color: "#22c55e", fontSize: 14, fontWeight: 600 }}>
                    🎉 恭喜！今日目标已完成！
                  </div>
                )}
              </div>

              {/* Chapter breakdown */}
              <div>
                <h4 style={{ margin: "0 0 8px" }}>章节字数分布</h4>
                <div style={{ maxHeight: 200, overflow: "auto" }}>
                  {chapterStats.map((ch) => (
                    <div key={ch.id} style={{ display: "flex", justifyContent: "space-between", padding: "8px 0", borderBottom: "1px solid var(--color-border)" }}>
                      <span style={{ flex: 1, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{ch.title}</span>
                      <span style={{ color: "var(--color-text-secondary)", marginLeft: 16 }}>{ch.wordCount.toLocaleString()} 字</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
            <div className="modal-actions" style={{ marginTop: 16 }}>
              <button className="btn-cancel" onClick={() => setShowStatsModal(false)}>关闭</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
