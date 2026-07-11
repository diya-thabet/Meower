from .base import BaseTool, ToolResult, ToolCategory
from ._runner import run_cli, _make_result


class CensysTool(BaseTool):
    name = "censys"
    category = ToolCategory.DOMAIN
    description = "Discover SSL certificates, open ports, and services via Censys"

    async def run(self, target: str, **kwargs) -> ToolResult:
        result = await run_cli(self.name, self.category, [
            "censys", "certificates", target,
        ], timeout=90)

        if result.status != "success":
            return result

        normalized = []
        stdout = result.raw_data.get("stdout", "")
        for line in stdout.splitlines():
            line = line.strip()
            if line and not line.startswith("{"):
                normalized.append({
                    "type": "certificate",
                    "domain": target,
                    "value": line,
                })

        result.normalized = normalized
        return result
