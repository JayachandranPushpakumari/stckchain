import json
from datetime import date, datetime, timedelta, timezone

import numpy as np
import pandas as pd
from sqlalchemy import bindparam, text

from db import engine
from services.opportunities import (
    MIN_FUNDAMENTAL_SCORE,
    MIN_HISTORY_ROWS,
    MIN_MEDIAN_TURNOVER,
    MIN_MEDIAN_VOLUME,
    MIN_STOCKCHAIN_SCORE,
    _technical_score,
)
from services.technicals import calculate_indicators

MAX_HOLDING_DAYS = 90


def _regime_for_row(close, ma50, ma200, breadth):
    if close > ma50 > ma200 and breadth >= 55:
        return "BULL", 10
    if close > ma200 and breadth >= 45:
        return "NEUTRAL", 6
    if close > ma200 or breadth >= 35:
        return "WEAK", 3
    return "BEAR", 0


def _simulate_trade(prices, signal_index, entry_low, entry_high, stop_loss, target_1, target_2):
    if signal_index + 1 >= len(prices):
        return None
    entry_bar = prices.iloc[signal_index + 1]
    if entry_bar["open"] > entry_high or entry_bar["high"] < entry_low:
        return None
    entry_price = max(float(entry_bar["open"]), entry_low)
    entry_date = entry_bar["date"]
    stop_hit = False
    target_1_hit = False
    target_2_hit = False
    exit_price = None
    exit_date = None
    exit_reason = "TIMEOUT"
    mfe = 0.0
    mae = 0.0
    end_index = min(signal_index + MAX_HOLDING_DAYS, len(prices) - 1)
    for index in range(signal_index + 1, end_index + 1):
        bar = prices.iloc[index]
        mfe = max(mfe, (float(bar["high"]) - entry_price) / entry_price * 100)
        mae = min(mae, (float(bar["low"]) - entry_price) / entry_price * 100)
        if float(bar["low"]) <= stop_loss:
            stop_hit = True
            exit_price = stop_loss
            exit_date = bar["date"]
            exit_reason = "STOP_LOSS"
            break
        if float(bar["high"]) >= target_1:
            target_1_hit = True
        if float(bar["high"]) >= target_2:
            target_2_hit = True
            exit_price = target_2
            exit_date = bar["date"]
            exit_reason = "TARGET_2"
            break
    if exit_price is None:
        final_bar = prices.iloc[end_index]
        exit_price = float(final_bar["close"])
        exit_date = final_bar["date"]
    return {
        "entry_date": entry_date,
        "entry_price": round(entry_price, 2),
        "exit_date": exit_date,
        "exit_price": round(exit_price, 2),
        "exit_reason": exit_reason,
        "return_pct": round((exit_price - entry_price) / entry_price * 100, 2),
        "target_1_hit": target_1_hit,
        "target_2_hit": target_2_hit,
        "stop_hit": stop_hit,
        "mfe_pct": round(mfe, 2),
        "mae_pct": round(mae, 2),
    }


def _metrics(trades):
    if not trades:
        return {
            "total_trades": 0, "win_rate": 0.0, "avg_return": 0.0, "profit_factor": 0.0,
            "max_drawdown": 0.0, "target_1_rate": 0.0, "target_2_rate": 0.0,
            "stop_loss_rate": 0.0, "timeout_rate": 0.0, "avg_mfe": 0.0, "avg_mae": 0.0,
        }
    returns = pd.Series([trade["return_pct"] for trade in trades], dtype=float)
    equity = (1 + returns / 100).cumprod()
    drawdown = (equity / equity.cummax() - 1) * 100
    gains = returns[returns > 0].sum()
    losses = abs(returns[returns < 0].sum())
    count = len(trades)
    rate = lambda key: round(100 * sum(bool(trade[key]) for trade in trades) / count, 2)
    return {
        "total_trades": count,
        "win_rate": round(100 * (returns > 0).mean(), 2),
        "avg_return": round(float(returns.mean()), 2),
        "profit_factor": round(float(gains / losses), 2) if losses else None,
        "max_drawdown": round(float(drawdown.min()), 2),
        "target_1_rate": rate("target_1_hit"),
        "target_2_rate": rate("target_2_hit"),
        "stop_loss_rate": rate("stop_hit"),
        "timeout_rate": round(100 * sum(trade["exit_reason"] == "TIMEOUT" for trade in trades) / count, 2),
        "avg_mfe": round(float(np.mean([trade["mfe_pct"] for trade in trades])), 2),
        "avg_mae": round(float(np.mean([trade["mae_pct"] for trade in trades])), 2),
    }


