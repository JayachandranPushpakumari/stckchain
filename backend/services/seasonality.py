import pandas as pd
from functools import lru_cache
from sqlalchemy import text

from db import engine

def seasonal_stocks(month):

    query = text("""
    WITH monthly_prices AS (
        SELECT
            symbol,
            EXTRACT(YEAR FROM date)::int AS year,
            close,
            ROW_NUMBER() OVER (
                PARTITION BY symbol, EXTRACT(YEAR FROM date)
                ORDER BY date ASC
            ) AS first_row,
            ROW_NUMBER() OVER (
                PARTITION BY symbol, EXTRACT(YEAR FROM date)
                ORDER BY date DESC
            ) AS last_row
        FROM price_data
        WHERE EXTRACT(MONTH FROM date) = :month
          AND NOT (
              EXTRACT(YEAR FROM date) = EXTRACT(YEAR FROM CURRENT_DATE)
              AND EXTRACT(MONTH FROM date) = EXTRACT(MONTH FROM CURRENT_DATE)
              AND :month = EXTRACT(MONTH FROM CURRENT_DATE)
          )
    ),
    monthly_returns AS (
        SELECT
            symbol,
            year,
            MAX(close) FILTER (WHERE first_row = 1) AS start,
            MAX(close) FILTER (WHERE last_row = 1) AS "end"
        FROM monthly_prices
        GROUP BY symbol, year
    ),
    seasonality AS (
        SELECT
            symbol,
            year,
            ((("end" - start) / NULLIF(start, 0)) * 100) AS return_pct
        FROM monthly_returns
        WHERE start IS NOT NULL
          AND "end" IS NOT NULL
    ),
    last5_returns AS (
        SELECT
            symbol,
            ARRAY_AGG(ROUND(return_pct::numeric, 2) ORDER BY year DESC) AS yearly_returns
        FROM (
            SELECT symbol, year, return_pct,
                   ROW_NUMBER() OVER (PARTITION BY symbol ORDER BY year DESC) AS rn
            FROM seasonality
        ) ranked
        WHERE rn <= 5
        GROUP BY symbol
    ),
    latest_scores AS (
        SELECT DISTINCT ON (symbol)
            symbol,
            total_score
        FROM fundamental_scores
        ORDER BY symbol, screened_at DESC
    )
    SELECT
        seasonality.symbol,
        sectors.sector,
        latest_scores.total_score,
        ROUND(PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY return_pct)::numeric, 2) AS median_return,
        ROUND((AVG(CASE WHEN return_pct > 0 THEN 1 ELSE 0 END) * 100)::numeric, 2) AS win_rate,
        ROUND(((COALESCE(latest_scores.total_score, 0) * 0.6) + ((AVG(CASE WHEN return_pct > 0 THEN 1 ELSE 0 END) * 100) * 0.4))::numeric, 2) AS combined_score,
        last5_returns.yearly_returns
    FROM seasonality
    LEFT JOIN sectors
      ON seasonality.symbol = sectors.symbol
    LEFT JOIN latest_scores
      ON seasonality.symbol = latest_scores.symbol
    LEFT JOIN last5_returns
      ON seasonality.symbol = last5_returns.symbol
    GROUP BY seasonality.symbol, sectors.sector, latest_scores.total_score, last5_returns.yearly_returns
    HAVING COUNT(*) >= 3
       AND (AVG(CASE WHEN return_pct > 0 THEN 1 ELSE 0 END) * 100) >= 100
    ORDER BY combined_score DESC, win_rate DESC, median_return DESC
    LIMIT 100
    """)

    return pd.read_sql(query, engine, params={"month": month})


@lru_cache(maxsize=12)
def seasonal_stock_records(month):
    df = seasonal_stocks(month)

    return tuple(df.to_dict(orient="records"))
