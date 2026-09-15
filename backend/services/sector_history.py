import pandas as pd
from datetime import date
from sqlalchemy import text
from db import engine

def save_sector_snapshot():

    query = """
    SELECT sector, strength
    FROM sector_strength
    """

    df = pd.read_sql(query, engine)

    df["snapshot_date"] = date.today()

    df.to_sql(
        "sector_strength_history",
        engine,
        if_exists="append",
        index=False
    )

    print(f"Saved {len(df)} sectors")