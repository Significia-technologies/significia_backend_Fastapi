import uuid
import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Main DB Config from .env
# Using local credentials found in .env
MAIN_DB_URL = "postgresql+psycopg://significia:significia@localhost:5432/significia"

engine = create_engine(MAIN_DB_URL)
SessionLocal = sessionmaker(bind=engine)
db = SessionLocal()

print("Checking Connectors in main DB...")
try:
    # Try with public schema first
    connectors = db.execute(text("SELECT id, name, database_name, initialization_status FROM connectors")).fetchall()
except Exception as e:
    print(f"Error querying connectors: {e}")
    db.rollback()
    try:
        # Try with explicitly 'public' schema
        connectors = db.execute(text("SELECT id, name, database_name, initialization_status FROM public.connectors")).fetchall()
    except Exception as e2:
        print(f"Error querying public.connectors: {e2}")
        connectors = []

for conn in connectors:
    print(f"Connector: {conn[1]} ({conn[0]}), DB: {conn[2]}, Status: {conn[3]}")
    
    if conn[3] == "READY":
        REMOTE_URL = f"postgresql+psycopg://significia:significia@localhost:5432/{conn[2]}"
        remote_engine = create_engine(REMOTE_URL, connect_args={"options": "-c search_path=significia_core,public"})
        RemoteSession = sessionmaker(bind=remote_engine)
        rdb = RemoteSession()
        
        try:
            print(f"  Querying ia_master in {conn[2]}...")
            # Check table existence and columns
            ia_masters = rdb.execute(text("SELECT * FROM significia_core.ia_master")).fetchall()
            if not ia_masters:
                print("    NO IA MASTER RECORDS FOUND")
            else:
                # Get column names
                cols_res = rdb.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name = 'ia_master' AND table_schema = 'significia_core'")).fetchall()
                col_names = [c[0] for c in cols_res]
                for row in ia_masters:
                    ia_dict = dict(zip(col_names, row))
                    print(f"    IA Master ID: {ia_dict.get('id')} - Name: {ia_dict.get('name_of_ia')} - Logo: {ia_dict.get('ia_logo_path')}")
        except Exception as e:
            print(f"    Error querying remote DB {conn[2]}: {e}")
        finally:
            rdb.close()

db.close()
