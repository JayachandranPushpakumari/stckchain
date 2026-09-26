from fastapi import APIRouter
import pandas as pd
from sqlalchemy import text

from fastapi import BackgroundTasks

from db import engine
from services.screeners import save_breakouts

router = APIRouter()

@router.get("/screen/breakout")
def breakout_screen():

    try:
        df = pd.read_sql(
            text("SELECT * FROM breakout_results"),
            engine
        )
    except Exception:
        return []

    return df.to_dict(orient="records")


@router.post("/screen/breakout/refresh")
def refresh_breakout_screen(background_tasks: BackgroundTasks):
    background_tasks.add_task(save_breakouts)
    return {"status": "accepted", "message": "Breakout screen refresh started in the background."}
