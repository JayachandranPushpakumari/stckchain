import json

from fastapi import APIRouter
from sqlalchemy import text

from db import engine
from services.opportunities import generate_breakout_opportunities

router = APIRouter(prefix="/internal/opportunities", tags=["internal-opportunities"])


@router.post("/breakout/run")
def run_breakout_opportunities():
    return generate_breakout_opportunities(save_to_db=True)


@router.get("/latest")
def latest_opportunities():
    with engine.connect() as connection:
        run = connection.execute(
            text("""
            SELECT id, setup_type, market_regime, stage_counts, minimum_score, generated_at
            FROM opportunity_runs
            ORDER BY generated_at DESC
            LIMIT 1
            """)
        ).mappings().first()
        if not run:
            return {"message": "No opportunity run has been generated.", "opportunities": []}
        rows = connection.execute(
            text("""
            SELECT symbol, setup_type, status, rank, score, current_price, entry_low, entry_high,
                   target_1, target_2, stop_loss, risk_reward, fundamental_score, technical_score,
                   momentum_score, liquidity_score, regime_score, risk_reward_score, market_regime, reasons
            FROM opportunities
            WHERE run_id = :run_id
            ORDER BY rank
            """),
            {"run_id": run["id"]},
        ).mappings().all()
    opportunities = [dict(row) for row in rows]
    for opportunity in opportunities:
        if isinstance(opportunity["reasons"], str):
            opportunity["reasons"] = json.loads(opportunity["reasons"])
    return {
        "run_id": run["id"],
        "generated_at": run["generated_at"],
        "setup_type": run["setup_type"],
        "market_regime": run["market_regime"],
        "stage_counts": run["stage_counts"],
        "minimum_score": run["minimum_score"],
        "message": None if opportunities else "No high-confidence opportunities today.",
        "opportunities": opportunities,
    }
