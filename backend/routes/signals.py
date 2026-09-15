from fastapi import APIRouter
import pandas as pd
from sqlalchemy import text
from db import engine

router = APIRouter()

@router.get("/signals/{symbol}")
def get_signal(symbol: str):

    query = text("""
    SELECT date, close
    FROM (
        SELECT date, close
        FROM price_data
        WHERE symbol = :symbol
        ORDER BY date DESC
        LIMIT 60
    ) AS recent_prices
    ORDER BY date
    """)

    normalized_symbol = symbol.upper()
    df = pd.read_sql(query, engine, params={"symbol": normalized_symbol})

    if len(df) < 50:
        return {
            "symbol": normalized_symbol,
            "signal": "INSUFFICIENT_DATA",
            "price": None
        }

    df["ma20"] = df["close"].rolling(20).mean()
    df["ma50"] = df["close"].rolling(50).mean()

    latest = df.iloc[-1]

    signal = "HOLD"

    if latest["ma20"] > latest["ma50"]:
        signal = "BUY"
    elif latest["ma20"] < latest["ma50"]:
        signal = "SELL"

    return {
        "symbol": normalized_symbol,
        "signal": signal,
        "price": latest["close"]
    }
