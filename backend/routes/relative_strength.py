from fastapi import APIRouter
import pandas as pd
from db import engine

router = APIRouter()

@router.get("/leaders/rs")
def rs_leaders():

    query = """
    SELECT *
    FROM relative_strength
    ORDER BY rs_score DESC
    LIMIT 100
    """

    df = pd.read_sql(query, engine)
    
    df = df.dropna(subset=['rs_score'])

    return df.to_dict("records")