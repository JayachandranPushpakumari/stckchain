import os
from dotenv import load_dotenv
from sqlalchemy import create_engine

load_dotenv()

DB_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:Jayan%40123@localhost:5432/stockDB"
)

engine = create_engine(DB_URL)