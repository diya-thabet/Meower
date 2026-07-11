import json
from .base import BaseTool, ToolResult, ToolCategory
from ._runner import run_cli, _make_result


class GhuntTool(BaseTool):
    name = "ghunt"
    category = ToolCategory.EMAIL
    description = "Google account reconnaissance via email address"

    async def run(self, target: str, **kwargs) -> ToolResult:
        result = await run_cli(self.name, self.category, [
            "ghunt", "email", target,
        ], timeout=60)

        if result.status != "success":
            return result

        normalized = []
        stdout = result.raw_data.get("stdout", "")
        for line in stdout.splitlines():
            if ":" in line:
                key, _, val = line.partition(":")
                key = key.strip().lower().replace(" ", "_")
                val = val.strip()
                if key and val:
                    entry = {"key": key, "value": val, "email": target}
                    normalized.append(entry)

        result.normalized = normalized
        return result