def _load_symbols(start_date, end_date):
    rows = pd.read_sql(
        text("""
        SELECT DISTINCT symbol
        FROM price_data
        WHERE symbol <> '^NSEI' AND date BETWEEN :start_date AND :end_date
        ORDER BY symbol
        """),
        engine,
        params={"start_date": start_date, "end_date": end_date},
    )
    return rows["symbol"].tolist()


def _iter_symbol_data(symbols, start_date, end_date, chunk_size=100):
    price_query = text("""
        SELECT symbol, date, open, high, low, close, volume
        FROM price_data
        WHERE symbol IN :symbols AND date BETWEEN :history_start AND :end_date
        ORDER BY symbol, date
    """).bindparams(bindparam("symbols", expanding=True))
    score_query = text("""
        SELECT symbol, total_score, screened_at
        FROM fundamental_scores
        WHERE symbol IN :symbols AND screened_at <= :end_date
        ORDER BY symbol, screened_at
    """).bindparams(bindparam("symbols", expanding=True))
    for offset in range(0, len(symbols), chunk_size):
        chunk = symbols[offset:offset + chunk_size]
        prices = pd.read_sql(
            price_query,
            engine,
            params={"symbols": chunk, "history_start": start_date - timedelta(days=500), "end_date": end_date},
            parse_dates=["date"],
        )
        scores = pd.read_sql(
            score_query,
            engine,
            params={"symbols": chunk, "end_date": datetime.combine(end_date + timedelta(days=1), datetime.min.time())},
            parse_dates=["screened_at"],
        )
        price_groups = {symbol: rows.drop(columns="symbol").reset_index(drop=True) for symbol, rows in prices.groupby("symbol")}
        score_groups = {symbol: rows.drop(columns="symbol").reset_index(drop=True) for symbol, rows in scores.groupby("symbol")}
        for symbol in chunk:
            yield symbol, price_groups.get(symbol, pd.DataFrame()), score_groups.get(symbol, pd.DataFrame(columns=["total_score", "screened_at"]))


def _prepare_market(start_date, end_date):
    history_start = start_date - timedelta(days=500)
    nifty = pd.read_sql(
        text("""
        SELECT date, close
        FROM price_data
        WHERE symbol = '^NSEI' AND close > 0 AND date BETWEEN :history_start AND :end_date
        ORDER BY date
        """),
        engine,
        params={"history_start": history_start, "end_date": end_date},
        parse_dates=["date"],
    )
    nifty["ma50"] = nifty["close"].rolling(50).mean()
    nifty["ma200"] = nifty["close"].rolling(200).mean()
    breadth = pd.read_sql(
        text("""
        WITH moving_averages AS (
            SELECT symbol, date, close,
                   AVG(close) OVER (PARTITION BY symbol ORDER BY date ROWS BETWEEN 49 PRECEDING AND CURRENT ROW) AS ma50,
                   COUNT(*) OVER (PARTITION BY symbol ORDER BY date ROWS BETWEEN 49 PRECEDING AND CURRENT ROW) AS observations
            FROM price_data
            WHERE symbol <> '^NSEI' AND close > 0 AND date BETWEEN :history_start AND :end_date
        )
        SELECT date, 100.0 * AVG(CASE WHEN close > ma50 THEN 1.0 ELSE 0.0 END) AS breadth
        FROM moving_averages
        WHERE observations = 50
        GROUP BY date
        ORDER BY date
        """),
        engine,
        params={"history_start": history_start, "end_date": end_date},
        parse_dates=["date"],
    )
    market = nifty.merge(breadth, on="date", how="left")
    market[["regime", "regime_score"]] = market.apply(
        lambda row: pd.Series(_regime_for_row(row["close"], row["ma50"], row["ma200"], row["breadth"]))
        if pd.notna(row[["close", "ma50", "ma200", "breadth"]]).all() else pd.Series(["UNKNOWN", 0]),
        axis=1,
    )
    return market.set_index("date")[["breadth", "regime", "regime_score"]].to_dict("index")


