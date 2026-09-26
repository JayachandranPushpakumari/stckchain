import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
from sqlalchemy import text

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from db import engine
from services.chart_patterns import detect_bullish_patterns
from services.market_regime import classify_market_regime
from services.technicals import calculate_indicators

MIN_HISTORY_ROWS = 250
MIN_MEDIAN_TURNOVER = 10_000_000
MIN_MEDIAN_VOLUME = 50_000
MIN_FUNDAMENTAL_SCORE = 60
MIN_RISK_REWARD = 2.0
MIN_STOCKCHAIN_SCORE = 85
MAX_PATTERN_BREAKOUT_AGE_SESSIONS = 1


def _eligible_universe():
    return pd.read_sql(
        text("""
        WITH market_date AS (
            SELECT MAX(date) AS latest_date FROM price_data WHERE symbol <> '^NSEI'
        ), recent AS (
            SELECT p.symbol, p.date, p.open, p.high, p.low, p.close, p.volume,
                   ROW_NUMBER() OVER (PARTITION BY p.symbol ORDER BY p.date DESC) AS rn
            FROM price_data p, market_date m
            WHERE p.symbol <> '^NSEI' AND p.date >= m.latest_date - INTERVAL '400 days'
        ), quality AS (
            SELECT symbol,
                   COUNT(*) FILTER (WHERE rn <= 300) AS history_rows,
                   COUNT(*) FILTER (WHERE rn <= 250 AND open > 0 AND high > 0 AND low > 0 AND close > 0 AND volume > 0) AS valid_rows,
                   MAX(date) AS latest_date
            FROM recent
            WHERE rn <= 300
            GROUP BY symbol
        ), liquidity AS (
            SELECT symbol,
                   PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY close * volume) FILTER (WHERE rn <= 20) AS median_turnover,
                   PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY volume) FILTER (WHERE rn <= 20) AS median_volume
            FROM recent
            WHERE rn <= 20 AND close > 0 AND volume > 0
            GROUP BY symbol
        ), latest_scores AS (
            SELECT DISTINCT ON (symbol) symbol, total_score
            FROM fundamental_scores
            ORDER BY symbol, screened_at DESC
        ), market_date_value AS (
            SELECT latest_date FROM market_date
        )
        SELECT q.symbol, q.history_rows, q.valid_rows, q.latest_date,
               l.median_turnover, l.median_volume, s.total_score,
               (q.history_rows >= :min_history AND q.valid_rows >= :min_valid
                AND q.latest_date >= m.latest_date - INTERVAL '7 days') AS data_quality_pass,
               (l.median_turnover >= :min_turnover AND l.median_volume >= :min_volume) AS liquidity_pass,
               (s.total_score > :min_fundamental) AS fundamental_pass
        FROM quality q
        JOIN liquidity l ON l.symbol = q.symbol
        LEFT JOIN latest_scores s ON s.symbol = q.symbol
        CROSS JOIN market_date_value m
        """),
        engine,
        params={
            "min_history": MIN_HISTORY_ROWS,
            "min_valid": int(MIN_HISTORY_ROWS * 0.95),
            "min_turnover": MIN_MEDIAN_TURNOVER,
            "min_volume": MIN_MEDIAN_VOLUME,
            "min_fundamental": MIN_FUNDAMENTAL_SCORE,
        },
    )


def _momentum_percentiles():
    rows = pd.read_sql(
        text("""
        SELECT symbol, 100 * PERCENT_RANK() OVER (ORDER BY rs_score) AS percentile
        FROM relative_strength
        WHERE rs_score IS NOT NULL
        """),
        engine,
    )
    return dict(zip(rows["symbol"], rows["percentile"]))


def _price_history(symbol):
    return pd.read_sql(
        text("""
        SELECT date, open, high, low, close, volume
        FROM price_data
        WHERE symbol = :symbol
        ORDER BY date DESC
        LIMIT 300
        """),
        engine,
        params={"symbol": symbol},
    ).sort_values("date").reset_index(drop=True)


def _technical_score(latest, previous):
    trend = 5 if latest["ma20"] > latest["ma50"] > 0 else 0
    rsi = max(0.0, min(5.0, (float(latest["rsi"]) - 55) / 4))
    volume = max(0.0, min(5.0, (float(latest["volume_ratio"]) - 1) * 2.5))
    adx = max(0.0, min(5.0, (float(latest["adx"]) - 15) / 5))
    breakout_pct = (float(latest["close"]) / float(previous["high_20"]) - 1) * 100
    structure = max(0.0, 5.0 - max(0.0, breakout_pct - 2.5)) if breakout_pct >= 0 else 0
    return round(trend + rsi + volume + adx + structure, 2), breakout_pct


