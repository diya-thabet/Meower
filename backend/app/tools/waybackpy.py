from .base import BaseTool, ToolResult, ToolCategory
from ._runner import _make_result


class WaybackpyTool(BaseTool):
    name = "waybackpy"
    category = ToolCategory.DOMAIN
    description = "Fetch historical snapshots from the Wayback Machine"

    async def run(self, target: str, **kwargs) -> ToolResult:
        try:
            import waybackpy
            url = target if target.startswith("http") else f"https://{target}"
            user_agent = "Meower/1.0"
            wb = waybackpy.Url(url, user_agent)
            oldest = wb.oldest()
            newest = wb.newest()
            normalized = [
                {"type": "wayback_snapshot", "url": url, "oldest": str(oldest) if oldest else "", "newest": str(newest) if newest else ""},
            ]
            return _make_result(
                self.name, self.category, "success",
                raw_data={"oldest": str(oldest), "newest": str(newest)},
                normalized=normalized,
            )
        except ImportError:
            return _make_result(
                self.name, self.category, "error",
                error="waybackpy library not installed",
            )
        except Exception as e:
            return _make_result(
                self.name, self.category, "error",
                error=str(e),
            )