def _momentum_percentile(symbol, signal_date):
    value = pd.read_sql(
        text("""
        WITH ranked_prices AS (
            SELECT symbol, close,
                   ROW_NUMBER() OVER (PARTITION BY symbol ORDER BY date DESC) AS rn
            FROM price_data
            WHERE close > 0 AND symbol <> '^NSEI'
              AND date BETWEEN :history_start AND :signal_date
        ), returns AS (
            SELECT symbol,
                   MAX(close) FILTER (WHERE rn = 1) / NULLIF(MAX(close) FILTER (WHERE rn = 64), 0) - 1 AS return_63
            FROM ranked_prices
            WHERE rn <= 64
            GROUP BY symbol
            HAVING COUNT(*) = 64
        ), percentiles AS (
            SELECT symbol, 100 * PERCENT_RANK() OVER (ORDER BY return_63) AS percentile
            FROM returns
        )
        SELECT percentile FROM percentiles WHERE symbol = :symbol
        """),
        engine,
        params={"symbol": symbol, "signal_date": signal_date, "history_start": signal_date - timedelta(days=500)},
    )
    return float(value.iloc[0]["percentile"]) if not value.empty else 0.0


def run_opportunity_backtest(start_date=None, end_date=None, save_to_db=True):
    end_date = end_date or date.today()
    start_date = start_date or end_date - timedelta(days=365)
    if start_date >= end_date:
        raise ValueError("start_date must be earlier than end_date")
    if end_date > date.today():
        raise ValueError("end_date cannot be in the future")
    if (end_date - start_date).days > 3650:
        raise ValueError("backtest period cannot exceed 10 years")
    symbols = _load_symbols(start_date, end_date)
    market = _prepare_market(start_date, end_date)
    stage_counts = {key: 0 for key in ("evaluated", "data_quality", "liquidity", "fundamentals", "breakout", "bull_regime", "high_confidence", "entered")}
    trades = []
    for symbol, raw, symbol_scores in _iter_symbol_data(symbols, start_date, end_date):
        if raw.empty:
            continue
        valid = raw[["open", "high", "low", "close", "volume"]].gt(0).all(axis=1)
        if len(raw) < MIN_HISTORY_ROWS:
            continue
        indicators = calculate_indicators(raw.copy())
        indicators["quality_pass"] = valid.rolling(MIN_HISTORY_ROWS).sum() >= int(MIN_HISTORY_ROWS * 0.95)
        indicators["median_turnover"] = (indicators["close"] * indicators["volume"]).rolling(20).median()
        indicators["median_volume"] = indicators["volume"].rolling(20).median()
        symbol_scores = symbol_scores.dropna().sort_values("screened_at")
        if symbol_scores.empty:
            indicators["fundamental_score"] = np.nan
        else:
            indicators = pd.merge_asof(indicators.sort_values("date"), symbol_scores, left_on="date", right_on="screened_at", direction="backward")
            indicators = indicators.rename(columns={"total_score": "fundamental_score"})
        in_period = indicators["date"].dt.date.between(start_date, end_date)
        quality_pass = in_period & indicators["quality_pass"]
        liquidity_pass = quality_pass & indicators["median_turnover"].ge(MIN_MEDIAN_TURNOVER) & indicators["median_volume"].ge(MIN_MEDIAN_VOLUME)
        fundamental_pass = liquidity_pass & indicators["fundamental_score"].ge(MIN_FUNDAMENTAL_SCORE)
        breakout_pass = fundamental_pass & indicators["ma20"].gt(indicators["ma50"]) & indicators["rsi"].gt(60) & indicators["close"].gt(indicators["high_20"].shift(1)) & indicators["volume_ratio"].gt(2) & indicators["adx"].gt(20)
        bull_pass = breakout_pass & indicators["date"].map(lambda value: market.get(value, {}).get("regime") == "BULL")
        stage_counts["evaluated"] += int(in_period.sum())
        stage_counts["data_quality"] += int(quality_pass.sum())
        stage_counts["liquidity"] += int(liquidity_pass.sum())
        stage_counts["fundamentals"] += int(fundamental_pass.sum())
        stage_counts["breakout"] += int(breakout_pass.sum())
        stage_counts["bull_regime"] += int(bull_pass.sum())
        last_exit_date = None
        for index in indicators.index[bull_pass]:
            row = indicators.iloc[index]
            previous = indicators.iloc[index - 1]
            signal_date = row["date"]
            if last_exit_date is not None and signal_date <= last_exit_date:
                continue
            regime = market[signal_date]
            momentum_percentile = _momentum_percentile(symbol, signal_date)
            technical_score, _ = _technical_score(row, previous)
            entry_low = float(row["close"])
            entry_high = entry_low + 0.5 * float(row["atr"])
            entry_reference = (entry_low + entry_high) / 2
            stop_loss = max(float(previous["high_20"]) - 0.5 * float(row["atr"]), entry_reference - 2 * float(row["atr"]))
            risk = entry_reference - stop_loss
            if risk <= 0:
                continue
            target_1 = entry_reference + 2 * risk
            target_2 = entry_reference + 3 * risk
            liquidity_component = min(10.0, 5 + 5 * float(row["median_turnover"]) / (10 * MIN_MEDIAN_TURNOVER))
            score = min(100.0, 35 * float(row["fundamental_score"]) / 100 + technical_score + 10 * momentum_percentile / 100 + liquidity_component + regime["regime_score"] + 10)
            if score < MIN_STOCKCHAIN_SCORE:
                continue
            stage_counts["high_confidence"] += 1
            trade = _simulate_trade(indicators, index, entry_low, entry_high, stop_loss, target_1, target_2)
            if trade is None:
                continue
            trade.update({"symbol": symbol, "signal_date": signal_date, "score": round(score, 2), "market_regime": regime["regime"], "entry_low": round(entry_low, 2), "entry_high": round(entry_high, 2), "stop_loss": round(stop_loss, 2), "target_1": round(target_1, 2), "target_2": round(target_2, 2)})
            trades.append(trade)
            last_exit_date = trade["exit_date"]
            stage_counts["entered"] += 1
    trades.sort(key=lambda trade: trade["signal_date"])
    result = {"generated_at": datetime.now(timezone.utc), "start_date": start_date, "end_date": end_date, "strategy": "BREAKOUT_OPPORTUNITY_V1", "stage_counts": stage_counts, "metrics": _metrics(trades), "trades": trades}
    if save_to_db:
        _save_result(result)
    return result


