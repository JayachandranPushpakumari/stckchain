from datetime import datetime, timezone

import numpy as np
import pandas as pd
from sqlalchemy import text

from db import engine
from services.technicals import calculate_indicators

MIN_FUNDAMENTAL_SCORE = 60
MIN_HISTORY_ROWS = 200
STRUCTURE_WINDOW = 60
MAX_BAND_POSITION = 0.45
MIN_RISK_REWARD = 2.0

_bullish_structures_cache: dict | None = None
_bullish_structures_cached_at: datetime | None = None


def _cache_is_fresh():
    return (
        _bullish_structures_cache is not None
        and _bullish_structures_cached_at is not None
        and _bullish_structures_cached_at.date() == datetime.now(timezone.utc).date()
    )


def _band_line(frame, column, quantile):
    frame = frame.reset_index(drop=True)
    boundaries = np.linspace(0, len(frame), 7, dtype=int)
    bins = [frame.iloc[boundaries[i]:boundaries[i + 1]] for i in range(6)]
    x = np.array([(i + 0.5) * len(frame) / 6 for i in range(6)], dtype=float)
    values = np.array([part[column].quantile(quantile) for part in bins], dtype=float)
    slope, intercept = np.polyfit(x, values, 1)
    return float(slope), float(intercept)


def detect_bullish_structure(prices):
    clean = prices.dropna(subset=["open", "high", "low", "close", "volume"]).reset_index(drop=True)
    if len(clean) < MIN_HISTORY_ROWS:
        return None

    indicators = calculate_indicators(clean.copy())
    frame = indicators.tail(STRUCTURE_WINDOW).reset_index(drop=True)
    latest = frame.iloc[-1]
    previous = frame.iloc[-2]
    lower_slope, lower_intercept = _band_line(frame, "low", 0.20)
    upper_slope, upper_intercept = _band_line(frame, "high", 0.80)
    x = STRUCTURE_WINDOW - 1
    lower_band = lower_intercept + lower_slope * x
    upper_band = upper_intercept + upper_slope * x
    width = upper_band - lower_band
    close = float(latest["close"])
    atr = float(latest["atr"])
    if width <= 0 or atr <= 0 or width < 2.5 * atr:
        return None

    mean_price = float(frame["close"].mean())
    normalized_lower_slope = lower_slope * STRUCTURE_WINDOW / mean_price
    normalized_upper_slope = upper_slope * STRUCTURE_WINDOW / mean_price
    if normalized_lower_slope < -0.03 or normalized_upper_slope < -0.03:
        return None

    slope_gap = abs(normalized_lower_slope - normalized_upper_slope)
    if abs(normalized_lower_slope) <= 0.03 and abs(normalized_upper_slope) <= 0.03:
        structure_type = "HORIZONTAL_RANGE"
        label = "Horizontal Range Support"
    elif normalized_lower_slope >= 0.04 and abs(normalized_upper_slope) <= 0.04:
        structure_type = "ASCENDING_TRIANGLE_SUPPORT"
        label = "Ascending Triangle Support"
    elif normalized_lower_slope >= 0.04 and normalized_upper_slope >= 0.04 and slope_gap <= 0.08:
        structure_type = "RISING_CHANNEL_PULLBACK"
        label = "Rising Channel Pullback"
    elif normalized_lower_slope >= 0.04:
        structure_type = "ASCENDING_TRENDLINE_BOUNCE"
        label = "Ascending Trendline Bounce"
    else:
        return None

    tolerance = max(atr, width * 0.08)
    lower_line = lower_intercept + lower_slope * np.arange(STRUCTURE_WINDOW)
    upper_line = upper_intercept + upper_slope * np.arange(STRUCTURE_WINDOW)
    lower_touches = int((frame["low"] <= lower_line + tolerance).sum())
    upper_touches = int((frame["high"] >= upper_line - tolerance).sum())
    if lower_touches < 2 or upper_touches < 1:
        return None

    band_position = (close - lower_band) / width
    if band_position < -0.08 or band_position > MAX_BAND_POSITION:
        return None
    if close < lower_band - 0.5 * atr:
        return None

    rsi = float(latest["rsi"])
    previous_rsi = float(previous["rsi"])
    macd_histogram = float(latest["macd"] - latest["macd_signal"])
    previous_macd_histogram = float(previous["macd"] - previous["macd_signal"])
    bullish_candle = close > float(latest["open"]) or close > float(previous["close"])
    momentum_signals = sum((rsi > previous_rsi, macd_histogram > previous_macd_histogram, bullish_candle))
    if not 35 <= rsi <= 70 or momentum_signals < 2:
        return None

    entry_low = close
    entry_high = close + 0.25 * atr
    entry_reference = (entry_low + entry_high) / 2
    stop_loss = min(lower_band - 0.25 * atr, float(frame.tail(5)["low"].min()) - 0.10 * atr)
    target_1 = lower_band + width * 0.60
    target_2 = upper_band
    risk = entry_reference - stop_loss
    reward = target_2 - entry_reference
    if risk <= 0 or reward <= 0:
        return None
    risk_reward = reward / risk
    if risk_reward < MIN_RISK_REWARD:
        return None

    return {
        "structure_type": structure_type,
        "structure_label": label,
        "lower_band": round(lower_band, 2),
        "upper_band": round(upper_band, 2),
        "band_position": round(max(0.0, min(1.0, band_position)) * 100, 1),
        "lower_touches": lower_touches,
        "upper_touches": upper_touches,
        "rsi": round(rsi, 1),
        "macd_improving": True,
        "current_price": round(close, 2),
        "entry_low": round(entry_low, 2),
        "entry_high": round(entry_high, 2),
        "stop_loss": round(stop_loss, 2),
        "target_1": round(target_1, 2),
        "target_2": round(target_2, 2),
        "risk_reward": round(risk_reward, 2),
        "as_of_date": str(latest["date"]),
        "reasons": [
            f"Price is in the lower {max(0.0, min(1.0, band_position)) * 100:.0f}% of a valid bullish structure",
            f"Structure has {lower_touches} lower-band and {upper_touches} upper-band contacts",
            f"RSI improved from {previous_rsi:.1f} to {rsi:.1f} while MACD momentum strengthened",
            f"Upper-band target offers {risk_reward:.1f}:1 reward to structural risk",
        ],
    }


