from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from ..core.database import Base


def utcnow():
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), default="user", nullable=False)  # admin / user
    status = Column(String(20), default="active", nullable=False)  # active / disabled
    created_at = Column(DateTime, default=utcnow)

    tasks = relationship("Task", back_populates="owner")


class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(Text, default="")
    type = Column(String(20), default="novel", nullable=False)  # novel / script / storyboard
    status = Column(String(20), default="active", nullable=False)  # active / completed / archived
    directory_path = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    owner = relationship("User", back_populates="tasks")
    chapters = relationship("Chapter", back_populates="task", order_by="Chapter.order_index", cascade="all, delete-orphan")
    conversations = relationship("Conversation", back_populates="task", cascade="all, delete-orphan")
    sources = relationship("Source", back_populates="task", cascade="all, delete-orphan")
    characters = relationship("Character", back_populates="task", cascade="all, delete-orphan")
    notes = relationship("Note", back_populates="task", cascade="all, delete-orphan")
    categories = relationship("Category", back_populates="task", cascade="all, delete-orphan")


class Chapter(Base):
    __tablename__ = "chapters"

    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False)
    title = Column(String(200), nullable=False)
    content = Column(Text, default="")
    order_index = Column(Integer, default=0)
    version = Column(Integer, default=1)
    status = Column(String(20), default="draft")  # idea / outline / draft / revision / final
    scheduled_date = Column(DateTime, nullable=True)  # 计划完成日期
    completed_date = Column(DateTime, nullable=True)  # 实际完成日期
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    task = relationship("Task", back_populates="chapters")
    versions = relationship("ChapterVersion", back_populates="chapter", order_by="ChapterVersion.version.desc()", cascade="all, delete-orphan")


class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False)
    title = Column(String(200), default="新对话")
    created_at = Column(DateTime, default=utcnow)

    task = relationship("Task", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", order_by="Message.created_at", cascade="all, delete-orphan")


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=False)
    role = Column(String(20), nullable=False)  # user / assistant / system
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=utcnow)

    conversation = relationship("Conversation", back_populates="messages")


class Template(Base):
    __tablename__ = "templates"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False)
    type = Column(String(20), nullable=False)  # novel / script / storyboard
    content = Column(Text, nullable=False)
    is_builtin = Column(Integer, default=0)
    is_public = Column(Integer, default=0)
    author_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=utcnow)

    author = relationship("User")


class Source(Base):
    __tablename__ = "sources"

    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False)
    name = Column(String(200), nullable=False)
    type = Column(String(20), default="text", nullable=False)  # text / file / url / chapter
    content = Column(Text, default="")
    word_count = Column(Integer, default=0)
    summary = Column(Text, default="")
    keywords = Column(String(500), default="")
    created_at = Column(DateTime, default=utcnow)

    task = relationship("Task", back_populates="sources")


class ChapterVersion(Base):
    __tablename__ = "chapter_versions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    chapter_id = Column(Integer, ForeignKey("chapters.id"), nullable=False)
    version = Column(Integer, nullable=False)
    title = Column(String(200), nullable=False)
    content = Column(Text, default="")
    created_at = Column(DateTime, default=utcnow)

    chapter = relationship("Chapter", back_populates="versions")


class Character(Base):
    __tablename__ = "characters"

    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False)
    name = Column(String(100), nullable=False)
    role = Column(String(100), default="")
    appearance = Column(Text, default="")
    personality = Column(Text, default="")
    backstory = Column(Text, default="")
    relationships = Column(Text, default="")
    created_at = Column(DateTime, default=utcnow)

    task = relationship("Task", back_populates="characters")


class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False)
    name = Column(String(100), nullable=False)
    icon = Column(String(10), default="📁")
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime, default=utcnow)

    task = relationship("Task", back_populates="categories")
    notes = relationship("Note", back_populates="category", cascade="all, delete-orphan")


