import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from app.tools.base import ToolCategory
from app.tools.holehe import HoleheTool
from app.tools.ghunt import GhuntTool
from app.tools.h8mail import H8MailTool
from app.tools.emailfinder import EmailFinderTool
from app.tools.theharvester import TheHarvesterTool
from app.tools.sherlock import SherlockTool
from app.tools.maigret import MaigretTool
from app.tools.socid_extractor import SocidExtractorTool
from app.tools.instaloader import InstaloaderTool
from app.tools.snscrape import SnscrapeTool
from app.tools.censys import CensysTool
from app.tools.shodan import ShodanTool
from app.tools.facebook_scraper import FacebookScraperTool
from app.tools.waybackpy import WaybackpyTool


def mock_cli_result(stdout: str, returncode: int = 0):
    mock_proc = AsyncMock()
    mock_proc.communicate = AsyncMock(return_value=(stdout.encode(), b""))
    mock_proc.returncode = returncode
    return mock_proc


# ── Holehe ──

class TestHoleheTool:
    @pytest.mark.anyio
    async def test_run_finds_services(self):
        tool = HoleheTool()
        stdout = "[+] Twitter\n[+] GitHub\n[-] SomeService (not used)\n[+] Reddit\n"
        with patch("asyncio.create_subprocess_exec", AsyncMock(return_value=mock_cli_result(stdout))):
            result = await tool.run("test@example.com")
        assert result.status == "success"
        assert len(result.normalized) == 4
        assert result.normalized[0] == {"service": "Twitter", "email": "test@example.com", "exists": True}
        assert result.normalized[2]["service"] == "SomeService (not used)"
        assert result.normalized[2]["exists"] is False

    @pytest.mark.anyio
    async def test_run_cli_error(self):
        tool = HoleheTool()
        with patch("asyncio.create_subprocess_exec", AsyncMock(side_effect=FileNotFoundError)):
            result = await tool.run("test@example.com")
        assert result.status == "error"

    @pytest.mark.anyio
    async def test_name_and_category(self):
        assert HoleheTool().name == "holehe"
        assert HoleheTool().category == ToolCategory.EMAIL


# ── GHunt ──

class TestGhuntTool:
    @pytest.mark.anyio
    async def test_run_parses_output(self):
        tool = GhuntTool()
        stdout = "Name: John Doe\nGoogle ID: 12345\nProfile Pic: https://pic.url\n"
        with patch("asyncio.create_subprocess_exec", AsyncMock(return_value=mock_cli_result(stdout))):
            result = await tool.run("john@gmail.com")
        assert result.status == "success"
        assert len(result.normalized) == 3
        assert result.normalized[0] == {"key": "name", "value": "John Doe", "email": "john@gmail.com"}

    @pytest.mark.anyio
    async def test_name_and_category(self):
        assert GhuntTool().name == "ghunt"
        assert GhuntTool().category == ToolCategory.EMAIL


# ── H8Mail ──

class TestH8MailTool:
    @pytest.mark.anyio
    async def test_run_parses_breaches(self):
        tool = H8MailTool()
        stdout = "Breach: Collection1\nemail: test@example.com\nPaste found at example.com\n"
        with patch("asyncio.create_subprocess_exec", AsyncMock(return_value=mock_cli_result(stdout))):
            result = await tool.run("test@example.com")
        assert result.status == "success"
        assert any("Collection1" in str(n) for n in result.normalized)

    @pytest.mark.anyio
    async def test_name_and_category(self):
        assert H8MailTool().name == "h8mail"
        assert H8MailTool().category == ToolCategory.DATA_BREACH


# ── EmailFinder ──

class TestEmailFinderTool:
    @pytest.mark.anyio
    async def test_run_extracts_emails(self):
        tool = EmailFinderTool()
        stdout = "Some text foo@example.com more bar@example.com stuff\n"
        with patch("asyncio.create_subprocess_exec", AsyncMock(return_value=mock_cli_result(stdout))):
            result = await tool.run("example.com")
        assert result.status == "success"
        assert len(result.normalized) == 2
        assert result.normalized[0]["email"] == "foo@example.com"

    @pytest.mark.anyio
    async def test_run_deduplicates(self):
        tool = EmailFinderTool()
        stdout = "foo@example.com foo@example.com"
        with patch("asyncio.create_subprocess_exec", AsyncMock(return_value=mock_cli_result(stdout))):
            result = await tool.run("example.com")
        assert len(result.normalized) == 1

    @pytest.mark.anyio
    async def test_name_and_category(self):
        assert EmailFinderTool().name == "emailfinder"
        assert EmailFinderTool().category == ToolCategory.EMAIL


# ── TheHarvester ──

