from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.database import get_db
from ..core.deps import require_admin
from ..core.security import hash_password
from ..models.models import Chapter, Conversation, Message, Task, Template, User

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/stats")
async def admin_stats(user=Depends(require_admin), db: AsyncSession = Depends(get_db)):
    user_count = (await db.execute(select(func.count(User.id)))).scalar()
    task_count = (await db.execute(select(func.count(Task.id)))).scalar()
    chapter_count = (await db.execute(select(func.count(Chapter.id)))).scalar()
    conversation_count = (await db.execute(select(func.count(Conversation.id)))).scalar()
    message_count = (await db.execute(select(func.count(Message.id)))).scalar()
    template_count = (await db.execute(select(func.count(Template.id)))).scalar()
    return {
        "user_count": user_count,
        "task_count": task_count,
        "chapter_count": chapter_count,
        "conversation_count": conversation_count,
        "message_count": message_count,
        "template_count": template_count,
    }


# ---- Users ----
@router.get("/users")
async def list_users(user=Depends(require_admin), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).order_by(User.created_at.desc()))
    users = result.scalars().all()
    return [
        {"id": u.id, "name": u.name, "email": u.email, "role": u.role, "status": u.status,
         "created_at": u.created_at.isoformat()}
        for u in users
    ]


class UserCreate(BaseModel):
    name: str
    email: str
    password: str
    role: str = "user"


@router.post("/users")
async def create_user(req: UserCreate, user=Depends(require_admin), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == req.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already exists")
    new_user = User(name=req.name, email=req.email, password_hash=hash_password(req.password), role=req.role)
    db.add(new_user)
    await db.commit()
    return {"ok": True}


class UserUpdate(BaseModel):
    name: str | None = None
    role: str | None = None
    status: str | None = None


@router.patch("/users/{user_id}")
async def update_user(user_id: int, req: UserUpdate, admin=Depends(require_admin), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.id == user_id))
    u = result.scalar_one_or_none()
    if not u:
        raise HTTPException(status_code=404, detail="User not found")
    if req.name is not None:
        u.name = req.name
    if req.role is not None:
        u.role = req.role
    if req.status is not None:
        u.status = req.status
    await db.commit()
    return {"ok": True}


@router.delete("/users/{user_id}")
async def delete_user(user_id: int, admin=Depends(require_admin), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.id == user_id))
    u = result.scalar_one_or_none()
    if not u:
        raise HTTPException(status_code=404, detail="User not found")
    await db.delete(u)
    await db.commit()
    return {"ok": True}


# ---- Templates ----
@router.get("/templates")
async def list_templates(user=Depends(require_admin), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Template).order_by(Template.created_at.desc()))
    templates = result.scalars().all()
    return [
        {"id": t.id, "name": t.name, "type": t.type, "content": t.content, "is_builtin": t.is_builtin}
        for t in templates
    ]


class TemplateCreate(BaseModel):
    name: str
    type: str
    content: str


class TemplateUpdate(BaseModel):
    name: str | None = None
    type: str | None = None
    content: str | None = None


@router.post("/templates")
async def create_template(req: TemplateCreate, user=Depends(require_admin), db: AsyncSession = Depends(get_db)):
    t = Template(name=req.name, type=req.type, content=req.content, is_builtin=0)
    db.add(t)
    await db.commit()
    await db.refresh(t)
    return {"id": t.id, "name": t.name}


@router.patch("/templates/{template_id}")
async def update_template(template_id: int, req: TemplateUpdate, user=Depends(require_admin), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Template).where(Template.id == template_id))
    t = result.scalar_one_or_none()
    if not t:
        raise HTTPException(status_code=404, detail="Template not found")
    for field, value in req.model_dump(exclude_none=True).items():
        setattr(t, field, value)
    await db.commit()
    return {"ok": True}


@router.delete("/templates/{template_id}")
async def delete_template(template_id: int, user=Depends(require_admin), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Template).where(Template.id == template_id))
    t = result.scalar_one_or_none()
    if not t:
        raise HTTPException(status_code=404, detail="Template not found")
    await db.delete(t)
    await db.commit()
    return {"ok": True}
