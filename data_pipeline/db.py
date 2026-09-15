from sqlalchemy import create_engine

DB_URL = "postgresql://postgres:Jayan%40123@localhost:5432/stockDB"

engine = create_engine(DB_URL)