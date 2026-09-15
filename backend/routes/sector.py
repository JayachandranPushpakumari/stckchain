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

LEADERS_QUERY = text("""
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
        ((latest.close - old.close) / NULLIF(old.close, 0)) * 100 AS rs_score
    FROM latest_prices latest
    JOIN LATERAL (
        SELECT close
        FROM price_data old_price
        WHERE old_price.symbol = latest.symbol
          AND old_price.date <= latest.date - CAST(:lookback_interval AS interval)
        ORDER BY old_price.date DESC
        LIMIT 1
    ) old ON TRUE
),
latest_scores AS (
    SELECT DISTINCT ON (symbol)
        symbol,
        total_score
    FROM fundamental_scores
    ORDER BY symbol, screened_at DESC
),
ranked_leaders AS (
    SELECT
        sr.symbol,
        s.sector,
        ROUND(sr.rs_score::numeric, 2) AS rs_score,
        ls.total_score,
        DENSE_RANK() OVER (PARTITION BY s.sector ORDER BY sr.rs_score DESC) AS rank
    FROM symbol_returns sr
    JOIN sectors s
        ON sr.symbol = s.symbol
    LEFT JOIN latest_scores ls
        ON sr.symbol = ls.symbol
    WHERE sr.rs_score IS NOT NULL
)
SELECT symbol, sector, rs_score, total_score, rank
FROM ranked_leaders
WHERE rank <= 10
    AND (:sector IS NULL OR sector = :sector)
ORDER BY sector, rank
""")


def get_lookback_interval(period: str):
    return PERIOD_INTERVALS.get(period, PERIOD_INTERVALS["3m"])


@lru_cache(maxsize=32)
def get_sector_leaders_records(period: str, sector: str | None):
    df = pd.read_sql(
        LEADERS_QUERY,
        engine,
        params={"lookback_interval": get_lookback_interval(period), "sector": sector}
    )

    return tuple(df.to_dict(orient="records"))


@router.get("/leaders/sector-leaders")
def get_all_sector_leaders(period: str = "3m"):

    return list(get_sector_leaders_records(period, None))


@router.get("/leaders/sector/{sector}")
def get_sector_leaders(sector: str, period: str = "3m"):

    return list(get_sector_leaders_records(period, sector))
