from datetime import date

from fastapi import APIRouter, HTTPException
from services.backtest_service import (
    run_breakout_backtest,
    get_backtest_results,
    get_top_strategies,
    backtest_single_symbol
)
from services.opportunity_backtest import get_latest_opportunity_backtest, run_opportunity_backtest

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


@router.post("/backtest/opportunities/run")
def opportunity_backtest(start_date: date | None = None, end_date: date | None = None):
    try:
        return run_opportunity_backtest(start_date=start_date, end_date=end_date)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/backtest/opportunities/latest")
def latest_opportunity_backtest():
    result = get_latest_opportunity_backtest()
    if result is None:
        raise HTTPException(status_code=404, detail="No Opportunity V1 backtest has been generated")
    return result