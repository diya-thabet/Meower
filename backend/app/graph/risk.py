from typing import Any

BREACH_WEIGHT = 25
SERVICE_WEIGHT = 5
SOCIAL_WEIGHT = 8
PASSWORD_LEAK_WEIGHT = 40
DOMAIN_EXPOSURE_WEIGHT = 10
IP_EXPOSURE_WEIGHT = 15


def calculate_risk_score(seed: str, tool_results: dict[str, Any]) -> int:
    score = 0
    signals: list[str] = []

    for tool, result in tool_results.items():
        if not isinstance(result, dict):
            continue
        if result.get("status") != "success":
            continue
        normalized = result.get("normalized", [])
        if not isinstance(normalized, list):
            continue

        if tool == "holehe":
            registered = sum(1 for item in normalized if item.get("exists"))
            score += registered * SERVICE_WEIGHT
            if registered > 5:
                signals.append("extensive_service_registration")

        elif tool == "h8mail":
            breaches = len(normalized)
            score += breaches * BREACH_WEIGHT
            has_password = any(
                "password" in str(item.get("source", "")).lower()
                or "pass" in str(item.get("contents", "")).lower()
                for item in normalized
            )
            if has_password:
                score += PASSWORD_LEAK_WEIGHT
                signals.append("password_leak")
            if breaches > 0:
                signals.append("data_breach")

        elif tool in ("sherlock", "maigret"):
            accounts = len(normalized)
            score += accounts * SOCIAL_WEIGHT
            if accounts > 5:
                signals.append("wide_social_footprint")
            if accounts > 20:
                signals.append("extreme_social_footprint")

        elif tool == "theHarvester":
            emails = sum(1 for item in normalized if item.get("type") == "email")
            hosts = sum(1 for item in normalized if item.get("type") in ("host", "subdomain"))
            ips = sum(1 for item in normalized if item.get("type") == "ip")
            score += emails * SERVICE_WEIGHT
            score += hosts * DOMAIN_EXPOSURE_WEIGHT
            score += ips * IP_EXPOSURE_WEIGHT
            if hosts > 3:
                signals.append("extensive_infrastructure")

        elif tool == "snscrape":
            score += len(normalized) * SOCIAL_WEIGHT

        elif tool in ("censys", "shodan"):
            exposed = len(normalized)
            score += exposed * DOMAIN_EXPOSURE_WEIGHT
            if exposed > 3:
                signals.append("exposed_services")

    score = min(score, 100)

    if "password_leak" in signals:
        score = max(score, 60)
    if "data_breach" in signals and score < 30:
        score = 30

    return score


def get_risk_label(score: int) -> str:
    if score >= 70:
        return "CRITICAL"
    if score >= 40:
        return "HIGH"
    if score >= 20:
        return "MEDIUM"
    return "LOW"


def get_risk_signals(tool_results: dict[str, Any]) -> list[str]:
    signals: list[str] = []
    for tool, result in tool_results.items():
        if not isinstance(result, dict) or result.get("status") != "success":
            continue
        norm = result.get("normalized", [])
        if not isinstance(norm, list):
            continue
        if tool == "holehe":
            registered = sum(1 for item in norm if item.get("exists"))
            if registered > 10:
                signals.append("Massive service registration")
            elif registered > 5:
                signals.append("Wide service registration")
            elif registered > 0:
                signals.append("Service registration detected")
        elif tool == "h8mail":
            breaches = len(norm)
            if breaches > 2:
                signals.append(f"Found in {breaches} data breaches")
            elif breaches > 0:
                signals.append("Found in data breach")
            has_pass = any("password" in str(item.get("source", "")).lower() or "pass" in str(item.get("contents", "")).lower() for item in norm)
            if has_pass:
                signals.append("Password leaked in breach")
        elif tool in ("sherlock", "maigret"):
            if len(norm) > 20:
                signals.append(f"Extensive social footprint ({len(norm)} accounts)")
            elif len(norm) > 5:
                signals.append(f"Wide social footprint ({len(norm)} accounts)")
        elif tool in ("censys", "shodan"):
            if len(norm) > 5:
                signals.append(f"Multiple exposed services ({len(norm)})")
    return signals