class Note(Base):
    __tablename__ = "notes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=True)
    title = Column(String(200), nullable=False)
    content = Column(Text, default="")
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    task = relationship("Task", back_populates="notes")
    category = relationship("Category", back_populates="notes")


class SourceReference(Base):
    __tablename__ = "source_references"

    id = Column(Integer, primary_key=True, autoincrement=True)
    source_id = Column(Integer, ForeignKey("sources.id"), nullable=False)
    message_id = Column(Integer, ForeignKey("messages.id"), nullable=False)
    created_at = Column(DateTime, default=utcnow)

    source = relationship("Source")
    message = relationship("Message")


class CanvasCard(Base):
    __tablename__ = "canvas_cards"

    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False)
    title = Column(String(200), nullable=False)
    content = Column(Text, default="")
    card_type = Column(String(20), default="note")  # note / scene / character / event / idea
    x = Column(Integer, default=100)
    y = Column(Integer, default=100)
    width = Column(Integer, default=200)
    height = Column(Integer, default=150)
    color = Column(String(20), default="#ffffff")
    created_at = Column(DateTime, default=utcnow)

    task = relationship("Task")


class CanvasConnection(Base):
    __tablename__ = "canvas_connections"

    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False)
    source_card_id = Column(Integer, ForeignKey("canvas_cards.id"), nullable=False)
    target_card_id = Column(Integer, ForeignKey("canvas_cards.id"), nullable=False)
    label = Column(String(100), default="")
    connection_type = Column(String(20), default="related")  # related / causes / leads_to / part_of
    created_at = Column(DateTime, default=utcnow)

    task = relationship("Task")
    source_card = relationship("CanvasCard", foreign_keys=[source_card_id])
    target_card = relationship("CanvasCard", foreign_keys=[target_card_id])


class DailyNote(Base):
    __tablename__ = "daily_notes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    date = Column(String(10), nullable=False)  # YYYY-MM-DD
    content = Column(Text, default="")
    mood = Column(String(20), default="")
    word_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    user = relationship("User")


class Snippet(Base):
    __tablename__ = "snippets"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)
    category = Column(String(50), default="general")  # scene / dialogue / description / general
    tags = Column(String(500), default="")
    usage_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=utcnow)

    user = relationship("User")


class ChapterBranch(Base):
    __tablename__ = "chapter_branches"

    id = Column(Integer, primary_key=True, autoincrement=True)
    chapter_id = Column(Integer, ForeignKey("chapters.id"), nullable=False)
    name = Column(String(100), nullable=False)
    content = Column(Text, default="")
    is_active = Column(Integer, default=0)
    created_at = Column(DateTime, default=utcnow)

    chapter = relationship("Chapter")


class FavoriteItem(Base):
    __tablename__ = "favorite_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    item_type = Column(String(20), nullable=False)  # chapter / character / note / source
    item_id = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=utcnow)

    user = relationship("User")


from sqlalchemy import UniqueConstraint


class Link(Base):
    """双向链接关系表"""
    __tablename__ = "links"
    __table_args__ = (
        UniqueConstraint('task_id', 'source_type', 'source_id', 'target_type', 'target_id', name='uq_link'),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False)
    source_type = Column(String(20), nullable=False)  # chapter / note / character / source
    source_id = Column(Integer, nullable=False)
    target_type = Column(String(20), nullable=False)  # chapter / note / character / source
    target_id = Column(Integer, nullable=False)
    anchor_text = Column(String(500))  # 链接显示文本
    created_at = Column(DateTime, default=utcnow)

    task = relationship("Task")


class Tag(Base):
    """标签表"""
    __tablename__ = "tags"
    __table_args__ = (
        UniqueConstraint('task_id', 'name', name='uq_tag'),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False)
    name = Column(String(50), nullable=False)
    color = Column(String(7))  # HEX颜色值
    created_at = Column(DateTime, default=utcnow)

    task = relationship("Task")
    content_tags = relationship("ContentTag", back_populates="tag", cascade="all, delete-orphan")


