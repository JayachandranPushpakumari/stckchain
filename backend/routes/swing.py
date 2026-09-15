from fastapi import APIRouter
from services.fundamentals import calculate_fundamental_score

router = APIRouter()

@router.get("/screen/swing")
def swing_screen():

    return calculate_fundamental_score(save_to_db=False)
