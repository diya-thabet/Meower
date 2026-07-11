from .base import BaseTool, ToolResult, ToolCategory
from ._runner import run_cli


class ShodanTool(BaseTool):
    name = "shodan"
    category = ToolCategory.DOMAIN
    description = "Discover IoT devices, services, and vulnerabilities via Shodan"

    async def run(self, target: str, **kwargs) -> ToolResult:
        result = await run_cli(self.name, self.category, [
            "shodan", "search", target,
        ], timeout=90)

        if result.status != "success":
            return result

        normalized = []
        stdout = result.raw_data.get("stdout", "")
        for line in stdout.splitlines():
            line = line.strip()
            if not line or line.startswith("Search Query"):
                continue
            parts = line.split()
            if len(parts) >= 2:
                normalized.append({
                    "type": "service",
                    "domain": target,
                    "ip": parts[0],
                    "service": " ".join(parts[1:]),
                })

        result.normalized = normalized
        return result
