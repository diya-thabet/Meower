from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class ToolCategory(str, Enum):
    EMAIL = "email"
    USERNAME = "username"
    SOCIAL = "social"
    DOMAIN = "domain"
    PHONE = "phone"
    DATA_BREACH = "data_breach"


@dataclass
class ToolResult:
    tool_name: str
    category: ToolCategory
    status: str
    raw_data: dict
    normalized: list[dict] = field(default_factory=list)
    error: Optional[str] = None
    duration_ms: int = 0


class BaseTool(ABC):
    name: str = ""
    category: ToolCategory = ToolCategory.EMAIL
    description: str = ""
    enabled: bool = True

    @abstractmethod
    async def run(self, target: str, **kwargs) -> ToolResult:
        ...
