from .base import BaseTool, ToolResult, ToolCategory  # noqa: F401
from .holehe import HoleheTool
from .ghunt import GhuntTool
from .h8mail import H8MailTool
from .emailfinder import EmailFinderTool
from .theharvester import TheHarvesterTool
from .sherlock import SherlockTool
from .maigret import MaigretTool
from .socid_extractor import SocidExtractorTool
from .instaloader import InstaloaderTool
from .facebook_scraper import FacebookScraperTool
from .snscrape import SnscrapeTool
from .censys import CensysTool
from .shodan import ShodanTool
from .waybackpy import WaybackpyTool

TOOL_REGISTRY: list[BaseTool] = [
    HoleheTool(),
    GhuntTool(),
    H8MailTool(),
    EmailFinderTool(),
    TheHarvesterTool(),
    SherlockTool(),
    MaigretTool(),
    SocidExtractorTool(),
    InstaloaderTool(),
    FacebookScraperTool(),
    SnscrapeTool(),
    CensysTool(),
    ShodanTool(),
    WaybackpyTool(),
]

TOOL_MAP: dict[str, BaseTool] = {t.name: t for t in TOOL_REGISTRY}


def get_tools_by_category(category: ToolCategory) -> list[BaseTool]:
    return [t for t in TOOL_REGISTRY if t.category == category]


def get_tool(name: str) -> BaseTool | None:
    return TOOL_MAP.get(name)
