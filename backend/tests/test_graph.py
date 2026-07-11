import pytest
from app.graph.builder import GraphBuilder, extract_usernames, extract_emails, extract_domains


@pytest.fixture
def builder():
    return GraphBuilder()


class TestGraphBuilder:
    def test_build_empty_results(self, builder):
        graph = builder.build("test@example.com", {})
        assert graph["edges"] == []
        assert len(graph["nodes"]) == 1
        assert graph["nodes"][0]["data"]["id"] == "seed"

    def test_build_empty_normalized(self, builder):
        results = {"holehe": {"status": "success", "normalized": []}}
        graph = builder.build("test@example.com", results)
        assert len(graph["nodes"]) == 1
        assert graph["nodes"][0]["data"]["type"] == "email"

    def test_build_email_seed_type(self, builder):
        graph = builder.build("user@domain.com", {})
        assert graph["nodes"][0]["data"]["type"] == "email"

    def test_build_domain_seed_type(self, builder):
        graph = builder.build("example.com", {})
        assert graph["nodes"][0]["data"]["type"] == "domain"

    def test_build_username_seed_type(self, builder):
        graph = builder.build("john_doe", {})
        assert graph["nodes"][0]["data"]["type"] == "username"

    def test_holehe_registered_services(self, builder):
        results = {
            "holehe": {
                "status": "success",
                "normalized": [
                    {"service": "github", "exists": True, "username": "test"},
                    {"service": "twitter", "exists": True, "username": "test"},
                    {"service": "notfound", "exists": False, "username": "test"},
                ],
            }
        }
        graph = builder.build("test@example.com", results)
        service_nodes = [n for n in graph["nodes"] if n["data"]["type"] == "service"]
        assert len(service_nodes) == 2
        service_ids = {n["data"]["id"] for n in service_nodes}
        assert "service:github" in service_ids
        assert "service:twitter" in service_ids

    def test_holehe_skips_non_existent(self, builder):
        results = {
            "holehe": {
                "status": "success",
                "normalized": [{"service": "missing", "exists": False}],
            }
        }
        graph = builder.build("test@example.com", results)
        service_nodes = [n for n in graph["nodes"] if n["data"]["type"] == "service"]
        assert len(service_nodes) == 0

    def test_ghunt_person(self, builder):
        results = {
            "ghunt": {
                "status": "success",
                "normalized": [{"key": "name", "value": "John Doe"}],
            }
        }
        graph = builder.build("test@gmail.com", results)
        person_nodes = [n for n in graph["nodes"] if n["data"]["type"] == "person"]
        assert len(person_nodes) == 1
        assert person_nodes[0]["data"]["label"] == "John Doe"

    def test_h8mail_breaches(self, builder):
        results = {
            "h8mail": {
                "status": "success",
                "normalized": [{"source": "breach1.com"}, {"source": "breach2.com"}],
            }
        }
        graph = builder.build("test@example.com", results)
        breach_nodes = [n for n in graph["nodes"] if n["data"]["type"] == "breach"]
        assert len(breach_nodes) == 2

    def test_theharvester_mixed(self, builder):
        results = {
            "theHarvester": {
                "status": "success",
                "normalized": [
                    {"value": "admin@example.com", "type": "email"},
                    {"value": "mail.example.com", "type": "host"},
                    {"value": "192.168.1.1", "type": "ip"},
                ],
            }
        }
        graph = builder.build("example.com", results)
        types = {n["data"]["type"] for n in graph["nodes"]}
        assert "email" in types
        assert "domain" in types
        assert "ip" in types

    def test_sherlock_socials(self, builder):
        results = {
            "sherlock": {
                "status": "success",
                "normalized": [
                    {"site": "github", "url": "https://github.com/test", "username": "test"},
                    {"site": "twitter", "url": "https://twitter.com/test", "username": "test"},
                ],
            }
        }
        graph = builder.build("test", results)
        social_nodes = [n for n in graph["nodes"] if n["data"]["type"] == "social"]
        assert len(social_nodes) == 2
        assert any("github.com" in n["data"]["url"] for n in social_nodes if "url" in n["data"])

    def test_instaloader(self, builder):
        results = {
            "instaloader": {
                "status": "success",
                "normalized": [{"username": "testuser", "followers": 100}],
            }
        }
        graph = builder.build("testuser", results)
        social_nodes = [n for n in graph["nodes"] if n["data"]["type"] == "social"]
        assert len(social_nodes) == 1
        assert "Instagram" in social_nodes[0]["data"]["label"]

    def test_snscrape(self, builder):
        results = {
            "snscrape": {
                "status": "success",
                "raw_data": {"metadata": {"platform": "twitter"}},
                "normalized": [{"username": "test", "content": "Hello world"}],
            }
        }
        graph = builder.build("test", results)
        social_nodes = [n for n in graph["nodes"] if n["data"]["type"] == "social"]
        assert len(social_nodes) >= 1

    def test_censys_shodan(self, builder):
        results = {
            "censys": {
                "status": "success",
                "normalized": [{"value": "443/https"}, {"value": "22/ssh"}],
            }
        }
        graph = builder.build("example.com", results)
        service_nodes = [n for n in graph["nodes"] if n["data"]["type"] == "service"]
        assert len(service_nodes) == 2
        assert all(s["data"]["id"].startswith("censys:") for s in service_nodes)

    def test_waybackpy(self, builder):
        results = {
            "waybackpy": {
                "status": "success",
                "normalized": [{"url": "https://example.com/old"}, {"url": "https://example.com/new"}],
            }
        }
        graph = builder.build("example.com", results)
        archive_nodes = [n for n in graph["nodes"] if n["data"]["type"] == "archive"]
        assert len(archive_nodes) == 2
        assert all(n["data"]["id"].startswith("wayback:") for n in archive_nodes)

    def test_results_with_non_dicts_are_skipped(self, builder):
        results = {"tool1": "just a string", "tool2": 42, "tool3": ["list"]}
        graph = builder.build("test@example.com", results)
        assert len(graph["nodes"]) == 1

    def test_different_tools_create_separate_nodes(self, builder):
        results = {
            "sherlock": {
                "status": "success",
                "normalized": [
                    {"site": "github", "url": "https://github.com/test", "username": "test"},
                ],
            },
            "maigret": {
                "status": "success",
                "normalized": [
                    {"site": "github", "url": "https://github.com/test", "username": "test"},
                ],
            },
        }
        graph = builder.build("test", results)
        github_nodes = [n for n in graph["nodes"] if "github" in n["data"]["id"]]
        assert len(github_nodes) == 2

    def test_error_status_skips_node_creation(self, builder):
        results = {
            "holehe": {
                "status": "error",
                "normalized": [{"service": "github", "exists": True}],
            }
        }
        graph = builder.build("test@example.com", results)
        assert len(graph["nodes"]) == 1

    def test_edges_seed_to_findings(self, builder):
        results = {
            "holehe": {
                "status": "success",
                "normalized": [{"service": "github", "exists": True, "username": "test"}],
            }
        }
        graph = builder.build("test@example.com", results)
        assert len(graph["edges"]) == 1
        assert graph["edges"][0]["data"]["source"] == "seed"
        assert graph["edges"][0]["data"]["target"] == "service:github"


