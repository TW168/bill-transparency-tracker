from __future__ import annotations

from typing import Any

from app.config import get_settings


class AIClient:
    def __init__(self) -> None:
        self.settings = get_settings()

    async def summarize_text(self, text: str) -> str:
        if not text:
            return ""
        if not self.settings.ai_provider:
            return text[:500]

        # Placeholder provider-agnostic shim for v1.
        return text[:500]

    async def suggest_entities(self, bill_title: str, summary: str, filings: list[dict[str, Any]]) -> list[dict[str, str]]:
        if not self.settings.ai_provider:
            return []

        # Provider output is intentionally treated as a suggestion and must be reviewed.
        candidates: list[dict[str, str]] = []
        for filing in filings[:3]:
            client = filing.get("client")
            if client:
                candidates.append(
                    {
                        "name": str(client),
                        "entity_type": "organization",
                        "source": "ai",
                        "evidence": f"AI-suggested from lobbying context for {bill_title}",
                    }
                )

        return candidates
