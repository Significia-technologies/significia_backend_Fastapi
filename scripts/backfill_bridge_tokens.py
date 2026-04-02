import os
import uuid
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# DB connection details from backend/.env (standard docker setup)
DB_URL = "postgresql+psycopg2://significia:significia@localhost:5432/significia"

def backfill_tokens():
    engine = create_engine(DB_URL)
    Session = sessionmaker(bind=engine)
    session = Session()

    print("[*] Checking for tenants missing bridge tokens...")
    
    # Simple query to find tenants in PENDING status with no token
    # Using text() for simplicity to avoid importing models
    query = text("SELECT id, name FROM tenants WHERE bridge_status = 'PENDING' AND bridge_registration_token IS NULL")
    tenants = session.execute(query).fetchall()

    if not tenants:
        print("[+] No tenants need backfilling. System is clean!")
        return

    import secrets
    def generate_token():
        return secrets.token_urlsafe(64)

    for tenant_id, name in tenants:
        new_token = generate_token()
        print(f"[*] Backfilling token for {name} ({tenant_id})")
        update_query = text("UPDATE tenants SET bridge_registration_token = :token WHERE id = :id")
        session.execute(update_query, {"token": new_token, "id": tenant_id})

    session.commit()
    print(f"\n[+] Successfully backfilled {len(tenants)} tenants.")
    session.close()

if __name__ == "__main__":
    backfill_tokens()