class TestExtractHelpers:
    def test_extract_usernames(self):
        results = {
            "sherlock": {
                "status": "success",
                "normalized": [{"username": "alice"}, {"username": "bob"}],
            },
            "maigret": {
                "status": "success",
                "normalized": [{"username": "alice"}, {"username": "charlie"}],
            },
        }
        usernames = extract_usernames(results)
        assert len(usernames) == 3
        assert "alice" in usernames
        assert "bob" in usernames
        assert "charlie" in usernames

    def test_extract_usernames_dedup(self):
        results = {
            "sherlock": {
                "status": "success",
                "normalized": [{"username": "alice"}, {"username": "alice"}],
            },
        }
        usernames = extract_usernames(results)
        assert len(usernames) == 1

    def test_extract_emails(self):
        results = {
            "theHarvester": {
                "status": "success",
                "normalized": [{"email": "a@b.com"}, {"email": "c@d.com"}],
            },
        }
        emails = extract_emails(results)
        assert len(emails) == 2

    def test_extract_emails_from_value(self):
        results = {
            "emailfinder": {
                "status": "success",
                "normalized": [{"value": "x@y.com"}, {"value": "not_an_email"}],
            },
        }
        emails = extract_emails(results)
        assert "x@y.com" in emails
        assert "not_an_email" not in emails

    def test_extract_domains(self):
        results = {
            "theHarvester": {
                "status": "success",
                "normalized": [{"domain": "example.com"}],
            },
        }
        domains = extract_domains(results)
        assert "example.com" in domains

    def test_extract_domains_from_value(self):
        results = {
            "censys": {
                "status": "success",
                "normalized": [{"value": "example.org"}],
            },
        }
        domains = extract_domains(results)
        assert "example.org" in domains

    def test_extract_domains_excludes_non_domains(self):
        results = {
            "tool": {
                "status": "success",
                "normalized": [{"value": "hello world"}, {"value": "192.168.1.1"}],
            },
        }
        domains = extract_domains(results)
        assert len(domains) == 0
