import yfinance as yf
import pandas as pd
from sqlalchemy import create_engine

engine = create_engine("postgresql://postgres:Jayan%40123@localhost:5432/stockDB")

# symbols = pd.read_sql("SELECT stock_name FROM stocks2", engine)["stock_name"].tolist() # --backup
# stock_symbol = "GANESHHOU.BO"  # Replace with desired stock symbol
# symbols = pd.read_sql(f"SELECT symbol FROM stocks WHERE symbol = '{stock_symbol}'", engine)["symbol"].tolist()
symbols = pd.read_sql("SELECT distinct symbol FROM stocks", engine)["symbol"].tolist()

for sym in symbols:
    print(f"Fetching {sym}...")
    
    try:
        data = yf.download(sym, start="2026-08-19", end="2026-09-15", progress=False)

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