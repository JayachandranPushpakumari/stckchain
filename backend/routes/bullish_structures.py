from fastapi import APIRouter

from services.bullish_structures import scan_bullish_structures

router = APIRouter()


@router.get("/screen/bullish-structures")
def bullish_structure_screen():
    return scan_bullish_structures(force_refresh=False)


@router.post("/screen/bullish-structures/refresh")
def refresh_bullish_structure_screen():
    return scan_bullish_structures(force_refresh=True)
