from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from .api import admin, auth, categories, chapters, chat, conversations, notes, search, sources, summaries, templates, tasks, ai_actions, characters
from .core.config import settings
from .core.database import init_db
from .seed import bootstrap


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    await bootstrap()
    yield


app = FastAPI(title="Novel Platform", version="1.0.0", lifespan=lifespan)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API routes
app.include_router(auth.router, prefix="/api/v1")
app.include_router(tasks.router, prefix="/api/v1")
app.include_router(chapters.router, prefix="/api/v1")
app.include_router(chat.router, prefix="/api/v1")
app.include_router(conversations.router, prefix="/api/v1")
app.include_router(templates.router, prefix="/api/v1")
app.include_router(admin.router, prefix="/api/v1")
app.include_router(sources.router, prefix="/api/v1")
app.include_router(summaries.router, prefix="/api/v1")
app.include_router(ai_actions.router, prefix="/api/v1")
app.include_router(characters.router, prefix="/api/v1")
app.include_router(notes.router, prefix="/api/v1")
app.include_router(search.router, prefix="/api/v1")
app.include_router(categories.router, prefix="/api/v1")


@app.get("/api/v1/health")
async def health():
    return {"status": "ok", "llm_enabled": settings.llm_enabled}


# Serve frontend SPA
frontend_dist = Path(__file__).resolve().parents[2] / "frontend" / "dist"
if frontend_dist.is_dir():
    app.mount("/assets", StaticFiles(directory=str(frontend_dist / "assets")), name="assets")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        if full_path.startswith("api/"):
            return JSONResponse(status_code=404, content={"detail": "Not found"})
        file_path = frontend_dist / full_path
        if file_path.is_file():
            return FileResponse(str(file_path))
        return FileResponse(str(frontend_dist / "index.html"))


# Uniform error handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"code": 500, "message": str(exc), "error_code": "INTERNAL_ERROR"},
    )
