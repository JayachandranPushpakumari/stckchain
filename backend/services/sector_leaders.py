import pandas as pd
from pathlib import Path
import sys

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from db import engine

def calculate_sector_leaders():

    rs_df = pd.read_sql(
        "SELECT symbol, rs_score FROM relative_strength",
        engine
    )

    sector_df = pd.read_sql(
        "SELECT symbol, sector FROM sectors",
        engine
    )

    merged = rs_df.merge(
        sector_df,
        on="symbol",
        how="inner"
    )

    merged["rank"] = (
        merged.groupby("sector")["rs_score"]
        .rank(
            ascending=False,
            method="dense"
        )
    )

    leaders = merged[
        merged["rank"] <= 10
    ]

    leaders.to_sql(
        "sector_leaders",
        engine,
        if_exists="replace",
        index=False
    )

if __name__ == "__main__":
    calculate_sector_leaders()