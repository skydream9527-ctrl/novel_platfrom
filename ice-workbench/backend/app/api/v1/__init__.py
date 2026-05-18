"""API v1 router aggregator."""
from fastapi import APIRouter

from . import (
    admin,
    admin_resources,
    admin_review,
    admin_settings,
    admin_sql_audit,
    admin_usage,
    agents,
    auth,
    conversations,
    experience_cards,
    files,
    guide,
    notifications,
    scheduled,
    search,
    skills,
    system_config,
    tasks,
    templates,
    users,
    ws,
)

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(tasks.router, prefix="/tasks", tags=["tasks"])
api_router.include_router(admin_review.share_router, prefix="/tasks", tags=["tasks"])
api_router.include_router(files.router, prefix="/files", tags=["files"])
api_router.include_router(conversations.router, tags=["conversations"])
api_router.include_router(agents.router, prefix="/agents", tags=["agents"])
api_router.include_router(skills.router, prefix="/skills", tags=["skills"])
api_router.include_router(notifications.router, prefix="/notifications", tags=["notifications"])
api_router.include_router(system_config.router, prefix="/system-config", tags=["system-config"])
api_router.include_router(search.router, prefix="/search", tags=["search"])
api_router.include_router(templates.router, prefix="/templates", tags=["templates"])
api_router.include_router(scheduled.router, prefix="/scheduled-tasks", tags=["scheduled-tasks"])
api_router.include_router(experience_cards.router, prefix="/experience-cards", tags=["experience-cards"])
api_router.include_router(guide.router, tags=["guide"])
api_router.include_router(admin.router, prefix="/admin", tags=["admin"])
api_router.include_router(admin_settings.router, prefix="/admin/settings", tags=["admin-settings"])
api_router.include_router(admin_usage.router, prefix="/admin/usage", tags=["admin-usage"])
api_router.include_router(admin_sql_audit.router, prefix="/admin/sql-audit", tags=["admin-sql-audit"])
api_router.include_router(admin_review.router, prefix="/admin", tags=["admin-review"])
api_router.include_router(admin_resources.router, prefix="/admin", tags=["admin-resources"])
api_router.include_router(ws.router, tags=["websocket"])
