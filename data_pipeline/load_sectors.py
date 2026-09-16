import pandas as pd
from pathlib import Path
from db import engine

SECTOR_FILE = Path(__file__).resolve().parents[1] / "backend" / "data" / "sectors.csv.xlsx"

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