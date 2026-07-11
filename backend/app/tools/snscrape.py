import re
from .base import BaseTool, ToolResult, ToolCategory
from ._runner import run_cli, _make_result


class SnscrapeTool(BaseTool):
    name = "snscrape"
    category = ToolCategory.SOCIAL
    description = "Scrape social network data (Twitter/X, Reddit, Telegram)"

    async def run(self, target: str, **kwargs) -> ToolResult:
        platform = kwargs.get("platform", "twitter")
        result = await run_cli(self.name, self.category, [
            "snscrape", f"--max-results", "20",
            f"{platform}-user", target,
        ], timeout=120)

        if result.status != "success":
            return result

        normalized = []
        stdout = result.raw_data.get("stdout", "")
        for line in stdout.splitlines():
            line = line.strip()
            if not line:
                continue
            normalized.append({
                "platform": platform,
                "username": target,
                "content": line[:500],
            })
            if len(normalized) >= 20:
                break

        result.normalized = normalized
        return result
