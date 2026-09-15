import pandas as pd
from pathlib import Path
from sqlalchemy import create_engine

DB_URL = "postgresql://postgres:Jayan%40123@localhost:5432/stockDB"
SECTOR_FILE = Path(__file__).resolve().parents[1] / "backend" / "data" / "sectors.csv.xlsx"

engine = create_engine(DB_URL)

df = pd.read_excel(SECTOR_FILE)
df = df.rename(columns={"Name": "symbol", "Sector": "sector"})

# Clean symbols
df["symbol"] = df["symbol"].str.strip().str.upper()

df.to_sql(
    "sectors",
    engine,
    if_exists="replace",
    index=False
)

print(f"Inserted {len(df)} sectors")