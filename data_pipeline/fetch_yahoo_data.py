import yfinance as yf
import pandas as pd
from datetime import date, timedelta
from sqlalchemy import text
from db import engine

# symbols = pd.read_sql("SELECT stock_name FROM stocks2", engine)["stock_name"].tolist() # --backup
# stock_symbol = "GANESHHOU.BO"  # Replace with desired stock symbol
# symbols = pd.read_sql(f"SELECT symbol FROM stocks WHERE symbol = '{stock_symbol}'", engine)["symbol"].tolist()
symbols = pd.read_sql("SELECT distinct symbol FROM stocks", engine)["symbol"].tolist()

# Determine fetch window.
# If price_data has less than 180 calendar days of history, do a one-time
# historical backfill (400 days) so indicators like relative strength and
# MA200 have enough data. On subsequent daily runs use a 30-day rolling window.
end_date = date.today() + timedelta(days=1)

with engine.connect() as _conn:
    oldest_date = _conn.execute(
        text("SELECT MIN(date) FROM price_data WHERE symbol <> '^NSEI'")
    ).scalar()

if oldest_date is None or (date.today() - oldest_date).days < 180:
    start_date = end_date - timedelta(days=1826)  # ~5 years
    print("Historical backfill mode: fetching up to 5 years of price data.")
else:
    start_date = end_date - timedelta(days=30)

for sym in symbols:
    print(f"Fetching {sym}...")

    try:
        data = yf.download(sym, start=start_date, end=end_date, progress=False)

        if data.empty:
            print(f"No data for {sym}")
            continue

        data.reset_index(inplace=True)
        
        data.columns = data.columns.get_level_values(0)

        data.rename(columns={
            "Date": "date",
            "Open": "open",
            "High": "high",
            "Low": "low",
            "Close": "close",
            "Volume": "volume",
            "Adj Close": "adj_close"
        }, inplace=True)

        clean_symbol = sym.replace(".NS", "").replace(".BO", "")
        data["symbol"] = clean_symbol

        data = data[["date", "symbol", "open", "high", "low", "close", "volume"]]

        # Drop incomplete bars: close must be a positive number
        data = data[data["close"].notna() & (data["close"] > 0)]

        if data.empty:
            print(f"No valid bars for {clean_symbol} after filtering")
            continue

        # Remove existing rows in the fetched range so re-runs don't duplicate
        with engine.begin() as conn:
            conn.execute(
                text("DELETE FROM price_data WHERE symbol = :sym AND date BETWEEN :d1 AND :d2"),
                {"sym": clean_symbol, "d1": data["date"].min(), "d2": data["date"].max()}
            )

        data.to_sql(
            "price_data",
            engine,
            if_exists="append",
            index=False,
            method="multi"
        )

        print(f"Inserted {clean_symbol}")
    except Exception as e:
        print(f"Error processing {sym}: {str(e)}")
        continue

print("All data inserted successfully")