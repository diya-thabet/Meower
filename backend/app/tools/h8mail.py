from .base import BaseTool, ToolResult, ToolCategory
from ._runner import run_cli


class H8MailTool(BaseTool):
    name = "h8mail"
    category = ToolCategory.DATA_BREACH
    description = "Data breach and paste lookup for email addresses"

    async def run(self, target: str, **kwargs) -> ToolResult:
        result = await run_cli(self.name, self.category, [
            "h8mail", "-t", target,
        ], timeout=90)

        if result.status != "success":
            return result

        normalized = []
        stdout = result.raw_data.get("stdout", "")
        current_breach = {}
        for line in stdout.splitlines():
            line = line.strip()
            if "breach" in line.lower() or "leak" in line.lower():
                if current_breach:
                    normalized.append(current_breach)
                current_breach = {"source": line, "email": target}
            elif ":" in line and current_breach:
                k, v = line.split(":", 1)
                current_breach[k.strip().lower().replace(" ", "_")] = v.strip()
            elif "paste" in line.lower():
                normalized.append({"source": "paste", "email": target, "content": line})
        if current_breach:
            normalized.append(current_breach)

        result.normalized = normalized
        return result
