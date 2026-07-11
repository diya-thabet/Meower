import json
import logging
from typing import Optional
from openai import OpenAI, APIError
from ..core.config import settings
from .prompts import REPORT_SYSTEM_PROMPT

logger = logging.getLogger(__name__)


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

    async def _call(self, messages: list[dict]) -> str:
        try:
            response = self.client.chat.completions.create(
                model=self._model,
                messages=messages,
                temperature=0.3,
                max_tokens=4096,
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
        for tool, result in data.get("tool_results", {}).items():
            if isinstance(result, dict) and result.get("status") == "success":
                sections.append(f"=== {tool} ===")
                normalized = result.get("normalized", [])
                if normalized:
                    sections.append(json.dumps(normalized, indent=2, ensure_ascii=False))
                else:
                    sections.append(json.dumps(result, indent=2, ensure_ascii=False))
        return "\n".join(sections) if sections else "No data collected."

    async def generate_report(self, data: dict) -> str:
        context = self._build_context(data)
        messages = [
            {"role": "system", "content": REPORT_SYSTEM_PROMPT},
            {"role": "user", "content": f"## Raw Intelligence Data\n{context}\n\nGenerate a full intelligence report."},
        ]
        return await self._call(messages)

    async def generate_summary(self, data: dict) -> str:
        from .prompts import EXECUTIVE_SUMMARY_PROMPT
        context = self._build_context(data)
        messages = [
            {"role": "system", "content": EXECUTIVE_SUMMARY_PROMPT},
            {"role": "user", "content": f"## Data\n{context}"},
        ]
        return await self._call(messages)


llm_service = LLMService()
