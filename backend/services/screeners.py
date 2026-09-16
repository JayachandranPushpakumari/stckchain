import pandas as pd
from pathlib import Path
import sys
from sqlalchemy import text

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from db import engine
from services.technicals import calculate_indicators
from services.price_action import is_breakout

LOOKBACK_ROWS = 300
MIN_HISTORY_ROWS = 250


def _recent_prices():
    query = text("""
    SELECT date, symbol, open, high, low, close, volume
    FROM (
        SELECT date, symbol, open, high, low, close, volume,
               ROW_NUMBER() OVER (PARTITION BY symbol ORDER BY date DESC) AS rn
        FROM price_data
    ) recent
    WHERE rn <= :lookback
    """)
    df = pd.read_sql(query, engine, params={"lookback": LOOKBACK_ROWS})
    return df.sort_values(["symbol", "date"]).reset_index(drop=True)


def find_breakouts():

    prices = _recent_prices()
    results = []

    for symbol, df in prices.groupby("symbol"):

        df = calculate_indicators(df.copy())

        if len(df) < MIN_HISTORY_ROWS:
            continue

        latest = df.iloc[-1]
        previous = df.iloc[-2]

        bullish = (
            # Trend
            latest["ma20"] > latest["ma50"]
            # Momentum
            and latest["rsi"] > 60
            # Breakout
            and latest["close"] > previous["high_20"]
            # Volume confirmation
            and latest["volume_ratio"] > 2
            # Strong trend only
            and latest["adx"] > 20
        )

        if bullish:

            results.append({
                "symbol": symbol,
                "close": round(latest["close"], 2),
                "rsi": round(latest["rsi"], 2),
                "volume_ratio": round(latest["volume_ratio"], 2),
                "ma20": round(latest["ma20"], 2),
                "ma50": round(latest["ma50"], 2),
                "high_20": round(previous["high_20"], 2),
                "adx": round(latest["adx"], 2),
                "signal": "BREAKOUT"
            })

    return results


def save_breakouts():

    results = find_breakouts()
    df = pd.DataFrame(results)

    df.to_sql(
        "breakout_results",
        engine,
        if_exists="replace",
        index=False
    )

    return len(df)


if __name__ == "__main__":
    count = save_breakouts()
    print(f"Saved {count} breakouts")
