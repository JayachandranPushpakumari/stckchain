import pandas as pd
from pathlib import Path
import sys
from sqlalchemy import text

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from db import engine


def calculate_rs():

    symbols = pd.read_sql(
        "SELECT DISTINCT symbol FROM price_data",
        engine
    )

    results = []

    for symbol in symbols["symbol"]:

        query = text("""
        SELECT date, close
        FROM price_data
        WHERE symbol = :symbol
        ORDER BY date
        """)

        df = pd.read_sql(query, engine, params={"symbol": symbol})

        if len(df) < 150:
            continue

        latest = df["close"].iloc[-1]

        one_month = df["close"].iloc[-21]
        three_month = df["close"].iloc[-63]
        six_month = df["close"].iloc[-126]

        if one_month == 0 or three_month == 0 or six_month == 0:
            continue

        r1 = ((latest - one_month) / one_month) * 100
        r3 = ((latest - three_month) / three_month) * 100
        r6 = ((latest - six_month) / six_month) * 100

        rs_score = (
            0.3 * r1 +
            0.3 * r3 +
            0.4 * r6
        )

        if pd.isna(rs_score):
            continue

        results.append({
            "symbol": symbol,
            "rs_score": round(rs_score, 2)
        })

    return pd.DataFrame(results)


def save_rs_rankings():

    rs_df = calculate_rs()

    rs_df.to_sql(
        "relative_strength",
        engine,
        if_exists="replace",
        index=False
    )

    return len(rs_df)


if __name__ == "__main__":
    count = save_rs_rankings()
    print(f"Saved {count} stocks")