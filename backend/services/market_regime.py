import pandas as pd
from sqlalchemy import text

from db import engine

NIFTY_SYMBOL = "^NSEI"


def classify_market_regime():
    nifty = pd.read_sql(
        text("""
        SELECT date, close
        FROM price_data
        WHERE symbol = :symbol AND close IS NOT NULL
        ORDER BY date DESC
        LIMIT 250
        """),
        engine,
        params={"symbol": NIFTY_SYMBOL},
    ).sort_values("date")
    if len(nifty) < 200:
        return {"regime": "UNKNOWN", "score": 0, "reason": "NIFTY history is not yet sufficient", "breadth": None}

    nifty["ma50"] = nifty["close"].rolling(50).mean()
    nifty["ma200"] = nifty["close"].rolling(200).mean()
    latest = nifty.iloc[-1]
    breadth = pd.read_sql(
        text("""
        WITH recent AS (
            SELECT symbol, date, close,
                   ROW_NUMBER() OVER (PARTITION BY symbol ORDER BY date DESC) AS rn
            FROM price_data
            WHERE symbol <> :nifty_symbol AND close IS NOT NULL
        ), averages AS (
            SELECT symbol,
                   MAX(close) FILTER (WHERE rn = 1) AS latest_close,
                   AVG(close) FILTER (WHERE rn <= 50) AS ma50,
                   COUNT(*) FILTER (WHERE rn <= 50) AS observations
            FROM recent
            WHERE rn <= 50
            GROUP BY symbol
        )
        SELECT 100.0 * AVG(CASE WHEN latest_close > ma50 THEN 1.0 ELSE 0.0 END) AS breadth
        FROM averages
        WHERE observations = 50
        """),
        engine,
        params={"nifty_symbol": NIFTY_SYMBOL},
    ).iloc[0]["breadth"]
    breadth = float(breadth) if pd.notna(breadth) else 0.0
    close = float(latest["close"])
    ma50 = float(latest["ma50"])
    ma200 = float(latest["ma200"])

    if close > ma50 > ma200 and breadth >= 55:
        regime, score = "BULL", 10
    elif close > ma200 and breadth >= 45:
        regime, score = "NEUTRAL", 6
    elif close > ma200 or breadth >= 35:
        regime, score = "WEAK", 3
    else:
        regime, score = "BEAR", 0

    return {
        "regime": regime,
        "score": score,
        "reason": f"NIFTY {close:.2f}, MA50 {ma50:.2f}, MA200 {ma200:.2f}, breadth {breadth:.1f}%",
        "breadth": round(breadth, 2),
        "nifty_close": round(close, 2),
        "nifty_ma50": round(ma50, 2),
        "nifty_ma200": round(ma200, 2),
    }
