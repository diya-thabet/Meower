from .base import BaseTool, ToolResult, ToolCategory
from ._runner import run_cli


class SocidExtractorTool(BaseTool):
    name = "socid_extractor"
    category = ToolCategory.USERNAME
    description = "Extract social media IDs from profiles"

    async def run(self, target: str, **kwargs) -> ToolResult:
        result = await run_cli(self.name, self.category, [
            "socid_extractor", target,
        ], timeout=60)

        if result.status != "success":
            return result

        normalized = []
        stdout = result.raw_data.get("stdout", "")
        for line in stdout.splitlines():
            line = line.strip()
            if ":" in line and line.count(":") >= 1:
                key, val = line.split(":", 1)
                normalized.append({
                    "platform": key.strip(),
                    "value": val.strip(),
                    "username": target,
                })

        result.normalized = normalized
        return result
