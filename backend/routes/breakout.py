from fastapi import APIRouter
from services.screeners import find_breakouts

router = APIRouter()

@router.get("/screen/breakout")
def breakout_screen():

    return find_breakouts()