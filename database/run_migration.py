import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from db import engine
from sqlalchemy import text

def run_migration():
    sql_file = os.path.join(os.path.dirname(__file__), 'create_fundamental_scores_table.sql')
    
    with open(sql_file, 'r') as f:
        sql_script = f.read()
    
    with engine.connect() as connection:
        connection.execute(text(sql_script))
        connection.commit()
    
    print("Migration completed successfully! fundamental_scores table created.")

if __name__ == "__main__":
    run_migration()
