import pandas as pd
import numpy as np


def calculate_metrics(trades):
    """
    trades = list of trade dictionaries with entry_date, exit_date, and return
    Example:
    [{"entry_date": "2024-01-01", "exit_date": "2024-02-01", "return": 5}, ...]
    """

    trade_returns = pd.Series([t["return"] for t in trades])
    trades = trade_returns

    # -----------------------------
    # Total Trades
    # -----------------------------
    total_trades = len(trades)

    # -----------------------------
    # Winning / Losing Trades
    # -----------------------------
    wins = trades[trades > 0]
    losses = trades[trades < 0]

    # -----------------------------
    # Win Rate
    # -----------------------------
    win_rate = (len(wins) / total_trades) * 100 if total_trades > 0 else 0

    # -----------------------------
    # Average Return
    # -----------------------------
    avg_return = trades.mean()

    # -----------------------------
    # Profit Factor
    # -----------------------------
    gross_profit = wins.sum()

    gross_loss = abs(losses.sum())

    profit_factor = (
        gross_profit / gross_loss
        if gross_loss != 0
        else np.inf
    )

    # -----------------------------
    # Equity Curve
    # -----------------------------
    equity_curve = (1 + trades / 100).cumprod()

    # -----------------------------
    # Drawdown
    # -----------------------------
    rolling_max = equity_curve.cummax()

    drawdown = (
        (equity_curve - rolling_max) / rolling_max
    ) * 100

    max_drawdown = drawdown.min()

    # -----------------------------
    # CAGR
    # -----------------------------
    years = 5

    ending_value = equity_curve.iloc[-1]

    cagr = (
        (ending_value ** (1 / years)) - 1
    ) * 100

    # -----------------------------
    # Final Result
    # -----------------------------
    result = {
        "total_trades": total_trades,
        "win_rate": round(win_rate, 2),
        "avg_return": round(avg_return, 2),
        "profit_factor": round(profit_factor, 2),
        "max_drawdown": round(max_drawdown, 2),
        "cagr": round(cagr, 2)
    }

    return result