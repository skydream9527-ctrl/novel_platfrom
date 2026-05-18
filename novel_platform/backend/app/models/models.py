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
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    task = relationship("Task", back_populates="chapters")
    versions = relationship("ChapterVersion", back_populates="chapter", order_by="ChapterVersion.version.desc()", cascade="all, delete-orphan")


class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False)
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
    created_at = Column(DateTime, default=utcnow)


class Source(Base):
    __tablename__ = "sources"

    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False)
    name = Column(String(200), nullable=False)
    type = Column(String(20), default="text", nullable=False)  # text / file / url / chapter
    content = Column(Text, default="")
    word_count = Column(Integer, default=0)
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
