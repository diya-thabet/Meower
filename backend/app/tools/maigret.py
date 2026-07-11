import json
import tempfile
from pathlib import Path
from .base import BaseTool, ToolResult, ToolCategory
from ._runner import run_cli


class MaigretTool(BaseTool):
    name = "maigret"
    category = ToolCategory.USERNAME
    description = "Search for a username across 2500+ sites (superset of Sherlock)"

    async def run(self, target: str, **kwargs) -> ToolResult:
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w") as f:
            output_path = f.name

        try:
            result = await run_cli(self.name, self.category, [
                "maigret", target, "--json", output_path,
                "--no-recursion", "--timeout", "15",
            ], timeout=180)

            if Path(output_path).exists():
                try:
                    with open(output_path) as f:
                        data = json.load(f)
                except (json.JSONDecodeError, OSError):
                    data = {}

                if target in data:
                    raw = result.raw_data if result.status == "success" else {}
                    raw["json_output"] = data
                    result.raw_data = raw
                    result.status = "success"

                    normalized = []
                    for site_name, info in data.get(target, {}).items():
                        if isinstance(info, dict):
                            normalized.append({
                                "site": site_name,
                                "username": target,
                                "url": info.get("url", ""),
                                "status": info.get("status", "unknown"),
                            })
                    result.normalized = normalized
        finally:
            try:
                Path(output_path).unlink(missing_ok=True)
            except OSError:
                pass

        return result
