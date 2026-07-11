import json
import logging
from typing import Optional
from openai import OpenAI, APIError
from ..core.config import settings

logger = logging.getLogger(__name__)


_REPORT_PROMPTS: dict[str, str] = {}


def _get_prompt(name: str) -> str:
    if not _REPORT_PROMPTS:
        from .prompts import (
            REPORT_SYSTEM_PROMPT,
            EXECUTIVE_SUMMARY_PROMPT,
            SOCIAL_PROFILE_PROMPT,
            BREACH_ANALYSIS_PROMPT,
            RISK_ASSESSMENT_PROMPT,
            DOSSIER_PROMPT,
        )
        _REPORT_PROMPTS["full"] = REPORT_SYSTEM_PROMPT
        _REPORT_PROMPTS["summary"] = EXECUTIVE_SUMMARY_PROMPT
        _REPORT_PROMPTS["social"] = SOCIAL_PROFILE_PROMPT
        _REPORT_PROMPTS["breach"] = BREACH_ANALYSIS_PROMPT
        _REPORT_PROMPTS["risk"] = RISK_ASSESSMENT_PROMPT
        _REPORT_PROMPTS["dossier"] = DOSSIER_PROMPT
    return _REPORT_PROMPTS.get(name, _REPORT_PROMPTS["full"])


class LLMService:
    def __init__(self):
        self._client: Optional[OpenAI] = None
        self._model: str = settings.fanar_model

    @property
    def client(self) -> OpenAI:
        if self._client is None:
            if not settings.fanar_api_key:
                raise RuntimeError(
                    "FANAR_API_KEY is not set. "
                    "Get one at https://api.fanar.qa/request"
                )
            self._client = OpenAI(
                api_key=settings.fanar_api_key,
                base_url=settings.fanar_base_url,
                timeout=settings.fanar_timeout,
                max_retries=2,
            )
        return self._client

    @property
    def available(self) -> bool:
        return bool(settings.fanar_api_key)

    @property
    def report_types(self) -> list[dict]:
        return [
            {"id": "full", "name": "Full Intelligence Report", "description": "Comprehensive report with all findings"},
            {"id": "summary", "name": "Executive Summary", "description": "3-paragraph executive summary"},
            {"id": "social", "name": "Social Profile Analysis", "description": "Social media footprint analysis"},
            {"id": "breach", "name": "Data Breach Analysis", "description": "Breach exposure and remediation"},
            {"id": "risk", "name": "Risk Assessment", "description": "Structured risk scoring and mitigations"},
            {"id": "dossier", "name": "Full Dossier", "description": "Complete intelligence dossier"},
        ]

    async def _call(self, messages: list[dict], temperature: float = 0.3, max_tokens: int = 4096) -> str:
        try:
            response = self.client.chat.completions.create(
                model=self._model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            return response.choices[0].message.content or ""
        except APIError as e:
            logger.error("Fanar API error: %s", e)
            raise
        except Exception as e:
            logger.error("LLM call failed: %s", e)
            raise

    def _build_context(self, data: dict) -> str:
        sections = []

        seed = data.get("seed", "")
        if seed:
            sections.append(f"Target: {seed}")
            sections.append(f"Type: {data.get('type', 'unknown')}")

        graph = data.get("graph")
        if graph:
            nodes = graph.get("nodes", [])
            edges = graph.get("edges", [])
            stats = graph.get("stats", {})
            sections.append("=== Relationship Graph ===")
            sections.append(f"Nodes: {stats.get('total_nodes', len(nodes))}")
            sections.append(f"Edges: {stats.get('total_edges', len(edges))}")
            sections.append(f"Risk Score: {stats.get('risk_score', 'N/A')}")
            sections.append(f"Risk Label: {stats.get('risk_label', 'N/A')}")
            if nodes:
                sections.append("Nodes:")
                for n in nodes[:30]:
                    d = n.get("data", {})
                    sections.append(f"  - {d.get('type', '?')}: {d.get('label', '?')}")
            if edges:
                sections.append("Edges:")
                for e in edges[:30]:
                    d = e.get("data", {})
                    sections.append(f"  - {d.get('source', '?')} --[{d.get('label', '?')}]--> {d.get('target', '?')}")

        entities = data.get("entities", [])
        if entities:
            sections.append("=== Persisted Entities ===")
            for ent in entities[:20]:
                if isinstance(ent, dict):
                    sections.append(f"  - {ent.get('type', '?')}: {ent.get('primary_value', '?')} (risk: {ent.get('risk_score', '?')})")

        risk_signals = data.get("risk_signals", [])
        if risk_signals:
            sections.append("=== Risk Signals ===")
            for s in risk_signals:
                sections.append(f"  - {s}")

        tool_results = data.get("tool_results", {})
        if tool_results:
            sections.append("=== Tool Results ===")
            for tool, result in tool_results.items():
                if isinstance(result, dict) and result.get("status") == "success":
                    sections.append(f"--- {tool} ---")
                    normalized = result.get("normalized", [])
                    if normalized:
                        sections.append(json.dumps(normalized, indent=2, ensure_ascii=False)[:4000])
                    else:
                        raw = json.dumps(result, indent=2, ensure_ascii=False)
                        sections.append(raw[:2000])

        return "\n".join(sections) if sections else "No data collected."

    async def generate_report(self, data: dict, report_type: str = "full") -> str:
        prompt = _get_prompt(report_type)
        context = self._build_context(data)
        user_msg = f"## Intelligence Data\n{context}\n\nGenerate the report based on the above data."
        messages = [
            {"role": "system", "content": prompt},
            {"role": "user", "content": user_msg},
        ]
        temperature = 0.4 if report_type == "dossier" else 0.3
        max_tokens = 8192 if report_type == "dossier" else 4096
        return await self._call(messages, temperature=temperature, max_tokens=max_tokens)

    async def generate_summary(self, data: dict) -> str:
        return await self.generate_report(data, report_type="summary")

    async def generate_social_profile(self, data: dict) -> str:
        return await self.generate_report(data, report_type="social")

    async def generate_breach_analysis(self, data: dict) -> str:
        return await self.generate_report(data, report_type="breach")

    async def generate_risk_assessment(self, data: dict) -> str:
        return await self.generate_report(data, report_type="risk")

    async def generate_dossier(self, data: dict) -> str:
        return await self.generate_report(data, report_type="dossier")


llm_service = LLMService()
