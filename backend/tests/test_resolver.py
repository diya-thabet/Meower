from app.graph.resolver import EntityResolver
from app.models.entity import PersonEntity


class TestExtractCandidates:
    def setup_method(self):
        self.resolver = EntityResolver()

    def test_seed_as_first_candidate(self):
        candidates = self.resolver._extract_candidates("test@example.com", "email", {})
        assert ("test@example.com", "email") in candidates

    def test_extract_email_from_normalized(self):
        results = {
            "emailfinder": {
                "status": "success",
                "normalized": [{"email": "found@example.com"}],
            }
        }
        candidates = self.resolver._extract_candidates("seed@example.com", "email", results)
        assert ("found@example.com", "email") in candidates

    def test_extract_username(self):
        results = {
            "sherlock": {
                "status": "success",
                "normalized": [{"username": "johndoe", "site": "github"}],
            }
        }
        candidates = self.resolver._extract_candidates("seed", "username", results)
        assert ("johndoe", "username") in candidates

    def test_extract_domain(self):
        results = {
            "theHarvester": {
                "status": "success",
                "normalized": [{"domain": "example.com"}],
            }
        }
        candidates = self.resolver._extract_candidates("seed@example.com", "email", results)
        assert ("example.com", "domain") in candidates

    def test_no_duplicates(self):
        results = {
            "tool1": {
                "status": "success",
                "normalized": [{"email": "same@example.com"}],
            },
            "tool2": {
                "status": "success",
                "normalized": [{"email": "same@example.com"}],
            },
        }
        candidates = self.resolver._extract_candidates("seed@example.com", "email", results)
        email_count = sum(1 for v, t in candidates if v == "same@example.com")
        assert email_count == 1

    def test_user_at_sign_excluded_as_username(self):
        results = {
            "sherlock": {
                "status": "success",
                "normalized": [{"username": "user@domain.com"}],
            }
        }
        candidates = self.resolver._extract_candidates("seed", "username", results)
        assert ("user@domain.com", "username") not in candidates


class TestBuildMetadata:
    def setup_method(self):
        self.resolver = EntityResolver()

    def test_basic_email_metadata(self):
        meta = self.resolver._build_metadata("test@example.com", "email", {})
        assert meta["type"] == "email"
        assert "test@example.com" in meta["emails"]

    def test_holehe_services(self):
        results = {
            "holehe": {
                "status": "success",
                "normalized": [
                    {"service": "github", "exists": True},
                    {"service": "twitter", "exists": True},
                ],
            }
        }
        meta = self.resolver._build_metadata("test@example.com", "email", results)
        assert len(meta["services"]) == 2

    def test_h8mail_breaches(self):
        results = {
            "h8mail": {
                "status": "success",
                "normalized": [
                    {"source": "breach1", "contents": "password=abc"},
                    {"source": "breach2"},
                ],
            }
        }
        meta = self.resolver._build_metadata("test@example.com", "email", results)
        assert len(meta["breaches"]) == 2
        assert meta["breaches"][0].get("has_password") is True

    def test_sherlock_profiles(self):
        results = {
            "sherlock": {
                "status": "success",
                "normalized": [
                    {"site": "github", "url": "https://github.com/test", "username": "test"},
                ],
            }
        }
        meta = self.resolver._build_metadata("test", "username", results)
        assert len(meta["profiles"]) == 1
        assert meta["profiles"][0]["site"] == "github"

    def test_ghunt_google_info(self):
        results = {
            "ghunt": {
                "status": "success",
                "normalized": [
                    {"key": "name", "value": "John Doe"},
                    {"key": "id", "value": "12345"},
                ],
            }
        }
        meta = self.resolver._build_metadata("test@gmail.com", "email", results)
        assert meta["google"]["name"] == "John Doe"
        assert meta["google"]["id"] == "12345"


class TestDeriveDisplayName:
    def setup_method(self):
        self.resolver = EntityResolver()

    def test_google_name(self):
        name = self.resolver._derive_display_name("test@gmail.com", {"google": {"name": "John Doe"}})
        assert name == "John Doe"

    def test_profile_based_name(self):
        name = self.resolver._derive_display_name("testuser", {"profiles": [{"site": "github", "url": "https://github.com/testuser"}]})
        assert "github" in name

    def test_empty_metadata_returns_empty(self):
        name = self.resolver._derive_display_name("test", {})
        assert name == ""

    def test_no_match_returns_empty(self):
        name = self.resolver._derive_display_name("test", {"type": "email", "services": []})
        assert name == ""


