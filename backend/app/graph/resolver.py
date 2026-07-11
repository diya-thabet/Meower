import logging
from datetime import datetime, timezone
from typing import Any
from sqlalchemy import select

from ..models.entity import PersonEntity, DomainEntity, EntityEdge
from ..db.session import async_session

logger = logging.getLogger(__name__)


class EntityResolver:
    async def resolve_from_investigation(
        self,
        seed: str,
        seed_type: str,
        tool_results: dict[str, Any],
        risk_score: int,
        investigation_id: str | None = None,
    ) -> list[PersonEntity]:
        entities: list[PersonEntity] = []
        seen_values: set[str] = set()

        candidates = self._extract_candidates(seed, seed_type, tool_results)

        for value, etype in candidates:
            if value in seen_values:
                continue
            seen_values.add(value)
            entity = await self._resolve_entity(value, etype, tool_results, risk_score)
            entities.append(entity)

        await self._link_related_entities(entities, candidates, investigation_id)

        return entities

    def _extract_candidates(
        self, seed: str, seed_type: str, tool_results: dict[str, Any]
    ) -> list[tuple[str, str]]:
        candidates: list[tuple[str, str]] = [(seed, seed_type)]
        seen: set[str] = {seed}

        for tool, result in tool_results.items():
            if not isinstance(result, dict) or result.get("status") != "success":
                continue
            normalized = result.get("normalized", [])
            if not isinstance(normalized, list):
                continue

            for item in normalized:
                if not isinstance(item, dict):
                    continue

                email = item.get("email")
                if not email:
                    v = item.get("value", "")
                    email = v if "@" in v else None
                if email and email not in seen:
                    seen.add(email)
                    candidates.append((email, "email"))

                username = item.get("username")
                if username and username not in seen and "@" not in username:
                    seen.add(username)
                    candidates.append((username, "username"))

                domain = item.get("domain")
                if domain and domain not in seen and "." in domain:
                    seen.add(domain)
                    candidates.append((domain, "domain"))

                value = item.get("value", "")
                if value and value not in seen and "." in value and " " not in value and "/" not in value and "@" not in value:
                    seen.add(value)
                    candidates.append((value, "domain"))

        return candidates

    async def _resolve_entity(
        self,
        value: str,
        etype: str,
        tool_results: dict[str, Any],
        risk_score: int,
    ) -> PersonEntity | DomainEntity:
        if etype == "domain":
            return await self._resolve_domain(value, tool_results, risk_score)
        return await self._resolve_person(value, etype, tool_results, risk_score)

    async def _resolve_domain(
        self,
        domain: str,
        tool_results: dict[str, Any],
        risk_score: int,
    ) -> DomainEntity:
        async with async_session() as db:
            result = await db.execute(
                select(DomainEntity).where(DomainEntity.domain == domain)
            )
            existing = result.scalar_one_or_none()

            if existing:
                existing.last_seen = datetime.now(timezone.utc)
                existing.risk_score = max(existing.risk_score, risk_score)
                await db.commit()
                await db.refresh(existing)
                return existing

            entity = DomainEntity(
                domain=domain,
                risk_score=risk_score,
                first_seen=datetime.now(timezone.utc),
                last_seen=datetime.now(timezone.utc),
            )
            db.add(entity)
            await db.commit()
            await db.refresh(entity)
            return entity

    async def _resolve_person(
        self,
        value: str,
        etype: str,
        tool_results: dict[str, Any],
        risk_score: int,
    ) -> PersonEntity:
        async with async_session() as db:
            result = await db.execute(
                select(PersonEntity).where(PersonEntity.primary_value == value)
            )
            existing = result.scalar_one_or_none()

            if existing:
                existing.investigation_count += 1
                existing.last_seen = datetime.now(timezone.utc)
                existing.risk_score = max(existing.risk_score, risk_score)
                enriched = self._enrich_entity_metadata(existing, tool_results)
                if enriched:
                    existing.entity_metadata = enriched
                display = self._derive_display_name(value, existing.entity_metadata)
                if display:
                    existing.display_name = display
                await db.commit()
                await db.refresh(existing)
                return existing

            metadata = self._build_metadata(value, etype, tool_results)
            display_name = self._derive_display_name(value, metadata) or value

            entity = PersonEntity(
                primary_value=value,
                type=etype,
                display_name=display_name,
                risk_score=risk_score,
                investigation_count=1,
                first_seen=datetime.now(timezone.utc),
                last_seen=datetime.now(timezone.utc),
                entity_metadata=metadata,
            )
            self._apply_metadata_to_columns(entity, metadata)
            db.add(entity)
            await db.commit()
            await db.refresh(entity)
            return entity

    def _apply_metadata_to_columns(self, entity: PersonEntity, metadata: dict) -> None:
        google = metadata.get("google", {})
        if google.get("id"):
            entity.google_id = google["id"]
        profiles = metadata.get("profiles", [])
        if profiles:
            entity.profile_urls = profiles
            ids_map = {}
            for p in profiles:
                if isinstance(p, dict) and p.get("site"):
                    ids_map[p["site"]] = p.get("url", "")
            if ids_map:
                entity.social_ids = ids_map
        breaches = metadata.get("breaches", [])
        if breaches:
            entity.data_breaches = breaches
        services = metadata.get("services", [])
        if services:
            entity.services = services
        domains = metadata.get("domains", [])
        if domains:
            entity.associated_domains = domains

    def _enrich_entity_metadata(self, entity: PersonEntity, tool_results: dict[str, Any]) -> dict | None:
        merged = self._merge_metadata(entity.entity_metadata or {}, tool_results)
        if merged != entity.entity_metadata:
            self._apply_metadata_to_columns(entity, merged)
            return merged
        return None

    async def _link_related_entities(
        self,
        entities: list[PersonEntity | DomainEntity],
        candidates: list[tuple[str, str]],
        investigation_id: str | None = None,
    ) -> None:
        if len(entities) < 2:
            return

        entity_map: dict[str, PersonEntity | DomainEntity] = {}
        for e in entities:
            if isinstance(e, PersonEntity):
                entity_map[e.primary_value] = e
            elif isinstance(e, DomainEntity):
                entity_map[e.domain] = e

        for i in range(len(candidates)):
            for j in range(i + 1, len(candidates)):
                val_i, type_i = candidates[i]
                val_j, type_j = candidates[j]
                entity_i = entity_map.get(val_i)
                entity_j = entity_map.get(val_j)
                if not entity_i or not entity_j:
                    continue

                type_i, type_j = candidates[i][1], candidates[j][1]
                rel = self._derive_relationship(type_i, type_j)
                if rel:
                    await self._create_edge(entity_i, entity_j, rel, investigation_id)

    def _derive_relationship(self, type_a: str, type_b: str) -> str | None:
        pairs = {(type_a, type_b), (type_b, type_a)}
        if ("email", "username") in pairs:
            return "HAS_USERNAME"
        if ("email", "domain") in pairs:
            return "REGISTERED_DOMAIN"
        if ("username", "domain") in pairs:
            return "ASSOCIATED_ACCOUNT"
        if ("email", "email") in pairs:
            return "ASSOCIATED_EMAIL"
        if ("username", "username") in pairs:
            return "SOCIAL_CONNECTION"
        if ("domain", "domain") in pairs:
            return "ASSOCIATED_DOMAIN"
        return None

    async def _create_edge(
        self,
        source: PersonEntity | DomainEntity,
        target: PersonEntity | DomainEntity,
        relationship: str,
        investigation_id: str | None = None,
    ) -> EntityEdge | None:
        async with async_session() as db:
            existing = await db.execute(
                select(EntityEdge).where(
                    EntityEdge.source_entity_id == source.id,
                    EntityEdge.target_entity_id == target.id,
                    EntityEdge.relationship == relationship,
                )
            )
            if existing.scalar_one_or_none():
                return None

            edge = EntityEdge(
                source_entity_id=source.id,
                source_type="person" if isinstance(source, PersonEntity) else "domain",
                target_entity_id=target.id,
                target_type="person" if isinstance(target, PersonEntity) else "domain",
                relationship=relationship,
                investigation_id=investigation_id,
                first_seen=datetime.now(timezone.utc),
            )
            db.add(edge)
            await db.commit()
            await db.refresh(edge)
            return edge

    def _build_metadata(self, value: str, etype: str, tool_results: dict[str, Any]) -> dict:
        metadata: dict = {"type": etype, "services": [], "breaches": [], "profiles": [], "emails": [], "domains": []}

        if etype == "email":
            metadata["emails"].append(value)
        elif etype == "domain":
            metadata["domains"].append(value)

        for tool, result in tool_results.items():
            if not isinstance(result, dict) or result.get("status") != "success":
                continue
            normalized = result.get("normalized", [])
            if not isinstance(normalized, list):
                continue

            for item in normalized:
                if not isinstance(item, dict):
                    continue

                if tool == "holehe":
                    service = item.get("service")
                    if service and service not in metadata["services"]:
                        metadata["services"].append({"name": service, "exists": item.get("exists", False)})

                elif tool == "ghunt":
                    key = item.get("key", "")
                    val = item.get("value", "")
                    if key and val:
                        metadata.setdefault("google", {})[key] = val

                elif tool == "h8mail":
                    source = item.get("source", "")
                    if source:
                        breach = {"source": source[:100]}
                        if "password" in str(item.get("contents", "")).lower() or "pass" in str(item.get("source", "")).lower():
                            breach["has_password"] = True
                        if breach not in metadata["breaches"]:
                            metadata["breaches"].append(breach)

                elif tool in ("sherlock", "maigret"):
                    site = item.get("site", "") or item.get("platform", "")
                    url = item.get("url", "")
                    if site:
                        profile = {"site": site, "url": url}
                        if profile not in metadata["profiles"]:
                            metadata["profiles"].append(profile)

                elif tool == "theHarvester":
                    val = item.get("value", "")
                    typ = item.get("type", "")
                    if typ == "email" and val and val not in metadata["emails"]:
                        metadata["emails"].append(val)
                    elif typ in ("host", "subdomain") and val and val not in metadata["domains"]:
                        metadata["domains"].append(val)

                elif tool == "emailfinder":
                    email = item.get("email", "")
                    if email and email not in metadata["emails"]:
                        metadata["emails"].append(email)

        return metadata

    def _merge_metadata(self, existing: dict, tool_results: dict[str, Any]) -> dict:
        merged = dict(existing)
        for key in ("services", "breaches", "profiles", "emails", "domains"):
            existing_list = merged.get(key, [])
            if not isinstance(existing_list, list):
                existing_list = []
            merged[key] = existing_list

        seen_items: dict[str, set] = {}
        for key in ("services", "breaches", "profiles", "emails", "domains"):
            seen_items[key] = set()
            for item in merged.get(key, []):
                if isinstance(item, dict):
                    seen_items[key].add(str(item.get("name", item.get("source", item.get("site", item.get("username", str(item)))))))
                elif isinstance(item, str):
                    seen_items[key].add(item)

        for tool, result in tool_results.items():
            if not isinstance(result, dict) or result.get("status") != "success":
                continue
            normalized = result.get("normalized", [])
            if not isinstance(normalized, list):
                continue

            for item in normalized:
                if not isinstance(item, dict):
                    continue

                if tool == "holehe":
                    service = item.get("service")
                    if service and service not in seen_items["services"]:
                        seen_items["services"].add(service)
                        merged.setdefault("services", []).append({"name": service, "exists": item.get("exists", False)})

                elif tool in ("sherlock", "maigret"):
                    site = item.get("site", "") or item.get("platform", "")
                    if site and site not in seen_items.get("profiles", set()):
                        seen_items.setdefault("profiles", set()).add(site)
                        merged.setdefault("profiles", []).append({"site": site, "url": item.get("url", "")})

        return merged

    def _derive_display_name(self, value: str, metadata: dict) -> str:
        if not metadata:
            return ""
        google = metadata.get("google", {})
        if google.get("name"):
            return google["name"]
        for profile in metadata.get("profiles", []):
            if isinstance(profile, dict):
                site_name = profile.get("site", "")
                if site_name and profile.get("url"):
                    return f"{site_name}/{value}"
        return ""
