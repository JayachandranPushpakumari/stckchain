from datetime import datetime, timezone

import pandas as pd
from sqlalchemy import text

from db import engine
from services.chart_patterns import detect_bullish_patterns


MAX_PATTERN_BREAKOUT_AGE_SESSIONS = 10


def scan_bullish_patterns():
    candidates = pd.read_sql(
        text("""
        WITH latest_scores AS (
            SELECT DISTINCT ON (symbol) symbol, total_score
            FROM fundamental_scores
            ORDER BY symbol, screened_at DESC
        )
        SELECT symbol, total_score
        FROM latest_scores
        WHERE total_score > 60
        ORDER BY total_score DESC, symbol
        """),
        engine,
    )
    results = []
    for row in candidates.to_dict(orient="records"):
        prices = pd.read_sql(
            text("""
            SELECT date, open, high, low, close, volume
            FROM price_data
            WHERE symbol = :symbol
            ORDER BY date DESC
            LIMIT 300
            """),
            engine,
            params={"symbol": row["symbol"]},
        ).sort_values("date").reset_index(drop=True)
        patterns = detect_bullish_patterns(prices, max_breakout_age_sessions=MAX_PATTERN_BREAKOUT_AGE_SESSIONS)
        if not patterns:
            continue
        latest = prices.dropna(subset=["close"]).iloc[-1]
        results.append({
            "symbol": row["symbol"],
            "fundamental_score": int(row["total_score"]),
            "current_price": round(float(latest["close"]), 2),
            "as_of_date": str(latest["date"]),
            "patterns": [pattern["label"] for pattern in patterns],
            "reasons": [pattern["reason"] for pattern in patterns],
        })
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "fundamental_candidates": int(len(candidates)),
        "matched_stocks": len(results),
        "stocks": results,
    }
