import pandas as pd
from pathlib import Path
import sys

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from db import engine


def calculate_sector_strength():

    sectors = pd.read_excel(
        BACKEND_DIR / "data" / "sectors.csv.xlsx"
    )
    sectors = sectors.rename(columns={
        "Name": "symbol",
        "Sector": "sector"
    })

    results = []

    for sector in sectors["sector"].unique():

        stocks = sectors[
            sectors["sector"] == sector
        ]["symbol"].tolist()

        returns = []

        for symbol in stocks:

            query = f"""
            SELECT date, close
            FROM price_data
            WHERE symbol='{symbol}'
            ORDER BY date
            """

            df = pd.read_sql(query, engine)

            if len(df) < 60:
                continue

            recent = df["close"].iloc[-1]
            old = df["close"].iloc[-60]

            pct_return = (
                recent - old
            ) / old * 100

            returns.append(pct_return)

        if returns:

            results.append({
                "sector": sector,
                "strength": round(
                    float(pd.Series(returns).median()), 2
                ),
                "pct_positive": round(
                    sum(1 for r in returns if r > 0) / len(returns) * 100, 1
                ),
                "stock_count": len(returns)
            })

    return pd.DataFrame(results)

if __name__ == "__main__":

    df = calculate_sector_strength()

    print(
        df.sort_values(
            "strength",
            ascending=False
        )
    )

df.to_sql(
    "sector_strength",
    engine,
    if_exists="replace",
    index=False
)