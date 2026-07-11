import re
from .base import BaseTool, ToolResult, ToolCategory
from ._runner import run_cli


class InstaloaderTool(BaseTool):
    name = "instaloader"
    category = ToolCategory.SOCIAL
    description = "Download Instagram profile data, posts, and followers"

    async def run(self, target: str, **kwargs) -> ToolResult:
        result = await run_cli(self.name, self.category, [
            "instaloader", "--no-pictures", "--no-videos",
            "--no-compress-json", f"--dirname-pattern=/tmp/instaloader_{target}",
            target,
        ], timeout=120)

        normalized = []
        if result.status == "success":
            stdout = result.raw_data.get("stdout", "")
            for line in stdout.splitlines():
                line = line.strip()
                m = re.match(r"Profile\s+(\S+).*?followers:\s+(\d+)", line)
                if m:
                    normalized.append({
                        "platform": "instagram",
                        "username": target,
                        "followers": int(m.group(2)),
                    })
                    break
            if not normalized:
                normalized.append({
                    "platform": "instagram",
                    "username": target,
                    "status": "found",
                })

        result.normalized = normalized
        return result