class TestTheHarvesterTool:
    @pytest.mark.anyio
    async def test_run_parses_sections(self):
        tool = TheHarvesterTool()
        stdout = (
            "[Emails]\n"
            "admin@example.com\n"
            "[Hosts]\n"
            "mail.example.com\n"
            "[Subdomains]\n"
            "api.example.com\n"
            "[IPs]\n"
            "1.2.3.4\n"
        )
        with patch("asyncio.create_subprocess_exec", AsyncMock(return_value=mock_cli_result(stdout))):
            result = await tool.run("example.com")
        assert result.status == "success"
        assert len(result.normalized) == 4
        types = {e["type"] for e in result.normalized}
        assert types == {"email", "host", "subdomain", "ip"}

    @pytest.mark.anyio
    async def test_name_and_category(self):
        assert TheHarvesterTool().name == "theHarvester"
        assert TheHarvesterTool().category == ToolCategory.DOMAIN


# ── Sherlock ──

class TestSherlockTool:
    @pytest.mark.anyio
    async def test_run_parses_found_urls(self):
        tool = SherlockTool()
        stdout = "[+] GitHub: https://github.com/testuser\n[+] Twitter: https://twitter.com/testuser\n"
        with patch("asyncio.create_subprocess_exec", AsyncMock(return_value=mock_cli_result(stdout))):
            result = await tool.run("testuser")
        assert result.status == "success"
        assert len(result.normalized) == 2
        assert result.normalized[0]["site"] == "GitHub"
        assert result.normalized[0]["url"] == "https://github.com/testuser"

    @pytest.mark.anyio
    async def test_name_and_category(self):
        assert SherlockTool().name == "sherlock"
        assert SherlockTool().category == ToolCategory.USERNAME


# ── Maigret ──

class TestMaigretTool:
    @pytest.mark.anyio
    async def test_run_parses_json_output(self):
        import tempfile
        import json as j
        from pathlib import Path
        tool = MaigretTool()
        mock_data = {
            "testuser": {
                "github": {"url": "https://github.com/testuser", "status": "claimed"},
                "twitter": {"url": "https://twitter.com/testuser", "status": "claimed"},
            }
        }
        tmpf = tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w")
        j.dump(mock_data, tmpf)
        tmpf.close()

        mock_proc = AsyncMock()
        mock_proc.communicate = AsyncMock(return_value=(b"", b""))
        mock_proc.returncode = 0

        with (
            patch("tempfile.NamedTemporaryFile") as mock_tmp,
            patch("asyncio.create_subprocess_exec", AsyncMock(return_value=mock_proc)),
            patch("pathlib.Path.unlink"),
        ):
            mock_tmp.return_value.__enter__.return_value.name = tmpf.name
            result = await tool.run("testuser")

        Path(tmpf.name).unlink(missing_ok=True)
        assert result.status == "success"
        assert len(result.normalized) == 2
        assert result.normalized[0]["site"] == "github"

    @pytest.mark.anyio
    async def test_name_and_category(self):
        assert MaigretTool().name == "maigret"
        assert MaigretTool().category == ToolCategory.USERNAME


# ── Socid Extractor ──

class TestSocidExtractorTool:
    @pytest.mark.anyio
    async def test_run_parses_ids(self):
        tool = SocidExtractorTool()
        stdout = "twitter: 12345\ninstagram: 67890\n"
        with patch("asyncio.create_subprocess_exec", AsyncMock(return_value=mock_cli_result(stdout))):
            result = await tool.run("testuser")
        assert result.status == "success"
        assert len(result.normalized) == 2
        assert result.normalized[0] == {"platform": "twitter", "value": "12345", "username": "testuser"}

    @pytest.mark.anyio
    async def test_name_and_category(self):
        assert SocidExtractorTool().name == "socid_extractor"
        assert SocidExtractorTool().category == ToolCategory.USERNAME


# ── Instaloader ──

class TestInstaloaderTool:
    @pytest.mark.anyio
    async def test_run_parses_followers(self):
        tool = InstaloaderTool()
        stdout = "Some output about Profile testuser\nnot matched\n"
        with patch("asyncio.create_subprocess_exec", AsyncMock(return_value=mock_cli_result(stdout))):
            result = await tool.run("testuser")
        assert result.status == "success"
        assert result.normalized[0]["status"] == "found"

    @pytest.mark.anyio
    async def test_name_and_category(self):
        assert InstaloaderTool().name == "instaloader"
        assert InstaloaderTool().category == ToolCategory.SOCIAL


# ── Facebook Scraper (use importlib patching) ──

class TestFacebookScraperTool:
    @pytest.mark.anyio
    async def test_run_uses_library(self):
        import sys
        fake_fb = MagicMock()
        fake_fb.get_profile = MagicMock(return_value={"Name": "John Doe", "Friends": 500, "About": "Bio here"})
        sys.modules["facebook_scraper"] = fake_fb

        tool = FacebookScraperTool()
        result = await tool.run("johndoe")

        sys.modules.pop("facebook_scraper", None)
        assert result.status == "success"
        assert result.normalized[0]["name"] == "John Doe"
        assert result.normalized[0]["followers"] == 500

    @pytest.mark.anyio
    async def test_run_missing_library(self):
        import sys
        sys.modules.pop("facebook_scraper", None)

        tool = FacebookScraperTool()
        result = await tool.run("johndoe")

        assert result.status == "error"
        assert "not installed" in (result.error or "")

    @pytest.mark.anyio
    async def test_name_and_category(self):
        assert FacebookScraperTool().name == "facebook_scraper"
        assert FacebookScraperTool().category == ToolCategory.SOCIAL


