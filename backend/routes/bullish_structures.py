from fastapi import APIRouter, BackgroundTasks

from services.bullish_structures import (
    get_bullish_structure_screen,
    run_bullish_structure_scan,
    start_bullish_structure_scan,
)

router = APIRouter()


@router.get("/screen/bullish-structures")
def bullish_structure_screen(background_tasks: BackgroundTasks):
    result = get_bullish_structure_screen()
    if result.get("status") == "not_started" and start_bullish_structure_scan():
        background_tasks.add_task(run_bullish_structure_scan)
        result["status"] = "scanning"
    return result


@router.post("/screen/bullish-structures/refresh")
def refresh_bullish_structure_screen(background_tasks: BackgroundTasks):
    if start_bullish_structure_scan():
        background_tasks.add_task(run_bullish_structure_scan)
    return get_bullish_structure_screen()
