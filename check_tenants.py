import sys
import os
from sqlalchemy import create_engine, text

def check_tenants():
    db_url = "postgresql+psycopg://significia:significia@localhost:5432/significia"
    engine = create_engine(db_url)
    
    print(f"Checking tenants in {db_url}...")
    try:
        with engine.connect() as conn:
            res = conn.execute(text("SELECT id, name, slug, bridge_url, bridge_status FROM tenants"))
            rows = res.fetchall()
            if not rows:
                print("❌ No tenants found.")
                return
                
            for row in rows:
                print(f"Tenant: {row.name} (Slug: {row.slug})")
                print(f"  ID: {row.id}")
                print(f"  Bridge URL: {row.bridge_url}")
                print(f"  Status: {row.bridge_status}")
    except Exception as e:
        print(f"❌ Error during check: {e}")

if __name__ == "__main__":
    check_tenants()
