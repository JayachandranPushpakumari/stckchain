from fastapi import APIRouter
from services.backtest_service import (
    run_breakout_backtest,
    get_backtest_results,
    get_top_strategies,
    backtest_single_symbol
)

router = APIRouter()


# -----------------------------------
# Run Breakout Backtest
# -----------------------------------
@router.get("/backtest/breakout")
def breakout_backtest():

    result = run_breakout_backtest()

    return {
        "status": "success",
        "data": result
    }


# -----------------------------------
# Get All Results
# -----------------------------------
@router.get("/backtest/results")
def backtest_results():

    results = get_backtest_results()

    return results


# -----------------------------------
# Get Top Strategies
# -----------------------------------
@router.get("/backtest/top-strategies")
def top_strategies():

    results = get_top_strategies()

    return results


# -----------------------------------
# Backtest Single Symbol
# -----------------------------------
@router.get("/backtest/symbol/{symbol}")
def backtest_symbol(symbol: str):

    result = backtest_single_symbol(symbol.upper())

    return result