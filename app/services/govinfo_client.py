from __future__ import annotations

from typing import Any

import httpx

from app.config import get_settings


class GovInfoClient:
    BASE_URL = "https://api.govinfo.gov/search"

    def __init__(self) -> None:
        self.settings = get_settings()

    async def search_bills(self, query: str, congress: int = 119, page: int = 1, page_size: int = 10) -> dict[str, Any]:
        if not query.strip() or not self.settings.govinfo_api_key:
            return {"results": [], "total": 0, "page": page, "page_size": page_size}

        page = max(page, 1)
        params = {"api_key": self.settings.govinfo_api_key}
        search_queries = self._build_candidate_queries(query, congress)
        data: dict[str, Any] | None = None
        non_400_error: str = ""

        for candidate in search_queries:
            try:
                data = await self._fetch_page(candidate, params, page, page_size)
                break
            except httpx.HTTPStatusError as exc:
                # Retry with the next candidate for syntax-related 400 errors.
                if exc.response.status_code == 400:
                    continue
                non_400_error = f"GovInfo returned {exc.response.status_code} for this query."
                break
            except httpx.HTTPError:
                non_400_error = "GovInfo search is temporarily unavailable."
                break

        if data is None:
            error_message = non_400_error or "GovInfo could not parse this query. Try fewer words or simpler terms."
            return {
                "results": [],
                "total": 0,
                "page": page,
                "page_size": page_size,
                "error": error_message,
            }

        packages = data.get("packages") or data.get("results") or []
        normalized: list[dict[str, Any]] = []

        for item in packages:
            title = item.get("title") or item.get("packageTitle") or "Untitled bill"
            package_id = item.get("packageId", "")
            bill_number = self._extract_bill_number(item)
            bill_type = self._extract_bill_type(item)
            introduced_date = item.get("dateIssued") or item.get("lastModified") or ""
            normalized.append(
                {
                    "title": title,
                    "package_id": package_id,
                    "congress": int(item.get("congress", congress)),
                    "bill_number": bill_number,
                    "bill_type": bill_type,
                    "introduced_date": introduced_date,
                    "status": item.get("docClass", "Available"),
                }
            )

        return {
            "results": normalized,
            "total": data.get("count", len(normalized)),
            "page": page,
            "page_size": page_size,
            "error": "",
        }

    async def _fetch_page(
        self,
        search_query: str,
        params: dict[str, str],
        page: int,
        page_size: int,
    ) -> dict[str, Any]:
        offset_mark = "*"
        response_payload: dict[str, Any] | None = None

        async with httpx.AsyncClient(timeout=20.0) as client:
            for _ in range(page):
                payload = {
                    "query": search_query,
                    "pageSize": page_size,
                    "offsetMark": offset_mark,
                    "sorts": [{"field": "score", "sortOrder": "DESC"}],
                }
                response = await client.post(self.BASE_URL, params=params, json=payload)
                response.raise_for_status()
                response_payload = response.json()

                next_mark = response_payload.get("offsetMark")
                if not next_mark:
                    break
                offset_mark = str(next_mark)

        return response_payload or {"results": [], "count": 0}

    @staticmethod
    def _build_candidate_queries(query: str, congress: int) -> list[str]:
        escaped_query = query.replace('"', "\\\"").strip()
        compact = " ".join(escaped_query.split())
        terms = [term for term in compact.split(" ") if term]

        base = f"collection:(BILLS) AND congress:{congress} AND "
        candidates: list[str] = []

        # 1) Exact phrase
        candidates.append(f'{base}("{compact}")')

        # 2) AND all words as individual phrases
        if len(terms) > 1:
            and_terms = " AND ".join(f'"{term}"' for term in terms)
            candidates.append(f"{base}({and_terms})")

        # 3) OR all words for a broader query if strict forms fail
        if len(terms) > 1:
            or_terms = " OR ".join(f'"{term}"' for term in terms)
            candidates.append(f"{base}({or_terms})")

        # 4) Last resort: first two terms only
        if len(terms) > 2:
            first_two = " AND ".join(f'"{term}"' for term in terms[:2])
            candidates.append(f"{base}({first_two})")

        return candidates

    @staticmethod
    def _extract_bill_number(item: dict[str, Any]) -> int:
        for key in ("billNumber", "number"):
            raw = item.get(key)
            if isinstance(raw, int):
                return raw
            if isinstance(raw, str):
                digits = "".join(ch for ch in raw if ch.isdigit())
                if digits:
                    return int(digits)

        package_id = item.get("packageId", "")
        digits = "".join(ch for ch in package_id if ch.isdigit())
        return int(digits[-4:]) if digits else 0

    @staticmethod
    def _extract_bill_type(item: dict[str, Any]) -> str:
        value = (item.get("billType") or item.get("type") or "").lower()
        if value:
            return value

        package_id = (item.get("packageId") or "").lower()
        for candidate in ("hr", "s", "hjres", "sjres", "hres", "sres", "hconres", "sconres"):
            if candidate in package_id:
                return candidate

        return "hr"
