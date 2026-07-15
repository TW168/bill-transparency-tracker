from __future__ import annotations

from typing import Any

import httpx

from app.config import get_settings


class CongressClient:
    BASE_URL = "https://api.congress.gov/v3"

    def __init__(self) -> None:
        self.settings = get_settings()

    async def get_bill(self, congress: int, bill_type: str, bill_number: int) -> dict[str, Any]:
        if not self.settings.congress_api_key:
            return self._fallback_bill(congress, bill_type, bill_number)

        endpoint = f"{self.BASE_URL}/bill/{congress}/{bill_type}/{bill_number}"
        params = {"api_key": self.settings.congress_api_key}

        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                response = await client.get(endpoint, params=params)
                response.raise_for_status()
                payload = response.json()
        except Exception:
            return self._fallback_bill(congress, bill_type, bill_number)

        bill_data = payload.get("bill") or payload
        return {
            "congress": congress,
            "bill_type": bill_type,
            "bill_number": bill_number,
            "title": bill_data.get("title") or "Untitled Bill",
            "sponsor": self._sponsor_name(bill_data),
            "status": bill_data.get("latestAction", {}).get("text") or "Status unavailable",
            "summary": self._summary_text(bill_data),
            "policy_area": (bill_data.get("policyArea") or {}).get("name", ""),
            "subjects": self._extract_subjects(bill_data),
            "committees": self._extract_names(bill_data.get("committees", [])),
            "actions": self._extract_actions(bill_data.get("actions", [])),
            "text_version_count": len(bill_data.get("textVersions", [])),
        }

    @staticmethod
    def _sponsor_name(bill_data: dict[str, Any]) -> str:
        sponsor = bill_data.get("sponsors", [])
        if sponsor and isinstance(sponsor, list):
            return sponsor[0].get("fullName", "")
        return ""

    @staticmethod
    def _summary_text(bill_data: dict[str, Any]) -> str:
        summaries = bill_data.get("summaries", [])
        if isinstance(summaries, dict):
            summaries = summaries.get("summaries", [])
        if summaries and isinstance(summaries, list) and isinstance(summaries[0], dict):
            return summaries[0].get("text", "")
        return ""

    @staticmethod
    def _extract_subjects(bill_data: dict[str, Any]) -> list[str]:
        subjects = bill_data.get("subjects", {})
        if isinstance(subjects, dict):
            subjects = subjects.get("legislativeSubjects", [])
        return CongressClient._extract_names(subjects)

    @staticmethod
    def _extract_names(items: Any) -> list[str]:
        names: list[str] = []
        if not isinstance(items, list):
            return names

        for item in items:
            if isinstance(item, dict):
                name = item.get("name") or item.get("title") or item.get("text")
                if isinstance(name, str) and name.strip():
                    names.append(name.strip())
            elif isinstance(item, str) and item.strip():
                names.append(item.strip())
        return names

    @staticmethod
    def _extract_actions(actions: Any) -> list[dict[str, str]]:
        if isinstance(actions, dict):
            actions = actions.get("actions", [])
        if not isinstance(actions, list):
            return []

        normalized: list[dict[str, str]] = []
        for action in actions[:25]:
            if isinstance(action, dict):
                normalized.append(
                    {
                        "text": str(action.get("text") or action.get("actionDesc") or "").strip(),
                        "actionDate": str(action.get("actionDate") or "").strip(),
                    }
                )
            elif isinstance(action, str) and action.strip():
                normalized.append({"text": action.strip(), "actionDate": ""})
        return normalized

    @staticmethod
    def _fallback_bill(congress: int, bill_type: str, bill_number: int) -> dict[str, Any]:
        return {
            "congress": congress,
            "bill_type": bill_type,
            "bill_number": bill_number,
            "title": f"{bill_type.upper()} {bill_number} (Live detail unavailable)",
            "sponsor": "",
            "status": "Congress.gov API key missing or invalid",
            "summary": "Set a valid CONGRESS_API_KEY to load official summaries and actions.",
            "policy_area": "",
            "subjects": [],
            "committees": [],
            "actions": [],
            "text_version_count": 0,
        }