def scan_bullish_structures(force_refresh=False):
    global _bullish_structures_cache, _bullish_structures_cached_at
    if not force_refresh and _cache_is_fresh():
        return _bullish_structures_cache

    prices = pd.read_sql(
        text("""
        WITH latest_scores AS (
            SELECT DISTINCT ON (symbol) symbol, total_score
            FROM fundamental_scores
            ORDER BY symbol, screened_at DESC
        ), ranked_prices AS (
            SELECT p.symbol, p.date, p.open, p.high, p.low, p.close, p.volume,
                   s.total_score,
                   ROW_NUMBER() OVER (PARTITION BY p.symbol ORDER BY p.date DESC) AS rn
            FROM price_data p
            JOIN latest_scores s ON s.symbol = p.symbol
            WHERE s.total_score > :minimum_score
        )
        SELECT symbol, date, open, high, low, close, volume, total_score
        FROM ranked_prices
        WHERE rn <= 300
        ORDER BY symbol, date
        """),
        engine,
        params={"minimum_score": MIN_FUNDAMENTAL_SCORE},
    )
    results = []
    for symbol, history in prices.groupby("symbol", sort=False):
        structure = detect_bullish_structure(history.reset_index(drop=True))
        if structure:
            results.append({"symbol": symbol, "fundamental_score": int(history["total_score"].iloc[-1]), **structure})
    results.sort(key=lambda item: (-item["risk_reward"], item["band_position"], item["symbol"]))
    result = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "fundamental_candidates": int(prices["symbol"].nunique()),
        "matched_stocks": len(results),
        "stocks": results,
    }
    _bullish_structures_cache = result
    _bullish_structures_cached_at = datetime.now(timezone.utc)
    return result
