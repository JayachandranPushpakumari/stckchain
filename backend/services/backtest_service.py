import pandas as pd
import numpy as np
from sqlalchemy import create_engine

from strategies.breakout import breakout_strategy
from backtest_metrics import calculate_metrics


def sanitize_for_json(data):
    """Replace NaN and infinity values with None for JSON serialization"""
    if isinstance(data, list):
        return [sanitize_for_json(item) for item in data]
    elif isinstance(data, dict):
        return {key: sanitize_for_json(value) for key, value in data.items()}
    elif isinstance(data, float):
        if np.isnan(data) or np.isinf(data):
            return None
        return data
    return data


DATABASE_URL = "postgresql://postgres:Jayan%40123@localhost:5432/stockDB"

engine = create_engine(DATABASE_URL)


# --------------------------------------------------
# RUN BACKTEST
# --------------------------------------------------
def run_breakout_backtest():

    symbols_query = """
    SELECT DISTINCT a.symbol
    FROM price_data a inner join fundamental_scores b
	on a.symbol = b.symbol
	and total_score >=60
    """

    symbols_df = pd.read_sql(symbols_query, engine)

    all_results = []

    for symbol in symbols_df["symbol"]:

        query = f"""
        SELECT date, open, high, low, close, volume
        FROM price_data
        WHERE symbol = '{symbol}'
        ORDER BY date
        """

        df = pd.read_sql(query, engine, parse_dates=['date'], index_col='date')

        if len(df) < 250:
            continue

        trades = breakout_strategy(df)

        if len(trades) == 0:
            continue

        metrics = calculate_metrics(trades)

        metrics["symbol"] = symbol

        all_results.append(metrics)

    results_df = pd.DataFrame(all_results)

    # Save results into DB
    results_df.to_sql(
        "backtest_results",
        engine,
        if_exists="replace",
        index=False
    )

    return sanitize_for_json(all_results)


# --------------------------------------------------
# GET RESULTS
# --------------------------------------------------
def get_backtest_results():

    query = """
    SELECT *
    FROM backtest_results
    ORDER BY win_rate DESC
    """

    df = pd.read_sql(query, engine)

    return sanitize_for_json(df.to_dict(orient="records"))


# --------------------------------------------------
# TOP STRATEGIES
# --------------------------------------------------
def get_top_strategies():

    query = """
    SELECT *
    FROM backtest_results
    WHERE win_rate > 55
    AND profit_factor > 1.5
    ORDER BY cagr DESC
    """

    df = pd.read_sql(query, engine)

    return sanitize_for_json(df.to_dict(orient="records"))


# --------------------------------------------------
# BACKTEST SINGLE SYMBOL
# --------------------------------------------------
def backtest_single_symbol(symbol: str):

    query = f"""
    SELECT date, open, high, low, close, volume
    FROM price_data
    WHERE symbol = '{symbol}'
    ORDER BY date
    """

    df = pd.read_sql(query, engine, parse_dates=['date'], index_col='date')

    if len(df) == 0:
        return {
            "error": f"No data found for {symbol}.",
            "symbol": symbol,
            "data_points": 0
        }

    trades = breakout_strategy(df)

    if len(trades) == 0:
        return {
            "error": f"No trades generated for {symbol} using the breakout strategy.",
            "symbol": symbol,
            "data_points": len(df)
        }

    metrics = calculate_metrics(trades)
    metrics["symbol"] = symbol
    metrics["total_data_points"] = len(df)
    metrics["trades_list"] = sanitize_for_json(list(reversed(trades)))

    return sanitize_for_json(metrics)