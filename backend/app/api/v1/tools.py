from fastapi import APIRouter
from ...tools.base import ToolCategory
from ...tools import TOOL_REGISTRY

router = APIRouter(prefix="/tools", tags=["tools"])


@router.get("")
async def list_tools():
    return [
        {
            "name": t.name,
            "category": t.category.value,
            "description": t.description,
        }
        for t in TOOL_REGISTRY
    ]


@router.get("/categories")
async def list_categories():
    return [c.value for c in ToolCategory]
