from fastapi import APIRouter
import pandas as pd
from functools import lru_cache
from sqlalchemy import text

from db import engine

router = APIRouter()

PERIOD_INTERVALS = {
    "1d": "1 day",
    "1w": "1 week",
    "1m": "1 month",
    "3m": "3 months",
    "6m": "6 months",
    "1y": "1 year",
}

ROTATION_PERIODS = ["1d", "1w", "1m", "3m", "6m"]


def get_sector_strength_frame(period: str):

    lookback_interval = PERIOD_INTERVALS.get(period, PERIOD_INTERVALS["3m"])

    query = text("""
    WITH latest_prices AS (
        SELECT DISTINCT ON (symbol)
            symbol,
            date,
            close
        FROM price_data
        ORDER BY symbol, date DESC
    ),
    symbol_returns AS (
        SELECT
            latest.symbol,
            ((latest.close - old.close) / NULLIF(old.close, 0)) * 100 AS pct_return
        FROM latest_prices latest
        JOIN LATERAL (
            SELECT close
            FROM price_data old_price
            WHERE old_price.symbol = latest.symbol
              AND old_price.date <= latest.date - CAST(:lookback_interval AS interval)
            ORDER BY old_price.date DESC
            LIMIT 1
        ) old ON TRUE
    )
    SELECT
        s.sector,
        ROUND(AVG(sr.pct_return)::numeric, 2) AS strength
    FROM symbol_returns sr
    JOIN sectors s
        ON sr.symbol = s.symbol
    WHERE sr.pct_return IS NOT NULL
    GROUP BY s.sector
    ORDER BY strength DESC
    """)

    return pd.read_sql(query, engine, params={"lookback_interval": lookback_interval})


@lru_cache(maxsize=16)
def get_sector_strength_records(period: str):
    df = get_sector_strength_frame(period)

    return tuple(df.to_dict(orient="records"))

@router.get("/heatmap/sectors")
def sector_heatmap(period: str = "3m"):

    return list(get_sector_strength_records(period))


@router.get("/heatmap/sector-rotation")
def sector_rotation():

    rotation = {}

    for period in ROTATION_PERIODS:
        df = pd.DataFrame(get_sector_strength_records(period))
        df["rank"] = range(1, len(df) + 1)

        for row in df.to_dict(orient="records"):
            sector = row["sector"]
            rotation.setdefault(sector, {"sector": sector})
            rotation[sector][period] = int(row["rank"])

    rows = []
    for item in rotation.values():
        ranks = [item.get(period) for period in ROTATION_PERIODS if item.get(period)]
        if not ranks:
            continue

        average_rank = sum(ranks) / len(ranks)
        one_week_rank = item.get("1w", average_rank)
        six_month_rank = item.get("6m", average_rank)
        momentum_change = six_month_rank - one_week_rank
        momentum_bonus = max(0, momentum_change)
        score = max(0, min(100, round(100 - (average_rank - 1) * 3 + momentum_bonus * 2)))

        item["momentum_change"] = int(momentum_change)
        item["score"] = score
        rows.append(item)

    rows.sort(key=lambda row: (row["momentum_change"], row["score"]), reverse=True)

    return rows

