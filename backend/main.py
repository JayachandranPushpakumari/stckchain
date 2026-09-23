import os
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
import pandas as pd

load_dotenv()
from auth import router as auth_router, require_auth
from db import engine
from routes.signals import router as signal_router
from routes.breakout import router as breakout_router
from routes.swing import router as swing_router
from routes.backtest import router as backtest_router
from routes.relative_strength import router as rs_router
from routes import sector_rotation
from routes import sector
from routes import heatmap
from routes import seasonality
from routes import opportunities


app = FastAPI()

def dataframe_to_json_records(df: pd.DataFrame):
    cleaned_df = df.replace([float("inf"), float("-inf")], pd.NA)
    cleaned_df = cleaned_df.astype(object).where(pd.notna(cleaned_df), None)
    return cleaned_df.to_dict(orient="records")

_raw_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:4200,http://127.0.0.1:4200")
_allowed_origins = [o.strip() for o in _raw_origins.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(signal_router, dependencies=[Depends(require_auth)])
app.include_router(breakout_router, dependencies=[Depends(require_auth)])
app.include_router(swing_router, dependencies=[Depends(require_auth)])
app.include_router(backtest_router, dependencies=[Depends(require_auth)])
app.include_router(rs_router, dependencies=[Depends(require_auth)])
app.include_router(sector_rotation.router, dependencies=[Depends(require_auth)])
app.include_router(sector.router, dependencies=[Depends(require_auth)])
app.include_router(heatmap.router, dependencies=[Depends(require_auth)])
app.include_router(seasonality.router, dependencies=[Depends(require_auth)])
app.include_router(opportunities.router, dependencies=[Depends(require_auth)])

@app.get("/")
def home():
    return {"message": "StockChain API Running"}

@app.get("/health")
def health():
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Database unavailable") from exc
    return {"status": "ok"}

# 🔹 Existing API
@app.get("/stocks/{symbol}", dependencies=[Depends(require_auth)])
def get_stock(symbol: str):
    query = text("""
    SELECT date, symbol, open, high, low, close, volume
    FROM price_data
    WHERE symbol = :symbol
    ORDER BY date DESC
    LIMIT 100
    """)
    
    df = pd.read_sql(query, engine, params={"symbol": symbol.upper()})
    return dataframe_to_json_records(df)

@app.get("/stocks/{symbol}/history", dependencies=[Depends(require_auth)])
def get_stock_history(symbol: str, limit: int = 500):
    normalized_limit = max(50, min(limit, 2000))
    query = text("""
    SELECT date, close
    FROM (
        SELECT date, close
        FROM price_data
        WHERE symbol = :symbol
        ORDER BY date DESC
        LIMIT :limit
    ) AS recent_prices
    ORDER BY date
    """)

    df = pd.read_sql(query, engine, params={"symbol": symbol.upper(), "limit": normalized_limit})
    if not df.empty:
        df["date"] = df["date"].astype(str)

    return {
        "symbol": symbol.upper(),
        "frequency": "1D",
        "prices": dataframe_to_json_records(df),
    }

@app.get("/scan", dependencies=[Depends(require_auth)])
def scan_market():
    query = text("""
    SELECT recent_prices.date, symbols.symbol, recent_prices.close
    FROM (
        SELECT DISTINCT symbol
        FROM price_data
    ) AS symbols
    CROSS JOIN LATERAL (
        SELECT date, close
        FROM price_data
        WHERE symbol = symbols.symbol
        ORDER BY date DESC
        LIMIT 60
    ) AS recent_prices
    ORDER BY symbols.symbol, recent_prices.date
    """)

    results = []
    prices = pd.read_sql(query, engine)

    for symbol, df in prices.groupby("symbol"):
        df = df.copy()
        df["close"] = pd.to_numeric(df["close"], errors="coerce")
        df = df.dropna(subset=["close"])
        if len(df) < 50:
            continue

        df["ma20"] = df["close"].rolling(20).mean()
        df["ma50"] = df["close"].rolling(50).mean()

        delta = df["close"].diff()
        gain = (delta.where(delta > 0, 0)).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = gain / loss
        df["rsi"] = 100 - (100 / (1 + rs))

        latest = df.iloc[-1]

        if latest["ma20"] > latest["ma50"] and latest["rsi"] < 35:
            results.append({
                "symbol": symbol,
                "price": float(latest["close"]),
                "rsi": round(latest["rsi"], 2),
                "signal": "BUY"
            })

    return results