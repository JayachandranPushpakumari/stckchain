from fastapi import APIRouter

from services.bullish_patterns import scan_bullish_patterns

router = APIRouter()


@router.get("/screen/bullish-patterns")
def bullish_pattern_screen():
    return scan_bullish_patterns()
