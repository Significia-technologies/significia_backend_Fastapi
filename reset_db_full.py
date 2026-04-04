import os
from sqlalchemy import create_engine, text

# Configuration
POSTGRES_URL = "postgresql+psycopg://significia:significia@localhost:5432/postgres"
MAIN_DB = "significia"

def reset_db():
    print("Connecting to postgres to manage databases...")
    engine = create_engine(POSTGRES_URL, isolation_level="AUTOCOMMIT")
    
    with engine.connect() as conn:
        # 1. Terminate connections and find databases
        print("Identifying significia-related databases...")
        dbs_to_drop = []
        result = conn.execute(text("SELECT datname FROM pg_database WHERE datname LIKE 'significia%';"))
        for row in result:
            dbs_to_drop.append(row[0])
            
        print(f"Found {len(dbs_to_drop)} databases to drop: {dbs_to_drop}")
        
        for db in dbs_to_drop:
            print(f"Dropping database {db}...")
            # Terminate active connections
            conn.execute(text(f"""
                SELECT pg_terminate_backend(pg_stat_activity.pid)
                FROM pg_stat_activity
                WHERE pg_stat_activity.datname = '{db}'
                  AND pid <> pg_backend_pid();
            """))
            # Drop the database
            conn.execute(text(f"DROP DATABASE IF EXISTS {db};"))
            print(f"Dropped: {db}")

        # 2. Recreate the main database
        print(f"Recreating main database: {MAIN_DB}...")
        conn.execute(text(f"CREATE DATABASE {MAIN_DB} OWNER significia;"))
        print(f"Successfully recreated: {MAIN_DB}")

if __name__ == "__main__":
    reset_db()
