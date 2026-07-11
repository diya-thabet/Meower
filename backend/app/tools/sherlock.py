import re
from .base import BaseTool, ToolResult, ToolCategory
from ._runner import run_cli


class SherlockTool(BaseTool):
    name = "sherlock"
    category = ToolCategory.USERNAME
    description = "Search for a username across 400+ social networks"

    async def run(self, target: str, **kwargs) -> ToolResult:
        result = await run_cli(self.name, self.category, [
            "sherlock", target, "--print-found", "--no-color",
        ], timeout=120)

        if result.status != "success":
            return result

        normalized = []
        stdout = result.raw_data.get("stdout", "")
        for line in stdout.splitlines():
            line = line.strip()
            if ":" in line and "http" in line.lower():
                site_part, _, rest = line.partition(":")
                site = site_part.strip()
                site = site.lstrip("[+]").strip()
                url_match = re.search(r"https?://\S+", rest)
                url = url_match.group(0) if url_match else rest.strip()
                normalized.append({
                    "site": site,
                    "username": target,
                    "url": url,
                })

        result.normalized = normalized
        return result
