import os
import sys

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from database.schema import metadata
from stockchain_db import engine


def run_migration():
    metadata.create_all(engine, checkfirst=True)
    print("Database schema baseline is present.")


if __name__ == "__main__":
    run_migration()
