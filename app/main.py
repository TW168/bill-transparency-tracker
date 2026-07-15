from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from app.db import Base, engine
from app.routers.admin import router as admin_router
from app.routers.public import router as public_router
from app.services.refresh_scheduler import start_scheduler, stop_scheduler
from app.templating import templates

# Import models so metadata is populated for create_all.
from app import models as _models  # noqa: F401


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    start_scheduler()
    yield
    stop_scheduler()


app = FastAPI(title="Bill Transparency Tracker", version="0.1.0", lifespan=lifespan)
app.mount("/static", StaticFiles(directory="app/static"), name="static")

app.include_router(public_router)
app.include_router(admin_router)


@app.exception_handler(404)
async def not_found_handler(request: Request, exc: Exception) -> HTMLResponse:
    del exc
    return templates.TemplateResponse(request, "404.html", {"request": request}, status_code=404)


@app.exception_handler(500)
async def server_error_handler(request: Request, exc: Exception) -> HTMLResponse:
    del exc
    return templates.TemplateResponse(request, "500.html", {"request": request}, status_code=500)
