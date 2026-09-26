import pandas as pd
from pathlib import Path
import sys
from sqlalchemy import text

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from db import engine


def calculate_rs():
    query = text("""
    WITH ranked AS (
        SELECT symbol, close,
               ROW_NUMBER() OVER (PARTITION BY symbol ORDER BY date DESC) AS rn
        FROM price_data
        WHERE symbol <> '^NSEI' AND close IS NOT NULL AND close > 0
    )
    SELECT symbol,
           MAX(close) FILTER (WHERE rn = 1) AS latest,
           MAX(close) FILTER (WHERE rn = 21) AS one_month,
           MAX(close) FILTER (WHERE rn = 63) AS three_month,
           MAX(close) FILTER (WHERE rn = 126) AS six_month,
           COUNT(*) AS rows
    FROM ranked
    GROUP BY symbol
    HAVING COUNT(*) >= 150
    """)

    df = pd.read_sql(query, engine)

    df = df[(df["one_month"] > 0) & (df["three_month"] > 0) & (df["six_month"] > 0)]

    df["r1"] = ((df["latest"] - df["one_month"]) / df["one_month"]) * 100
    df["r3"] = ((df["latest"] - df["three_month"]) / df["three_month"]) * 100
    df["r6"] = ((df["latest"] - df["six_month"]) / df["six_month"]) * 100

    df["rs_score"] = 0.3 * df["r1"] + 0.3 * df["r3"] + 0.4 * df["r6"]
    df = df.dropna(subset=["rs_score"])

    return pd.DataFrame({
        "symbol": df["symbol"],
        "rs_score": df["rs_score"].round(2),
    })


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