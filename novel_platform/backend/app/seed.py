from sqlalchemy import select

from .core.database import async_session
from .core.security import hash_password
from .models.models import Template, User


async def bootstrap():
    async with async_session() as db:
        # Seed admin user
        result = await db.execute(select(User).where(User.email == "admin@novel.com"))
        if not result.scalar_one_or_none():
            from .core.config import settings

            admin = User(
                name=settings.novel_bootstrap_admin_name,
                email=settings.novel_bootstrap_admin_email,
                password_hash=hash_password(settings.novel_bootstrap_admin_password),
                role="admin",
            )
            db.add(admin)

        # Seed templates
        result = await db.execute(select(Template).limit(1))
        if not result.scalar_one_or_none():
            templates = [
                Template(
                    name="小说大纲模板",
                    type="novel",
                    content="# 小说大纲\n\n## 故事背景\n\n## 主要人物\n\n### 主角\n\n### 配角\n\n## 故事线\n\n### 第一幕：开端\n\n### 第二幕：发展\n\n### 第三幕：高潮\n\n### 第四幕：结局\n\n## 主题与寓意\n",
                    is_builtin=1,
                ),
                Template(
                    name="剧本格式模板",
                    type="script",
                    content="# 剧本标题\n\n## 场景一\n\n**内景/外景** 地点 - 时间\n\n**人物：**\n\n---\n\n**角色名**：（动作描述）台词内容。\n\n**角色名**：台词内容。\n\n---\n\n## 场景二\n",
                    is_builtin=1,
                ),
                Template(
                    name="分镜脚本模板",
                    type="storyboard",
                    content="# 分镜脚本\n\n## 场景 1\n\n| 镜号 | 景别 | 画面描述 | 对白/旁白 | 时长 | 备注 |\n|------|------|----------|-----------|------|------|\n| 1 | 全景 | | | 3s | |\n| 2 | 中景 | | | 3s | |\n| 3 | 近景 | | | 2s | |\n\n## 场景 2\n\n| 镜号 | 景别 | 画面描述 | 对白/旁白 | 时长 | 备注 |\n|------|------|----------|-----------|------|------|\n| 1 | | | | | |\n",
                    is_builtin=1,
                ),
            ]
            db.add_all(templates)

        await db.commit()
