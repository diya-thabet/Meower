import re
from .base import BaseTool, ToolResult, ToolCategory
from ._runner import run_cli


class EmailFinderTool(BaseTool):
    name = "emailfinder"
    category = ToolCategory.EMAIL
    description = "Discover email addresses from a domain name"

    async def run(self, target: str, **kwargs) -> ToolResult:
        domain = kwargs.get("domain", target)
        result = await run_cli(self.name, self.category, [
            "emailfinder", "-d", domain,
        ], timeout=90)

        if result.status != "success":
            return result

        normalized = []
        stdout = result.raw_data.get("stdout", "")
        email_pattern = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
        found = set()
        for email in email_pattern.findall(stdout):
            if email not in found:
                found.add(email)
                normalized.append({"email": email, "domain": domain, "source": "emailfinder"})

        result.normalized = normalized
        return result
