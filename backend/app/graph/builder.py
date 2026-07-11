import re
from typing import Any

_RE_IP = re.compile(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$")


class GraphBuilder:
    def build(self, seed: str, tool_results: dict[str, Any]) -> dict:
        nodes: list[dict] = []
        edges: list[dict] = []
        seen_nodes: set[str] = set()

        def add_node(node_id: str, label: str, node_type: str, url: str = ""):
            if node_id not in seen_nodes:
                seen_nodes.add(node_id)
                node: dict = {"data": {"id": node_id, "label": label, "type": node_type}}
                if url:
                    node["data"]["url"] = url
                nodes.append(node)

        def add_edge(source: str, target: str, label: str):
            edge_id = f"{source}→{target}"
            edges.append({"data": {"id": edge_id, "source": source, "target": target, "label": label}})

        # Root seed node
        seed_type = self._infer_type(seed)
        add_node("seed", seed, seed_type)

        for tool, result in tool_results.items():
            if not isinstance(result, dict):
                continue
            status = result.get("status", "error")
            if status != "success":
                continue
            normalized = result.get("normalized", [])
            if not isinstance(normalized, list):
                continue

            if tool == "holehe":
                for item in normalized:
                    service = item.get("service", "")
                    exists = item.get("exists", False)
                    if service and exists:
                        sid = f"service:{service}"
                        add_node(sid, service, "service")
                        add_edge("seed", sid, "registered_on")

            elif tool == "ghunt":
                for item in normalized:
                    key = item.get("key", "")
                    val = item.get("value", "")
                    if key == "name" and val:
                        add_node("person:ghunt", val, "person")
                        add_edge("seed", "person:ghunt", "google_account")

            elif tool == "h8mail":
                for item in normalized:
                    source = item.get("source", "")
                    if source:
                        bid = f"breach:{hash(source)}"
                        add_node(bid, source[:40], "breach")
                        add_edge("seed", bid, "found_in_breach")

            elif tool == "emailfinder":
                for item in normalized:
                    email = item.get("email", "")
                    if email:
                        eid = f"email:{email}"
                        add_node(eid, email, "email")
                        add_edge("seed", eid, "associated_email")

            elif tool == "theHarvester":
                for item in normalized:
                    val = item.get("value", "")
                    typ = item.get("type", "")
                    if not val:
                        continue
                    if typ == "email":
                        eid = f"email:{val}"
                        add_node(eid, val, "email")
                        add_edge("seed", eid, "found_email")
                    elif typ in ("host", "subdomain"):
                        hid = f"host:{val}"
                        add_node(hid, val, "domain")
                        add_edge("seed", hid, typ)
                    elif typ == "ip":
                        iid = f"ip:{val}"
                        add_node(iid, val, "ip")
                        add_edge("seed", iid, "resolves_to")

            elif tool in ("sherlock", "maigret", "socid_extractor"):
                for item in normalized:
                    site = item.get("site", "") or item.get("platform", "")
                    url = item.get("url", "")
                    if site:
                        sid = f"{tool}:{site}"
                        label = f"{site} ({item.get('username', '')})"
                        add_node(sid, label, "social", url=url)
                        add_edge("seed", sid, f"found_on_{site}")

            elif tool == "instaloader":
                for item in normalized:
                    username = item.get("username", "")
                    if username:
                        sid = f"instagram:{username}"
                        add_node(sid, f"Instagram/{username}", "social")
                        add_edge("seed", sid, "instagram_profile")

            elif tool == "snscrape":
                platform = result.get("raw_data", {}).get("metadata", {}).get("platform", "social")
                for item in normalized:
                    platform_name = item.get("platform", platform)
                    sid = f"{platform_name}:{item.get('username', seed)}"
                    add_node(sid, f"{platform_name}/{item.get('username', seed)}", "social")
                    add_edge("seed", sid, f"content_on_{platform_name}")

            elif tool in ("censys", "shodan"):
                for item in normalized:
                    val = item.get("value", "") or item.get("ip", "") or item.get("service", "")
                    if val:
                        sid = f"{tool}:{val}"
                        add_node(sid, val[:40], "service")
                        add_edge("seed", sid, f"discovered_by_{tool}")

            elif tool == "waybackpy":
                for item in normalized:
                    url = item.get("url", "")
                    if url:
                        wid = f"wayback:{url}"
                        add_node(wid, url, "archive")
                        add_edge("seed", wid, "wayback_snapshot")

        from .risk import calculate_risk_score, get_risk_label, get_risk_signals

        risk_score = calculate_risk_score(seed, tool_results)
        risk_signals = get_risk_signals(tool_results)

        stats = {
            "total_nodes": len(nodes),
            "total_edges": len(edges),
            "risk_score": risk_score,
            "risk_label": get_risk_label(risk_score),
            "risk_signals": risk_signals,
            "node_counts": self._count_by_type(nodes),
        }
        return {"nodes": nodes, "edges": edges, "stats": stats}

    def _count_by_type(self, nodes: list[dict]) -> dict[str, int]:
        counts: dict[str, int] = {}
        for n in nodes:
            ntype = n.get("data", {}).get("type", "unknown")
            counts[ntype] = counts.get(ntype, 0) + 1
        return counts

    def _infer_type(self, seed: str) -> str:
        if "@" in seed:
            return "email"
        if re.match(r"^[\w.+-]+@[\w-]+\.[\w.]+$", seed):
            return "email"
        if re.match(r"^[\w.+-]+$", seed) and "." in seed:
            return "domain"
        return "username"


def extract_usernames(tool_results: dict) -> list[str]:
    seen = set()
    usernames = []
    for tool, result in tool_results.items():
        if not isinstance(result, dict):
            continue
        norm = result.get("normalized", [])
        if not isinstance(norm, list):
            continue
        for item in norm:
            u = item.get("username", "")
            if u and u not in seen:
                seen.add(u)
                usernames.append(u)
    return usernames


def extract_emails(tool_results: dict) -> list[str]:
    seen = set()
    emails = []
    for tool, result in tool_results.items():
        if not isinstance(result, dict):
            continue
        norm = result.get("normalized", [])
        if not isinstance(norm, list):
            continue
        for item in norm:
            e = item.get("email", "")
            if e and e not in seen:
                seen.add(e)
                emails.append(e)
            # Also check 'value' field for emails
            v = item.get("value", "")
            if "@" in v and v not in seen:
                seen.add(v)
                emails.append(v)
    return emails


def _is_valid_domain(value: str) -> bool:
    if _RE_IP.match(value):
        return False
    return "." in value and " " not in value and "/" not in value


def extract_domains(tool_results: dict) -> list[str]:
    seen = set()
    domains = []
    for tool, result in tool_results.items():
        if not isinstance(result, dict):
            continue
        norm = result.get("normalized", [])
        if not isinstance(norm, list):
            continue
        for item in norm:
            d = item.get("domain", "")
            if d and d not in seen:
                seen.add(d)
                domains.append(d)
            # Extract from value if it looks like a domain
            v = item.get("value", "")
            if v and _is_valid_domain(v) and v not in seen:
                seen.add(v)
                domains.append(v)
    return domains
