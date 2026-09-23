from datetime import date, timedelta

import pandas as pd
import yfinance as yf
from sqlalchemy import text

from db import engine

SYMBOL = "^NSEI"

with engine.connect() as connection:
    first_date = connection.execute(
        text("SELECT MIN(date) FROM price_data WHERE symbol = :symbol"),
        {"symbol": SYMBOL},
    ).scalar()

end_date = date.today() + timedelta(days=1)
start_date = end_date - timedelta(days=30) if first_date else date(2020, 1, 1)
data = yf.download(SYMBOL, start=start_date, end=end_date, progress=False)
if data.empty:
    raise RuntimeError("Yahoo Finance returned no NIFTY 50 index data")

data.reset_index(inplace=True)
data.columns = data.columns.get_level_values(0)
data.rename(columns={
    "Date": "date", "Open": "open", "High": "high", "Low": "low",
    "Close": "close", "Volume": "volume",
}, inplace=True)
data["symbol"] = SYMBOL
data = data[["date", "symbol", "open", "high", "low", "close", "volume"]]
with engine.begin() as connection:
    connection.execute(
        text("DELETE FROM price_data WHERE symbol = :symbol AND date BETWEEN :start AND :end"),
        {"symbol": SYMBOL, "start": data["date"].min(), "end": data["date"].max()},
    )
    data.to_sql("price_data", connection, if_exists="append", index=False, method="multi")
print(f"Inserted {len(data)} NIFTY 50 index rows")
