import pandas as pd

from db import engine
from services.technicals import calculate_indicators
from services.price_action import is_breakout

def find_breakouts():

    symbols_query = """
    SELECT DISTINCT symbol
    FROM price_data
    """

    symbols_df = pd.read_sql(symbols_query, engine)

    results = []

    for symbol in symbols_df["symbol"]:

        query = f"""
        SELECT *
        FROM price_data
        WHERE symbol = '{symbol}'
        ORDER BY date
        """

        df = pd.read_sql(query, engine)

        if len(df) < 250:
            continue

        df = calculate_indicators(df)

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