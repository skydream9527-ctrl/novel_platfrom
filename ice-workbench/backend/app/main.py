"""FastAPI application entry."""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException

from .api.v1 import api_router
from .core.config import get_settings
from .core.errors import APIError, ErrorCode
from .seed.runner import bootstrap

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
log = logging.getLogger("ice")


@asynccontextmanager
async def lifespan(app: FastAPI):
    from .services import scheduler_svc

    log.info("ICE backend starting up; running seed bootstrap…")
    await bootstrap()
    scheduler_svc.start_loop()
    log.info("ICE backend ready (scheduler loop active)")
    try:
        yield
    finally:
        scheduler_svc.stop_loop()


app = FastAPI(title="ICE Data Workbench v3 API", version="3.0.0", lifespan=lifespan)

settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(APIError)
async def _api_error_handler(_: Request, exc: APIError):
    return JSONResponse(status_code=exc.status_code, content=exc.to_envelope())


@app.exception_handler(StarletteHTTPException)
async def _http_handler(_: Request, exc: StarletteHTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "code": exc.status_code * 100 + 1,
            "message": str(exc.detail),
            "error_code": ErrorCode.INTERNAL_ERROR if exc.status_code >= 500 else "HTTP_ERROR",
            "data": None,
        },
    )


@app.exception_handler(Exception)
async def _fallback_handler(_: Request, exc: Exception):
    log.exception("unhandled exception")
    return JSONResponse(
        status_code=500,
        content={
            "code": 50001,
            "message": str(exc),
            "error_code": ErrorCode.INTERNAL_ERROR,
            "data": None,
        },
    )


@app.get("/api/v1/health")
async def health():
    return {"code": 0, "message": "success", "data": {"status": "ok", "version": "3.0.0"}}


app.include_router(api_router)


# ------------------------------------------------------------------
# 生产环境：同端口伺服前端 SPA dist
# ------------------------------------------------------------------
# 如果 frontend/dist/ 存在（`npm run build` 产出），挂载为静态文件并对
# 未命中的路由回落到 index.html（SPA history-mode 支持）。部署 Linux /
# 公网时只暴露后端端口（默认 8000），不用再单独跑 vite dev server，
# 也不再有前后端跨域。开发模式下这段不生效，照样用 vite :5173 + proxy。
_FRONTEND_DIST = Path(__file__).resolve().parents[2] / "frontend" / "dist"
if _FRONTEND_DIST.is_dir() and (_FRONTEND_DIST / "index.html").exists():
    # /assets/... 等静态资源
    _assets_dir = _FRONTEND_DIST / "assets"
    if _assets_dir.is_dir():
        app.mount("/assets", StaticFiles(directory=_assets_dir), name="assets")

    _index_path = _FRONTEND_DIST / "index.html"

    @app.get("/", include_in_schema=False)
    async def _spa_root():
        return FileResponse(_index_path)

    @app.get("/{full_path:path}", include_in_schema=False)
    async def _spa_fallback(full_path: str):
        # API 路由已在前面注册；这里只接未命中任何 API 的 GET。
        # /api/* 未命中的路径返回 JSON 404（交给 exception_handler）。
        if full_path.startswith("api/"):
            raise StarletteHTTPException(status_code=404, detail="Not Found")
        # 真实静态文件（favicon、manifest 等）优先读 dist 下的对应文件
        candidate = _FRONTEND_DIST / full_path
        if full_path and candidate.is_file():
            return FileResponse(candidate)
        return FileResponse(_index_path)

    log.info("Serving frontend SPA from %s", _FRONTEND_DIST)
else:
    log.info("frontend/dist/ not found — run `npm run build` for single-port deploy")