def _save_result(result):
    with engine.begin() as connection:
        run_id = connection.execute(text("""
            INSERT INTO opportunity_backtest_runs (strategy, start_date, end_date, stage_counts, metrics, generated_at)
            VALUES (:strategy, :start_date, :end_date, CAST(:stage_counts AS jsonb), CAST(:metrics AS jsonb), :generated_at)
            RETURNING id
        """), {**result, "stage_counts": json.dumps(result["stage_counts"]), "metrics": json.dumps(result["metrics"])}).scalar_one()
        for trade in result["trades"]:
            connection.execute(text("""
                INSERT INTO opportunity_backtest_trades (run_id, symbol, signal_date, entry_date, exit_date, entry_price, exit_price, entry_low, entry_high, stop_loss, target_1, target_2, score, market_regime, exit_reason, return_pct, target_1_hit, target_2_hit, stop_hit, mfe_pct, mae_pct)
                VALUES (:run_id, :symbol, :signal_date, :entry_date, :exit_date, :entry_price, :exit_price, :entry_low, :entry_high, :stop_loss, :target_1, :target_2, :score, :market_regime, :exit_reason, :return_pct, :target_1_hit, :target_2_hit, :stop_hit, :mfe_pct, :mae_pct)
            """), {**trade, "run_id": run_id})
    result["run_id"] = run_id


def get_latest_opportunity_backtest():
    with engine.connect() as connection:
        run = connection.execute(text("SELECT * FROM opportunity_backtest_runs ORDER BY generated_at DESC LIMIT 1")).mappings().first()
        if not run:
            return None
        trades = connection.execute(text("SELECT * FROM opportunity_backtest_trades WHERE run_id = :run_id ORDER BY signal_date DESC"), {"run_id": run["id"]}).mappings().all()
    return {**dict(run), "trades": [dict(trade) for trade in trades]}
