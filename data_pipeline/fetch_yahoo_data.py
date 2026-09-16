import yfinance as yf
import pandas as pd
from datetime import date, timedelta
from sqlalchemy import text
from db import engine

# symbols = pd.read_sql("SELECT stock_name FROM stocks2", engine)["stock_name"].tolist() # --backup
# stock_symbol = "GANESHHOU.BO"  # Replace with desired stock symbol
# symbols = pd.read_sql(f"SELECT symbol FROM stocks WHERE symbol = '{stock_symbol}'", engine)["symbol"].tolist()
symbols = pd.read_sql("SELECT distinct symbol FROM stocks", engine)["symbol"].tolist()

# Rolling window: fetch last ~30 days up to today so daily runs stay current.
# yfinance `end` is exclusive, so add one day to include today's bar.
end_date = date.today() + timedelta(days=1)
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

        clean_symbol = sym.replace(".NS", "")
        data["symbol"] = clean_symbol

        data = data[["date", "symbol", "open", "high", "low", "close", "volume"]]

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