def _build_opportunity(symbol, fundamental_score, momentum_percentile, median_turnover, regime):
    prices = _price_history(symbol)
    prices = prices.dropna(subset=["open", "high", "low", "close", "volume"])
    if len(prices) < MIN_HISTORY_ROWS:
        return None
    patterns = detect_bullish_patterns(prices, max_breakout_age_sessions=MAX_PATTERN_BREAKOUT_AGE_SESSIONS)
    if not patterns:
        return None
    indicators = calculate_indicators(prices.copy())
    latest = indicators.iloc[-1]
    previous = indicators.iloc[-2]
    required = ("atr", "ma20", "ma50", "rsi", "volume_ratio", "adx", "high_20")
    if any(pd.isna(latest[name]) for name in required) or pd.isna(previous["high_20"]):
        return None

    close = float(latest["close"])
    atr = float(latest["atr"])
    breakout_level = float(previous["high_20"])
    entry_low = close
    entry_high = close + 0.5 * atr
    entry_reference = (entry_low + entry_high) / 2
    stop_loss = max(breakout_level - 0.5 * atr, entry_reference - 2 * atr)
    risk = entry_reference - stop_loss
    if atr <= 0 or risk <= 0:
        return None
    target_1 = entry_reference + 2 * risk
    target_2 = entry_reference + 3 * risk
    risk_reward = (target_1 - entry_reference) / risk
    if risk_reward < MIN_RISK_REWARD:
        return None

    technical_score, breakout_pct = _technical_score(latest, previous)
    fundamental_component = 35 * float(fundamental_score) / 100
    momentum_component = 10 * max(0.0, min(100.0, float(momentum_percentile))) / 100
    liquidity_component = min(10.0, 5 + 5 * float(median_turnover) / (10 * MIN_MEDIAN_TURNOVER))
    risk_component = min(10.0, 5 * risk_reward)
    score = round(min(100.0, fundamental_component + technical_score + momentum_component + liquidity_component + regime["score"] + risk_component), 2)
    reasons = [
        *[pattern["reason"] for pattern in patterns],
        f"Fundamental quality score is {float(fundamental_score):.0f}/100",
        f"Price closed {breakout_pct:.1f}% above the prior 20-day high",
        f"Volume expanded to {float(latest['volume_ratio']):.1f}x its 20-day average",
        f"ADX {float(latest['adx']):.1f} confirms trend strength",
        f"Relative-strength percentile is {float(momentum_percentile):.0f}",
        regime["reason"],
        f"Target 1 offers {risk_reward:.1f}:1 reward to risk",
    ]
    return {
        "symbol": symbol,
        "setup_type": "BREAKOUT",
        "status": "READY_FOR_REVIEW",
        "score": score,
        "current_price": round(close, 2),
        "entry_low": round(entry_low, 2),
        "entry_high": round(entry_high, 2),
        "target_1": round(target_1, 2),
        "target_2": round(target_2, 2),
        "stop_loss": round(stop_loss, 2),
        "risk_reward": round(risk_reward, 2),
        "fundamental_score": round(float(fundamental_score), 2),
        "technical_score": technical_score,
        "momentum_score": round(momentum_component, 2),
        "liquidity_score": round(liquidity_component, 2),
        "regime_score": regime["score"],
        "risk_reward_score": round(risk_component, 2),
        "market_regime": regime["regime"],
        "patterns": [pattern["label"] for pattern in patterns],
        "reasons": reasons,
    }


def _breakout_candidates():
    universe = _eligible_universe()
    quality = universe[universe["data_quality_pass"].eq(True)]
    liquid = quality[quality["liquidity_pass"].eq(True)]
    fundamental = liquid[liquid["fundamental_pass"].eq(True)]
    breakouts = pd.read_sql(text("SELECT symbol FROM breakout_results"), engine)
    return fundamental[fundamental["symbol"].isin(set(breakouts["symbol"]))].copy()


