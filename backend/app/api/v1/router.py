from fastapi import APIRouter
from .investigations import router as investigations_router
from .tools import router as tools_router
from .reports import router as reports_router

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(investigations_router)
api_router.include_router(tools_router)
api_router.include_router(reports_router)
