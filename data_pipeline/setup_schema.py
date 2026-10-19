"""
Bootstrap a fresh PostgreSQL database for StockChain.

Run this ONCE before the regular pipeline when starting with an empty database:
  - Creates all required tables so downstream pipeline steps don't crash on
    missing-table errors.
  - Populates the `stocks` table from fundamentals.xlsx so fetch_yahoo_data.py
    can read the symbol list on the very first run.

Safe to re-run: uses CREATE TABLE IF NOT EXISTS and skips symbol insertion when
stocks already has rows.
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd
from sqlalchemy import text
from stockchain_db import engine

# ---------------------------------------------------------------------------
# 1. Create all tables needed by the pipeline
# ---------------------------------------------------------------------------
DDL = """
CREATE TABLE IF NOT EXISTS stocks (
    symbol TEXT PRIMARY KEY
);

CREATE TABLE IF NOT EXISTS price_data (
    date   DATE    NOT NULL,
    symbol TEXT    NOT NULL,
    open   NUMERIC,
    high   NUMERIC,
    low    NUMERIC,
    close  NUMERIC,
    volume BIGINT,
    PRIMARY KEY (date, symbol)
);

CREATE TABLE IF NOT EXISTS fundamental_scores (
    symbol      TEXT,
    total_score NUMERIC,
    date        DATE
);

CREATE TABLE IF NOT EXISTS relative_strength (
    symbol   TEXT,
    rs_score NUMERIC
);

CREATE TABLE IF NOT EXISTS breakout_results (
    symbol TEXT
);

CREATE TABLE IF NOT EXISTS sectors (
    symbol TEXT,
    sector TEXT
);

CREATE TABLE IF NOT EXISTS sector_strength (
    sector   TEXT,
    rs_score NUMERIC
);

CREATE TABLE IF NOT EXISTS sector_leaders (
    sector   TEXT,
    symbol   TEXT,
    rs_score NUMERIC
);

CREATE TABLE IF NOT EXISTS opportunity_runs (
    id               SERIAL PRIMARY KEY,
    generated_at     TIMESTAMP,
    run_date         DATE,
    market_regime    TEXT,
    total_candidates INTEGER,
    published_count  INTEGER
);

CREATE TABLE IF NOT EXISTS opportunities (
    run_id            INTEGER,
    symbol            TEXT,
    pattern           TEXT,
    entry_low         NUMERIC,
    entry_high        NUMERIC,
    stop_loss         NUMERIC,
    target            NUMERIC,
    risk_reward       NUMERIC,
    fundamental_score NUMERIC,
    signal_date       DATE
);
"""

with engine.begin() as conn:
    conn.execute(text(DDL))
print("All tables created (or already exist).")

# ---------------------------------------------------------------------------
# 2. Populate `stocks` from fundamentals.xlsx (skip if already populated)
# ---------------------------------------------------------------------------
with engine.connect() as conn:
    count = conn.execute(text("SELECT COUNT(*) FROM stocks")).scalar()

if count and count > 0:
    print(f"stocks table already has {count} rows — skipping symbol load.")
else:
    xlsx_path = Path(__file__).parent / "fundamentals.xlsx"
    df = pd.read_excel(xlsx_path)
    df.columns = df.columns.str.strip().str.lower()

    # Accept either 'stockname' or 'symbol' column
    if "stockname" in df.columns:
        symbols = df["stockname"].dropna().str.strip().unique().tolist()
    elif "symbol" in df.columns:
        symbols = df["symbol"].dropna().str.strip().unique().tolist()
    else:
        raise RuntimeError("fundamentals.xlsx has neither 'stockname' nor 'symbol' column")

    # Append .NS suffix for Yahoo Finance (NSE equities)
    ns_symbols = [s if s.endswith(".NS") else f"{s}.NS" for s in symbols if s]

    stocks_df = pd.DataFrame({"symbol": ns_symbols})
    stocks_df.to_sql("stocks", engine, if_exists="append", index=False, method="multi")
    print(f"Inserted {len(ns_symbols)} symbols into stocks table.")
