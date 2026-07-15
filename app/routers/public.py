from __future__ import annotations

import math

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import HTMLResponse, JSONResponse
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db import get_db
from app.services.analysis_service import AnalysisService
from app.services.govinfo_client import GovInfoClient
from app.templating import templates

router = APIRouter()


def _pagination(total: int, page: int, page_size: int) -> dict[str, int]:
    total_pages = max(1, math.ceil(total / page_size))
    return {
        "page": page,
        "page_size": page_size,
        "total": total,
        "total_pages": total_pages,
        "has_prev": page > 1,
        "has_next": page < total_pages,
    }


@router.get("/", response_class=HTMLResponse)
async def home(request: Request, db: Session = Depends(get_db)) -> HTMLResponse:
    analysis = AnalysisService()
    featured = analysis.get_cached_recent_bills(db)
    return templates.TemplateResponse(request, "home.html", {"request": request, "featured": featured})


@router.get("/search", response_class=HTMLResponse)
async def search(
    request: Request,
    q: str = Query(default=""),
    congress: int = Query(default=get_settings().default_congress),
    page: int = Query(default=1, ge=1),
    db: Session = Depends(get_db),
) -> HTMLResponse:
    del db
    settings = get_settings()
    page_size = 10
    client = GovInfoClient()
    payload = await client.search_bills(query=q, congress=congress, page=page, page_size=page_size)
    pager = _pagination(payload["total"], payload["page"], payload["page_size"])
    return templates.TemplateResponse(
        request,
        "search_results.html",
        {
            "request": request,
            "query": q,
            "congress": congress,
            "results": payload["results"],
            "pager": pager,
            "govinfo_api_configured": bool(settings.govinfo_api_key.strip()),
            "search_error": payload.get("error", ""),
        },
    )


@router.get("/bills/{congress}/{bill_type}/{number}", response_class=HTMLResponse)
async def bill_detail(
    request: Request,
    congress: int,
    bill_type: str,
    number: int,
    db: Session = Depends(get_db),
) -> HTMLResponse:
    analysis = AnalysisService()
    context = await analysis.get_or_build_bill_analysis(db, congress, bill_type.lower(), number)
    return templates.TemplateResponse(request, "bill_detail.html", {"request": request, **context})


@router.get("/about", response_class=HTMLResponse)
async def about(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(request, "about.html", {"request": request})


@router.get("/healthz")
async def healthz() -> JSONResponse:
    return JSONResponse({"status": "ok"})
