from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from .core.config import settings
from .db.base import Base
from .db.session import engine
from .api.v1.router import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()


app = FastAPI(
    title=settings.app_name,
    version=settings.version,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


@app.get("/health")
async def health():
    return {"status": "ok", "version": settings.version}


frontend_index = Path(settings.frontend_dir) / "index.html"
if frontend_index.exists():
    @app.api_route("/{path_name:path}", methods=["GET"])
    async def catch_all(request: Request, path_name: str):
        if path_name.startswith("api/") or path_name.startswith("ws/"):
            from fastapi import HTTPException
            raise HTTPException(status_code=404)
        full_path = Path(settings.frontend_dir) / path_name
        if full_path.exists() and full_path.is_file():
            return FileResponse(str(full_path))
        return FileResponse(str(frontend_index))
