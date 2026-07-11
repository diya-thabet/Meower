import pytest
from app.graph.risk import calculate_risk_score, get_risk_label, get_risk_signals


class TestRiskScore:
    def test_empty_results_zero_score(self):
        assert calculate_risk_score("test@example.com", {}) == 0

    def test_breach_score(self):
        results = {
            "h8mail": {
                "status": "success",
                "normalized": [{"source": "breach1"}, {"source": "breach2"}],
            }
        }
        score = calculate_risk_score("test@example.com", results)
        assert score >= 50

    def test_breach_with_password(self):
        results = {
            "h8mail": {
                "status": "success",
                "normalized": [
                    {"source": "breach1", "contents": "password123"},
                ],
            }
        }
        score = calculate_risk_score("test@example.com", results)
        assert score >= 60

    def test_social_footprint_score(self):
        results = {
            "sherlock": {
                "status": "success",
                "normalized": [{"site": f"site{i}", "url": f"https://site{i}.com/test", "username": "test"} for i in range(10)],
            }
        }
        score = calculate_risk_score("test", results)
        assert score >= 40

    def test_domain_exposure(self):
        results = {
            "theHarvester": {
                "status": "success",
                "normalized": [
                    {"value": "mail.example.com", "type": "host"},
                    {"value": "www.example.com", "type": "host"},
                    {"value": "192.168.1.1", "type": "ip"},
                ],
            }
        }
        score = calculate_risk_score("example.com", results)
        assert score >= 20

    def test_service_registration(self):
        results = {
            "holehe": {
                "status": "success",
                "normalized": [{"service": f"s{i}", "exists": True} for i in range(6)],
            }
        }
        score = calculate_risk_score("test@example.com", results)
        assert score >= 30

    def test_score_capped_at_100(self):
        results = {
            "h8mail": {
                "status": "success",
                "normalized": [{"source": f"breach{i}", "contents": f"password{i}"} for i in range(10)],
            },
            "sherlock": {
                "status": "success",
                "normalized": [{"site": f"site{i}", "url": f"https://site{i}.com/t", "username": "t"} for i in range(50)],
            },
        }
        score = calculate_risk_score("test@example.com", results)
        assert score == 100

    def test_non_dict_results_skipped(self):
        results = {"tool1": "string", "tool2": 42}
        assert calculate_risk_score("test@example.com", results) == 0

    def test_error_status_skipped(self):
        results = {
            "holehe": {
                "status": "error",
                "normalized": [{"service": "github", "exists": True}],
            }
        }
        assert calculate_risk_score("test@example.com", results) == 0

    def test_multiple_tools_combined(self):
        results = {
            "holehe": {
                "status": "success",
                "normalized": [{"service": "github", "exists": True}, {"service": "twitter", "exists": True}],
            },
            "sherlock": {
                "status": "success",
                "normalized": [{"site": "github", "url": "https://github.com/test", "username": "test"}],
            },
        }
        score = calculate_risk_score("test@example.com", results)
        assert 15 <= score <= 30


class TestRiskLabel:
    def test_low(self):
        assert get_risk_label(0) == "LOW"
        assert get_risk_label(19) == "LOW"

    def test_medium(self):
        assert get_risk_label(20) == "MEDIUM"
        assert get_risk_label(39) == "MEDIUM"

    def test_high(self):
        assert get_risk_label(40) == "HIGH"
        assert get_risk_label(69) == "HIGH"

    def test_critical(self):
        assert get_risk_label(70) == "CRITICAL"
        assert get_risk_label(100) == "CRITICAL"


class TestRiskSignals:
    def test_empty_signals(self):
        assert get_risk_signals({}) == []

    def test_breach_signal(self):
        results = {
            "h8mail": {
                "status": "success",
                "normalized": [{"source": "breach1"}],
            }
        }
        signals = get_risk_signals(results)
        assert any("data breach" in s.lower() for s in signals)

    def test_password_leak_signal(self):
        results = {
            "h8mail": {
                "status": "success",
                "normalized": [{"source": "breach1", "contents": "password=123"}],
            }
        }
        signals = get_risk_signals(results)
        assert any("password" in s.lower() for s in signals)

    def test_social_footprint_signal(self):
        results = {
            "maigret": {
                "status": "success",
                "normalized": [{"site": f"site{i}", "url": f"https://s{i}.com/t", "username": "t"} for i in range(10)],
            }
        }
        signals = get_risk_signals(results)
        assert any("social" in s.lower() for s in signals)

    def test_extreme_social_footprint(self):
        results = {
            "sherlock": {
                "status": "success",
                "normalized": [{"site": f"site{i}", "url": f"https://s{i}.com/t", "username": "t"} for i in range(25)],
            }
        }
        signals = get_risk_signals(results)
        assert any("extensive" in s.lower() for s in signals)

    def test_censys_signal(self):
        results = {
            "censys": {
                "status": "success",
                "normalized": [{"value": "443/https"} for _ in range(6)],
            }
        }
        signals = get_risk_signals(results)
        assert any("exposed" in s.lower() for s in signals)
