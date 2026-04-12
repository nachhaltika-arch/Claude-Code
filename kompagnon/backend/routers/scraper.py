"""
Scraper API Router
Endpoints for triggering and monitoring HWK scraper jobs.

Endpoints:
    POST /api/scraper/run          — trigger a scraper run (async background)
    POST /api/scraper/run-batch    — trigger batch scraper (top N trades)
    GET  /api/scraper/status       — list recent runs
    GET  /api/scraper/chambers     — list available chambers + trades
    GET  /api/scraper/health       — scheduler enabled state
    POST /api/scraper/schedule     — enable/disable scheduled runs
"""
import logging
import os
from datetime import datetime
from typing import Optional, List
from threading import Thread

from fastapi import APIRouter, HTTPException, BackgroundTasks, Query
from pydantic import BaseModel

from services.hwk_scraper import HwkScraperService, CHAMBER_CONFIGS, TRADES_MUENCHEN

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/scraper", tags=["Scraper"])


# ── In-memory run log (resets on restart; good enough for manual triggers) ─────
_run_history: List[dict] = []
_current_run: Optional[dict] = None

# ── Scheduler enabled flag (module-level, read by weekly job) ──────────────────
_schedule_enabled: bool = os.getenv("HWK_SCRAPER_ENABLED", "false").lower() == "true"


def is_schedule_enabled() -> bool:
    """Used by automations/scheduler.py to check if weekly job should run."""
    return _schedule_enabled


# ── Pydantic schemas ───────────────────────────────────────────────────────────

class ScrapeRequest(BaseModel):
    chamber: str = "muenchen"
    trade_label: str = "elektrotechnik"
    trade_value: str = "3"
    trade_name: str = "Elektrotechnik"
    cities: Optional[List[str]] = None  # None → use defaults


class BatchScrapeRequest(BaseModel):
    chamber: str = "muenchen"
    max_trades: int = 5  # How many trades from the default list to process


# ── Background runner ──────────────────────────────────────────────────────────

def _run_in_background(request_data: dict):
    """Executes the scraper in a thread and updates run log."""
    global _current_run

    run_id = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
    run_entry = {
        "run_id": run_id,
        "chamber": request_data.get("chamber"),
        "trade": request_data.get("trade_label") or "batch",
        "status": "running",
        "started_at": datetime.utcnow().isoformat(),
        "completed_at": None,
        "result": None,
        "error": None,
    }
    _current_run = run_entry
    _run_history.append(run_entry)

    try:
        service = HwkScraperService()
        if request_data.get("batch"):
            result = service.run_default_batch()
        else:
            result = service.run_chamber(
                chamber=request_data["chamber"],
                trade_label=request_data["trade_label"],
                trade_value=request_data["trade_value"],
                trade_name=request_data["trade_name"],
                cities=request_data.get("cities"),
            )
        run_entry["status"] = "completed"
        run_entry["result"] = result
    except Exception as e:
        logger.error(f"Scraper run failed: {e}", exc_info=True)
        run_entry["status"] = "failed"
        run_entry["error"] = str(e)
    finally:
        run_entry["completed_at"] = datetime.utcnow().isoformat()
        _current_run = None


# ── Endpoints ──────────────────────────────────────────────────────────────────

@router.post("/run", summary="Trigger a single-trade scraper run")
def trigger_scrape(request: ScrapeRequest, background_tasks: BackgroundTasks):
    """
    Trigger HWK scraper for a specific trade + chamber combination.
    Runs in the background — poll /api/scraper/status for progress.
    """
    global _current_run
    if _current_run and _current_run.get("status") == "running":
        raise HTTPException(
            status_code=409,
            detail=f"A scraper run is already in progress: {_current_run['run_id']}",
        )

    data = request.model_dump()
    thread = Thread(target=_run_in_background, args=(data,), daemon=True)
    thread.start()

    return {
        "message": "Scraper started in background",
        "chamber": request.chamber,
        "trade": request.trade_label,
        "cities": f"{len(request.cities)} custom" if request.cities else "default",
        "tip": "Poll GET /api/scraper/status to track progress",
    }


@router.post("/run-batch", summary="Trigger batch scraper (top N trades)")
def trigger_batch(request: BatchScrapeRequest, background_tasks: BackgroundTasks):
    """
    Run the scraper for the top N default trades for the given chamber.
    Default: top 5 München trades with the default city list.
    """
    global _current_run
    if _current_run and _current_run.get("status") == "running":
        raise HTTPException(
            status_code=409,
            detail=f"A scraper run is already in progress: {_current_run['run_id']}",
        )

    data = {"chamber": request.chamber, "batch": True, "trade_label": "batch"}
    thread = Thread(target=_run_in_background, args=(data,), daemon=True)
    thread.start()

    return {
        "message": "Batch scraper started",
        "chamber": request.chamber,
        "max_trades": request.max_trades,
        "tip": "Poll GET /api/scraper/status",
    }


@router.get("/status", summary="Get current + recent run status")
def get_status():
    """
    Returns the current running job (if any) and the last 10 completed runs.
    """
    return {
        "current_run": _current_run,
        "recent_runs": list(reversed(_run_history[-10:])),
        "total_runs": len(_run_history),
    }


@router.get("/chambers", summary="List available chambers and their trades")
def list_chambers():
    """List all configured chambers with available trades."""
    return {
        "chambers": [
            {
                "id": k,
                "name": v["name"],
                "has_detail_pages": v["has_detail_pages"],
            }
            for k, v in CHAMBER_CONFIGS.items()
        ],
        "trades_muenchen": [
            {"label": t["label"], "value": t["value"], "name": t["name"]}
            for t in TRADES_MUENCHEN
        ],
    }


class ScheduleRequest(BaseModel):
    enabled: bool


@router.get("/health", summary="Scheduler status + env config")
def scraper_health():
    """Return whether the weekly auto-scraper is enabled."""
    return {
        "schedule_enabled": _schedule_enabled,
        "current_run": _current_run,
        "total_runs": len(_run_history),
    }


@router.post("/schedule", summary="Enable/disable weekly auto-scraper")
def set_schedule(request: ScheduleRequest):
    """Toggle the weekly auto-scraper flag (read by automations/scheduler.py)."""
    global _schedule_enabled
    _schedule_enabled = bool(request.enabled)
    # Sync env var for legacy code paths that read it directly
    os.environ["HWK_SCRAPER_ENABLED"] = "true" if _schedule_enabled else "false"
    logger.info(f"HWK scraper schedule {'enabled' if _schedule_enabled else 'disabled'}")
    return {"schedule_enabled": _schedule_enabled}
