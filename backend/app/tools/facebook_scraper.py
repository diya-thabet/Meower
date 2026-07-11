from .base import BaseTool, ToolResult, ToolCategory
from ._runner import _make_result


class FacebookScraperTool(BaseTool):
    name = "facebook_scraper"
    category = ToolCategory.SOCIAL
    description = "Scrape public Facebook profile data"

    async def run(self, target: str, **kwargs) -> ToolResult:
        try:
            from facebook_scraper import get_profile
            profile = get_profile(target)
            normalized = [{
                "platform": "facebook",
                "username": target,
                "name": profile.get("Name", ""),
                "followers": profile.get("Friends", 0),
                "about": profile.get("About", ""),
            }]
            return _make_result(
                self.name, self.category, "success",
                raw_data={"profile": profile},
                normalized=normalized,
            )
        except ImportError:
            return _make_result(
                self.name, self.category, "error",
                error="facebook_scraper library not installed",
            )
        except Exception as e:
            return _make_result(
                self.name, self.category, "error",
                error=str(e),
            )