class ContentTag(Base):
    """内容标签关联表"""
    __tablename__ = "content_tags"
    __table_args__ = (
        UniqueConstraint('tag_id', 'content_type', 'content_id', name='uq_content_tag'),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    tag_id = Column(Integer, ForeignKey("tags.id"), nullable=False)
    content_type = Column(String(20), nullable=False)  # chapter / note / source
    content_id = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=utcnow)

    tag = relationship("Tag", back_populates="content_tags")


class WritingGoal(Base):
    """写作目标表"""
    __tablename__ = "writing_goals"

    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False)
    goal_type = Column(String(20), nullable=False)  # daily / weekly / total
    target_words = Column(Integer, nullable=False)
    start_date = Column(DateTime)
    end_date = Column(DateTime)
    created_at = Column(DateTime, default=utcnow)

    task = relationship("Task")


class WritingLog(Base):
    """写作记录表"""
    __tablename__ = "writing_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False)
    chapter_id = Column(Integer, ForeignKey("chapters.id"))
    words_written = Column(Integer, nullable=False)
    duration_seconds = Column(Integer)
    recorded_at = Column(DateTime, default=utcnow)

    task = relationship("Task")
    chapter = relationship("Chapter")


class AttributeDefinition(Base):
    """属性定义表"""
    __tablename__ = "attribute_definitions"
    __table_args__ = (
        UniqueConstraint('task_id', 'name', name='uq_attribute_def'),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False)
    name = Column(String(50), nullable=False)
    field_type = Column(String(20), nullable=False)  # text / number / select / multi_select / date / checkbox / url
    options = Column(Text)  # JSON数组，select/multi_select的选项
    default_value = Column(Text)
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime, default=utcnow)

    task = relationship("Task")


class AttributeValue(Base):
    """属性值表"""
    __tablename__ = "attribute_values"
    __table_args__ = (
        UniqueConstraint('definition_id', 'chapter_id', name='uq_attribute_val'),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    definition_id = Column(Integer, ForeignKey("attribute_definitions.id"), nullable=False)
    chapter_id = Column(Integer, ForeignKey("chapters.id"), nullable=False)
    value = Column(Text)
    created_at = Column(DateTime, default=utcnow)

    definition = relationship("AttributeDefinition")
    chapter = relationship("Chapter")


class OutlineNode(Base):
    """大纲节点表"""
    __tablename__ = "outline_nodes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False)
    parent_id = Column(Integer, ForeignKey("outline_nodes.id"), nullable=True)
    chapter_id = Column(Integer, ForeignKey("chapters.id"), nullable=True)
    title = Column(String(200), nullable=False)
    summary = Column(Text, default="")
    node_type = Column(String(20), default="node")  # root / act / chapter / scene / node
    sort_order = Column(Integer, default=0)
    is_collapsed = Column(Integer, default=0)  # 0=False, 1=True
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    task = relationship("Task")
    parent = relationship("OutlineNode", remote_side=[id], backref="children")
    chapter = relationship("Chapter")


class TimelineEvent(Base):
    """时间线事件表"""
    __tablename__ = "timeline_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False)
    chapter_id = Column(Integer, ForeignKey("chapters.id"), nullable=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, default="")
    event_type = Column(String(20), default="scene")  # scene / plot / background / flashback
    story_date = Column(String(100), default="")
    story_date_order = Column(Integer, default=0)
    duration = Column(String(100), default="")
    location = Column(String(200), default="")
    characters = Column(Text, default="[]")  # JSON数组，角色ID列表
    is_milestone = Column(Integer, default=0)  # 0=False, 1=True
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    task = relationship("Task")
    chapter = relationship("Chapter")


class Comment(Base):
    """评论表"""
    __tablename__ = "comments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False)
    chapter_id = Column(Integer, ForeignKey("chapters.id"), nullable=False)
    parent_id = Column(Integer, ForeignKey("comments.id"), nullable=True)
    author_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    content = Column(Text, nullable=False)
    comment_type = Column(String(20), default="general")  # general / suggestion / issue / praise / ai
    status = Column(String(20), default="open")  # open / resolved / wontfix
    selection_start = Column(Integer, nullable=True)
    selection_end = Column(Integer, nullable=True)
    selected_text = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    task = relationship("Task")
    chapter = relationship("Chapter")
    parent = relationship("Comment", remote_side=[id], backref="replies")
    author = relationship("User")


class WorldbuildingCategory(Base):
    """世界观分类表"""
    __tablename__ = "worldbuilding_categories"

    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False)
    name = Column(String(50), nullable=False)
    icon = Column(String(10), default="📁")
    description = Column(Text, default="")
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime, default=utcnow)

    task = relationship("Task")
    entries = relationship("WorldbuildingEntry", back_populates="category", cascade="all, delete-orphan")


