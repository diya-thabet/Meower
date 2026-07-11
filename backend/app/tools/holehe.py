import re
from .base import BaseTool, ToolResult, ToolCategory
from ._runner import run_cli, _make_result


class HoleheTool(BaseTool):
    name = "holehe"
    category = ToolCategory.EMAIL
    description = "Check if an email is registered on 120+ online services"

    async def run(self, target: str, **kwargs) -> ToolResult:
        result = await run_cli(self.name, self.category, [
            "holehe", target, "--only-used", "--no-color",
        ], timeout=60)

        if result.status != "success":
            return result

        normalized = []
        stdout = result.raw_data.get("stdout", "")
        for line in stdout.splitlines():
            line = line.strip()
            if "]" in line and "@" not in line:
                indicator, _, service = line.partition("]")
                indicator = indicator.strip().lstrip("[").strip()
                service = service.strip()
                if not service:
                    continue
                exists = indicator == "+"
                normalized.append({
                    "service": service,
                    "email": target,
                    "exists": exists,
                })

        result.normalized = normalized
        return result
