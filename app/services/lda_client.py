from __future__ import annotations

from typing import Any

import httpx

from app.config import get_settings


class LDAClient:
    def __init__(self) -> None:
        self.settings = get_settings()

    async def search_filings_for_bill(self, bill_label: str, limit: int = 10) -> list[dict[str, Any]]:
        if not self.settings.lda_api_key:
            return []

        base = self.settings.lda_api_base_url.rstrip("/")
        endpoint = f"{base}/filings/"
        params = {
            "api_key": self.settings.lda_api_key,
            "ordering": "-dt_posted",
            "page_size": limit,
            "search": bill_label,
        }

        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                response = await client.get(endpoint, params=params)
                response.raise_for_status()
                payload = response.json()
        except Exception:
            return []

        results = payload.get("results", []) if isinstance(payload, dict) else []
        normalized: list[dict[str, Any]] = []

        for item in results:
            filing_uuid = item.get("filing_uuid") or item.get("id") or ""
            specific_issues = item.get("specific_issues", "")
            client_name = (item.get("client") or {}).get("name", "") if isinstance(item.get("client"), dict) else ""
            registrant_name = (
                (item.get("registrant") or {}).get("name", "") if isinstance(item.get("registrant"), dict) else ""
            )
            amount = float(item.get("income") or item.get("expenses") or 0.0)
            normalized.append(
                {
                    "external_id": str(filing_uuid),
                    "registrant": registrant_name,
                    "client": client_name,
                    "specific_issues_text": specific_issues,
                    "filing_period": item.get("filing_period_display", ""),
                    "amount": amount,
                }
            )

        return normalized
