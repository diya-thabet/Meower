from .base import BaseTool, ToolResult, ToolCategory
from ._runner import run_cli


class TheHarvesterTool(BaseTool):
    name = "theHarvester"
    category = ToolCategory.DOMAIN
    description = "Gather emails, subdomains, hosts, and IPs from a domain"

    async def run(self, target: str, **kwargs) -> ToolResult:
        domain = kwargs.get("domain", target)
        result = await run_cli(self.name, self.category, [
            "theHarvester", "-d", domain, "-b", "all",
        ], timeout=120)

        if result.status != "success":
            return result

        normalized = []
        stdout = result.raw_data.get("stdout", "")

        section = None
        for line in stdout.splitlines():
            line = line.strip()
            if line.startswith("["):
                section = line.strip("[]").lower()
                continue
            if section == "emails" and "@" in line:
                normalized.append({"type": "email", "value": line.strip(), "domain": domain})
            elif section == "hosts" and line:
                normalized.append({"type": "host", "value": line, "domain": domain})
            elif section in ("subdomains", "virtual hosts") and line:
                normalized.append({"type": "subdomain", "value": line, "domain": domain})
            elif section == "ips" and line:
                normalized.append({"type": "ip", "value": line, "domain": domain})

        result.normalized = normalized
        return result