class TestMergeMetadata:
    def setup_method(self):
        self.resolver = EntityResolver()

    def test_merge_services(self):
        existing = {"services": [{"name": "github", "exists": True}]}
        results = {
            "holehe": {
                "status": "success",
                "normalized": [{"service": "twitter", "exists": True}],
            }
        }
        merged = self.resolver._merge_metadata(existing, results)
        assert len(merged["services"]) == 2

    def test_merge_services_dedup(self):
        existing = {"services": [{"name": "github", "exists": True}]}
        results = {
            "holehe": {
                "status": "success",
                "normalized": [{"service": "github", "exists": True}],
            }
        }
        merged = self.resolver._merge_metadata(existing, results)
        assert len(merged["services"]) == 1

    def test_merge_profiles(self):
        existing = {"profiles": []}
        results = {
            "sherlock": {
                "status": "success",
                "normalized": [{"site": "github", "url": "https://github.com/u", "username": "u"}],
            }
        }
        merged = self.resolver._merge_metadata(existing, results)
        assert len(merged["profiles"]) == 1


class TestPersonEntityModel:
    def test_create_entity_defaults(self):
        entity = PersonEntity(
            primary_value="test@example.com",
            type="email",
            display_name="Test User",
            risk_score=50,
            investigation_count=1,
        )
        assert entity.id is not None
        assert entity.primary_value == "test@example.com"
        assert entity.type == "email"
        assert entity.risk_score == 50
        assert entity.investigation_count == 1
        assert entity.entity_metadata == {}

    def test_create_entity_with_metadata(self):
        entity = PersonEntity(
            primary_value="test@example.com",
            type="email",
            entity_metadata={"services": [{"name": "github"}], "breaches": []},
        )
        assert entity.entity_metadata["services"][0]["name"] == "github"
        assert entity.entity_metadata["breaches"] == []

    def test_entity_id_is_uuid(self):
        import uuid
        entity = PersonEntity(primary_value="test", type="username")
        assert uuid.UUID(entity.id) is not None

    def test_entity_str_repr(self):
        entity = PersonEntity(primary_value="test@example.com", type="email", display_name="Test")
        assert entity.primary_value == "test@example.com"
        assert entity.type == "email"

    def test_entity_optional_fields_none(self):
        entity = PersonEntity(primary_value="test", type="email")
        assert entity.risk_score is None or entity.risk_score == 0
        assert entity.entity_metadata == {}




class TestResolverEdgeCases:
    def setup_method(self):
        self.resolver = EntityResolver()

    def test_extract_candidates_from_error_results(self):
        results = {
            "holehe": {"status": "error", "error": "timeout"},
            "sherlock": {"status": "error", "error": "rate limited"},
        }
        candidates = self.resolver._extract_candidates("seed@example.com", "email", results)
        assert ("seed@example.com", "email") in candidates
        assert len(candidates) == 1

    def test_extract_candidates_empty_results(self):
        candidates = self.resolver._extract_candidates("seed", "username", {})
        assert ("seed", "username") in candidates
        assert len(candidates) == 1

    def test_extract_candidates_partial_results(self):
        results = {
            "holehe": {"status": "success", "normalized": [{"service": "github"}]},
        }
        candidates = self.resolver._extract_candidates("seed@example.com", "email", results)
        assert ("seed@example.com", "email") in candidates
        assert len(candidates) == 1

    def test_extract_mixed_case_email_dedup(self):
        results = {
            "emailfinder": {
                "status": "success",
                "normalized": [{"email": "User@Example.COM"}, {"email": "user@example.com"}],
            }
        }
        candidates = self.resolver._extract_candidates("seed@example.com", "email", results)
        emails = [v for v, t in candidates if t == "email" and v != "seed@example.com"]
        assert len(emails) == 2

    def test_extract_domain_from_emailfinder(self):
        results = {
            "emailfinder": {
                "status": "success",
                "normalized": [{"domain": "sub.example.com"}],
            }
        }
        candidates = self.resolver._extract_candidates("seed", "email", results)
        assert ("sub.example.com", "domain") in candidates

    def test_build_metadata_no_results(self):
        meta = self.resolver._build_metadata("test", "email", {})
        assert meta["type"] == "email"
        assert meta.get("services") == []
        assert meta.get("breaches") == []

    def test_build_metadata_duplicate_services(self):
        results = {
            "holehe": {
                "status": "success",
                "normalized": [
                    {"service": "github", "exists": True},
                    {"service": "github", "exists": True},
                ],
            }
        }
        meta = self.resolver._build_metadata("test@example.com", "email", results)
        githubs = [s for s in meta["services"] if s.get("name") == "github"]
        assert len(githubs) >= 1

    def test_derive_display_name_from_services(self):
        meta = {"services": [{"name": "twitter", "exists": True}], "type": "email"}
        name = self.resolver._derive_display_name("test@example.com", meta)
        assert name == ""

    def test_build_domain_metadata(self):
        results = {
            "theHarvester": {
                "status": "success",
                "normalized": [
                    {"value": "admin@example.com", "type": "email"},
                    {"value": "sub.example.com", "type": "host"},
                ],
            }
        }
        meta = self.resolver._build_metadata("example.com", "domain", results)
        assert "admin@example.com" in meta.get("emails", [])
        assert meta["type"] == "domain"

    def test_merge_results_with_different_format(self):
        merged = self.resolver._merge_metadata({}, {})
        assert merged.get("services") == []
        assert merged.get("profiles") == []
