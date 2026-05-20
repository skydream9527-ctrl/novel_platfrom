from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from .config import settings

engine = create_async_engine(settings.db_url, echo=False)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncSession:
    async with async_session() as session:
        yield session


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        # Add new columns if they don't exist (migration for existing databases)
        try:
            await conn.execute(text("SELECT summary FROM sources LIMIT 1"))
        except Exception:
            try:
                await conn.execute(text("ALTER TABLE sources ADD COLUMN summary TEXT DEFAULT ''"))
                await conn.execute(text("ALTER TABLE sources ADD COLUMN keywords VARCHAR(500) DEFAULT ''"))
            except Exception:
                pass
        try:
            await conn.execute(text("SELECT title FROM conversations LIMIT 1"))
        except Exception:
            try:
                await conn.execute(text("ALTER TABLE conversations ADD COLUMN title VARCHAR(200) DEFAULT '新对话'"))
            except Exception:
                pass
        try:
            await conn.execute(text("SELECT is_public FROM templates LIMIT 1"))
        except Exception:
            try:
                await conn.execute(text("ALTER TABLE templates ADD COLUMN is_public INTEGER DEFAULT 0"))
                await conn.execute(text("ALTER TABLE templates ADD COLUMN author_id INTEGER REFERENCES users(id)"))
            except Exception:
                pass
