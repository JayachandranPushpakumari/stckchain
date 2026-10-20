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
    id            SERIAL PRIMARY KEY,
    setup_type    TEXT,
    market_regime TEXT,
    stage_counts  JSONB,
    minimum_score NUMERIC,
    generated_at  TIMESTAMP
);

CREATE TABLE IF NOT EXISTS opportunities (
    run_id            INTEGER,
    symbol            TEXT,
    setup_type        TEXT,
    status            TEXT,
    rank              INTEGER,
    score             NUMERIC,
    current_price     NUMERIC,
    entry_low         NUMERIC,
    entry_high        NUMERIC,
    target_1          NUMERIC,
    target_2          NUMERIC,
    stop_loss         NUMERIC,
    risk_reward       NUMERIC,
    fundamental_score NUMERIC,
    technical_score   NUMERIC,
    momentum_score    NUMERIC,
    liquidity_score   NUMERIC,
    regime_score      NUMERIC,
    risk_reward_score NUMERIC,
    market_regime     TEXT,
    reasons           JSONB
);
"""

with engine.begin() as conn:
    conn.execute(text(DDL))
print("All tables created (or already exist).")

# ---------------------------------------------------------------------------
# 2. Populate `stocks` from fundamentals.xlsx (upsert — safe to re-run)
# ---------------------------------------------------------------------------

# Extra symbols not in fundamentals.xlsx (e.g. BSE-listed stocks)
EXTRA_SYMBOLS = [
    "GANESHHOU.BO",
]

xlsx_path = Path(__file__).parent / "fundamentals.xlsx"
df = pd.read_excel(xlsx_path)
df.columns = df.columns.str.strip().str.lower()

# Accept either 'stockname' or 'symbol' column
if "stockname" in df.columns:
    raw_symbols = df["stockname"].dropna().str.strip().unique().tolist()
elif "symbol" in df.columns:
    raw_symbols = df["symbol"].dropna().str.strip().unique().tolist()
else:
    raise RuntimeError("fundamentals.xlsx has neither 'stockname' nor 'symbol' column")

# Append .NS suffix for Yahoo Finance (NSE equities)
ns_symbols = [s if "." in s else f"{s}.NS" for s in raw_symbols if s]

all_symbols = list(dict.fromkeys(ns_symbols + EXTRA_SYMBOLS))  # deduplicate, preserve order

# Upsert: insert new symbols, ignore duplicates (PRIMARY KEY conflict)
with engine.begin() as conn:
    conn.execute(
        text("INSERT INTO stocks (symbol) VALUES (:sym) ON CONFLICT (symbol) DO NOTHING"),
        [{"sym": s} for s in all_symbols],
    )
print(f"Upserted {len(all_symbols)} symbols into stocks table ({len(EXTRA_SYMBOLS)} extra).")