class WorldbuildingEntry(Base):
    """世界观条目表"""
    __tablename__ = "worldbuilding_entries"

    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False)
    category_id = Column(Integer, ForeignKey("worldbuilding_categories.id"), nullable=False)
    title = Column(String(200), nullable=False)
    content = Column(Text, default="")
    attributes = Column(Text, default="{}")  # JSON格式的自定义属性
    related_entries = Column(Text, default="[]")  # JSON数组，关联的其他条目ID
    related_characters = Column(Text, default="[]")  # JSON数组，关联的角色ID
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    task = relationship("Task")
    category = relationship("WorldbuildingCategory", back_populates="entries")


class Conflict(Base):
    """冲突表"""
    __tablename__ = "conflicts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(Text, default="")
    conflict_type = Column(String(20), default="external")  # external / internal / interpersonal
    status = Column(String(20), default="introduced")  # introduced / developing / climax / resolved
    priority = Column(String(10), default="medium")  # high / medium / low
    introduced_chapter_id = Column(Integer, ForeignKey("chapters.id"), nullable=True)
    resolved_chapter_id = Column(Integer, ForeignKey("chapters.id"), nullable=True)
    related_characters = Column(Text, default="[]")  # JSON数组，相关角色ID
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    task = relationship("Task")
    introduced_chapter = relationship("Chapter", foreign_keys=[introduced_chapter_id])
    resolved_chapter = relationship("Chapter", foreign_keys=[resolved_chapter_id])


class Foreshadowing(Base):
    """伏笔表"""
    __tablename__ = "foreshadowing"

    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(Text, default="")
    foreshadowing_type = Column(String(20), default="plot")  # plot / character / world / item
    status = Column(String(20), default="planted")  # planted / hinted / revealed / resolved
    planted_chapter_id = Column(Integer, ForeignKey("chapters.id"), nullable=True)
    revealed_chapter_id = Column(Integer, ForeignKey("chapters.id"), nullable=True)
    hints = Column(Text, default="[]")  # JSON数组，包含{chapter_id, description}的提示列表
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    task = relationship("Task")
    planted_chapter = relationship("Chapter", foreign_keys=[planted_chapter_id])
    revealed_chapter = relationship("Chapter", foreign_keys=[revealed_chapter_id])


class Annotation(Base):
    """审阅标注表"""
    __tablename__ = "annotations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False)
    chapter_id = Column(Integer, ForeignKey("chapters.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    annotation_type = Column(String(20), nullable=False)  # highlight / underline / strikethrough / wavy / margin_note
    color = Column(String(7), nullable=True)
    selection_start = Column(Integer, nullable=False)
    selection_end = Column(Integer, nullable=False)
    selected_text = Column(Text, nullable=True)
    note = Column(Text, nullable=True)
    suggestion = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utcnow)

    task = relationship("Task")
    chapter = relationship("Chapter")
    user = relationship("User")
