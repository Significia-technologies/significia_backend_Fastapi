import os
import sys

# Ensure the app module is in the python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database.session import engine
from sqlalchemy import text

def reset_database():
    print("=========================================")
    print("      DANGER: Full Database Reset       ")
    print("=========================================")
    
    with engine.connect() as conn:
        with conn.begin():
            # 1. Drop all tables in the public schema
            print("[*] Finding tables in 'public' schema...")
            result = conn.execute(text("SELECT tablename FROM pg_tables WHERE schemaname = 'public'"))
            tables = [row[0] for row in result]
            
            if tables:
                for table in tables:
                    print(f"    -> Dropping table public.{table}...")
                    conn.execute(text(f"DROP TABLE IF EXISTS public.\"{table}\" CASCADE"))
            else:
                print("    -> No tables found in public schema.")
            
            # 2. Drop the tenant schema entirely
            print("\n[*] Dropping tenant silo schema 'significia_core'...")
            conn.execute(text("DROP SCHEMA IF EXISTS significia_core CASCADE;"))
            
        print("\n[+] Database completely wiped.")
        
    print("\n=========================================")
    print("To recreate the database freshly, run:")
    print("1. alembic upgrade head")
    print("2. python scripts/seed_data.py")
    print("=========================================")

if __name__ == "__main__":
    print("WARNING: This will DESTROY all data in your Master and Tenant databases.")
    confirm = input("Are you SURE you want to proceed? Type 'RESET' to continue: ")
    if confirm == 'RESET':
        reset_database()
        
        # Optionally, automatically run migrations if requested
        run_alembic = input("Do you want to automatically run 'alembic upgrade head' now? (y/n): ")
        if run_alembic.lower() == 'y':
            print("\n[*] Running Alembic migrations...")
            os.system("alembic upgrade head")
            print("[+] Migrations complete.")
    else:
        print("Reset aborted.")
