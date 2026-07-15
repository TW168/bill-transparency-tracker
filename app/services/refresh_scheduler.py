from __future__ import annotations

from apscheduler.schedulers import SchedulerNotRunningError
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.config import get_settings

_scheduler: AsyncIOScheduler | None = None


def start_scheduler() -> None:
    global _scheduler
    if _scheduler is not None:
        return

    settings = get_settings()
    _scheduler = AsyncIOScheduler(timezone="UTC")

    # Lightweight refresh placeholder for cached-bill rechecks.
    _scheduler.add_job(lambda: None, trigger="interval", hours=12, id="cached_bill_refresh")

    if settings.app_env != "test":
        _scheduler.start()


def stop_scheduler() -> None:
    global _scheduler
    if _scheduler is not None:
        try:
            if _scheduler.running:
                _scheduler.shutdown(wait=False)
        except SchedulerNotRunningError:
            pass
        _scheduler = None