# ── Snscrape ──

class TestSnscrapeTool:
    @pytest.mark.anyio
    async def test_run_parses_content(self):
        tool = SnscrapeTool()
        stdout = "first result\nsecond result\n"
        with patch("asyncio.create_subprocess_exec", AsyncMock(return_value=mock_cli_result(stdout))):
            result = await tool.run("testuser", platform="twitter")
        assert result.status == "success"
        assert len(result.normalized) == 2
        assert all(n["platform"] == "twitter" for n in result.normalized)

    @pytest.mark.anyio
    async def test_max_results_limit(self):
        tool = SnscrapeTool()
        stdout = "\n".join([f"line {i}" for i in range(50)])
        with patch("asyncio.create_subprocess_exec", AsyncMock(return_value=mock_cli_result(stdout))):
            result = await tool.run("testuser")
        assert len(result.normalized) <= 20

    @pytest.mark.anyio
    async def test_name_and_category(self):
        assert SnscrapeTool().name == "snscrape"
        assert SnscrapeTool().category == ToolCategory.SOCIAL


# ── Censys ──

class TestCensysTool:
    @pytest.mark.anyio
    async def test_run_parses_lines(self):
        tool = CensysTool()
        stdout = "cert ABC123\ncert DEF456\n"
        with patch("asyncio.create_subprocess_exec", AsyncMock(return_value=mock_cli_result(stdout))):
            result = await tool.run("example.com")
        assert result.status == "success"
        assert len(result.normalized) == 2

    @pytest.mark.anyio
    async def test_name_and_category(self):
        assert CensysTool().name == "censys"
        assert CensysTool().category == ToolCategory.DOMAIN


# ── Shodan ──

class TestShodanTool:
    @pytest.mark.anyio
    async def test_run_parses_results(self):
        tool = ShodanTool()
        stdout = "1.2.3.4 Apache httpd\n5.6.7.8 Nginx\n"
        with patch("asyncio.create_subprocess_exec", AsyncMock(return_value=mock_cli_result(stdout))):
            result = await tool.run("example.com")
        assert result.status == "success"
        assert len(result.normalized) == 2
        assert result.normalized[0]["ip"] == "1.2.3.4"

    @pytest.mark.anyio
    async def test_name_and_category(self):
        assert ShodanTool().name == "shodan"
        assert ShodanTool().category == ToolCategory.DOMAIN


# ── Waybackpy (use importlib patching) ──

class TestWaybackpyTool:
    @pytest.mark.anyio
    async def test_run_uses_library(self):
        tool = WaybackpyTool()
        mock_oldest = MagicMock()
        mock_oldest.__str__ = MagicMock(return_value="2000-01-01")
        mock_newest = MagicMock()
        mock_newest.__str__ = MagicMock(return_value="2026-01-01")

        mock_url = MagicMock()
        mock_url.oldest = MagicMock(return_value=mock_oldest)
        mock_url.newest = MagicMock(return_value=mock_newest)

        with patch("waybackpy.Url", return_value=mock_url):
            result = await tool.run("example.com")
        assert result.status == "success"
        assert len(result.normalized) == 1

    @pytest.mark.anyio
    async def test_run_missing_library(self):
        tool = WaybackpyTool()
        with patch("waybackpy.Url", side_effect=ImportError):
            result = await tool.run("example.com")
        assert result.status == "error"

    @pytest.mark.anyio
    async def test_name_and_category(self):
        assert WaybackpyTool().name == "waybackpy"
        assert WaybackpyTool().category == ToolCategory.DOMAIN


# ── Registry Tests ──

class TestToolRegistry:
    def test_all_tools_registered(self):
        from app.tools import TOOL_REGISTRY, TOOL_MAP
        assert len(TOOL_REGISTRY) >= 14
        assert "holehe" in TOOL_MAP
        assert "sherlock" in TOOL_MAP
        assert "maigret" in TOOL_MAP
        assert "theHarvester" in TOOL_MAP

    def test_all_tools_have_unique_names(self):
        from app.tools import TOOL_REGISTRY
        names = [t.name for t in TOOL_REGISTRY]
        assert len(names) == len(set(names))

    def test_all_tools_have_descriptions(self):
        from app.tools import TOOL_REGISTRY
        for t in TOOL_REGISTRY:
            assert t.description, f"{t.name} has no description"

    def test_get_tools_by_category(self):
        from app.tools import get_tools_by_category
        email_tools = get_tools_by_category(ToolCategory.EMAIL)
        assert len(email_tools) >= 3
        assert all(t.category == ToolCategory.EMAIL for t in email_tools)
        username_tools = get_tools_by_category(ToolCategory.USERNAME)
        assert len(username_tools) >= 3
        social_tools = get_tools_by_category(ToolCategory.SOCIAL)
        assert len(social_tools) >= 2
        domain_tools = get_tools_by_category(ToolCategory.DOMAIN)
        assert len(domain_tools) >= 4