def diagnose_breakout_opportunities():
    candidates = _breakout_candidates()
    momentum = _momentum_percentiles()
    regime = classify_market_regime()
    diagnostics = []
    for row in candidates.to_dict(orient="records"):
        symbol = row["symbol"]
        fundamental_score = row["total_score"]
        prices = _price_history(symbol)
        prices = prices.dropna(subset=["open", "high", "low", "close", "volume"])
        pattern_result = "insufficient_price_history" if len(prices) < MIN_HISTORY_ROWS else None
        patterns = []
        if pattern_result is None:
            patterns = detect_bullish_patterns(prices, max_breakout_age_sessions=MAX_PATTERN_BREAKOUT_AGE_SESSIONS)
            if not patterns:
                pattern_result = "no_bullish_chart_pattern"
        opportunity = None
        risk_reward_result = None
        if patterns:
            opportunity = _build_opportunity(
                symbol, fundamental_score, momentum.get(symbol, 0),
                row["median_turnover"], regime,
            )
            if opportunity:
                risk_reward_result = "passed"
            else:
                risk_reward_result = "risk_reward_or_indicator_rejection"
        diagnostics.append({
            "symbol": symbol,
            "fundamental_score": float(fundamental_score) if fundamental_score is not None else None,
            "data_quality_pass": bool(row["data_quality_pass"]),
            "liquidity_pass": bool(row["liquidity_pass"]),
            "fundamental_pass": bool(row["fundamental_pass"]),
            "patterns": [pattern["label"] for pattern in patterns],
            "pattern_reasons": [pattern["reason"] for pattern in patterns],
            "pattern_result": pattern_result or ("matched" if patterns else "no_bullish_chart_pattern"),
            "risk_reward_result": risk_reward_result,
            "opportunity": opportunity,
            "rejection_reason": (
                None if opportunity else
                (pattern_result or "no_bullish_chart_pattern" if not patterns else risk_reward_result)
            ),
        })
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "market_regime": regime,
        "candidate_count": len(diagnostics),
        "published_count": sum(1 for d in diagnostics if d["opportunity"] is not None),
        "diagnostics": sorted(diagnostics, key=lambda d: d["symbol"]),
    }


def generate_breakout_opportunities(save_to_db=True):
    universe = _eligible_universe()
    stage_counts = {"all_stocks": int(len(universe))}
    quality = universe[universe["data_quality_pass"].eq(True)]
    stage_counts["data_quality"] = int(len(quality))
    liquid = quality[quality["liquidity_pass"].eq(True)]
    stage_counts["liquidity"] = int(len(liquid))
    fundamental = liquid[liquid["fundamental_pass"].eq(True)]
    stage_counts["fundamentals"] = int(len(fundamental))

    breakouts = pd.read_sql(text("SELECT symbol FROM breakout_results"), engine)
    candidates = fundamental[fundamental["symbol"].isin(set(breakouts["symbol"]))]
    stage_counts["breakout"] = int(len(candidates))
    regime = classify_market_regime()
    stage_counts["market_regime"] = int(len(candidates))

    momentum = _momentum_percentiles()
    opportunities = []
    for row in candidates.to_dict(orient="records"):
        opportunity = _build_opportunity(
            row["symbol"], row["total_score"], momentum.get(row["symbol"], 0),
            row["median_turnover"], regime,
        )
        if opportunity:
            opportunities.append(opportunity)
    stage_counts["chart_pattern"] = len(opportunities)
    stage_counts["risk_reward"] = len(opportunities)
    opportunities = sorted(opportunities, key=lambda item: item["score"], reverse=True)
    stage_counts["high_confidence"] = len(opportunities)
    for rank, opportunity in enumerate(opportunities, start=1):
        opportunity["rank"] = rank

    result = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "setup_type": "BREAKOUT",
        "market_regime": regime,
        "stage_counts": stage_counts,
        "minimum_score": 0,
        "message": None if opportunities else "No breakout stocks with a qualifying bullish chart pattern today.",
        "opportunities": opportunities,
    }
    if save_to_db:
        _save_run(result)
    return result


def _save_run(result):
    with engine.begin() as connection:
        run_id = connection.execute(
            text("""
            INSERT INTO opportunity_runs (setup_type, market_regime, stage_counts, minimum_score, generated_at)
            VALUES (:setup_type, :market_regime, CAST(:stage_counts AS jsonb), :minimum_score, :generated_at)
            RETURNING id
            """),
            {
                "setup_type": result["setup_type"],
                "market_regime": result["market_regime"]["regime"],
                "stage_counts": json.dumps(result["stage_counts"]),
                "minimum_score": result["minimum_score"],
                "generated_at": result["generated_at"],
            },
        ).scalar_one()
        for opportunity in result["opportunities"]:
            connection.execute(
                text("""
                INSERT INTO opportunities (
                    run_id, symbol, setup_type, status, rank, score, current_price, entry_low, entry_high,
                    target_1, target_2, stop_loss, risk_reward, fundamental_score, technical_score,
                    momentum_score, liquidity_score, regime_score, risk_reward_score, market_regime, reasons
                ) VALUES (
                    :run_id, :symbol, :setup_type, :status, :rank, :score, :current_price, :entry_low, :entry_high,
                    :target_1, :target_2, :stop_loss, :risk_reward, :fundamental_score, :technical_score,
                    :momentum_score, :liquidity_score, :regime_score, :risk_reward_score, :market_regime, CAST(:reasons AS jsonb)
                )
                """),
                {**opportunity, "run_id": run_id, "reasons": json.dumps(opportunity["reasons"])},
            )
    result["run_id"] = run_id


if __name__ == "__main__":
    output = generate_breakout_opportunities(save_to_db=True)
    print(f"Saved {len(output['opportunities'])} high-confidence breakout opportunities")
