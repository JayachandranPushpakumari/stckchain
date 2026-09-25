from fastapi import APIRouter

from services.bullish_patterns import scan_bullish_patterns

router = APIRouter()


@router.get("/screen/bullish-patterns")
def bullish_pattern_screen():
    return scan_bullish_patterns(force_refresh=False)


@router.post("/screen/bullish-patterns/refresh")
def refresh_bullish_pattern_screen():
    return scan_bullish_patterns(force_refresh=True)
