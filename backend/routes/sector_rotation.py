from fastapi import APIRouter
import pandas as pd
from db import engine

router = APIRouter()

@router.get("/leaders/sectors")
def leaders():

    query = """
    SELECT *
    FROM sector_strength
    ORDER BY strength DESC
    """

    df = pd.read_sql(query, engine)

    return df.to_dict(
        orient="records"
    )