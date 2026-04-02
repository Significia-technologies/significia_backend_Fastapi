import asyncio
import uuid
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.tenant import Tenant
from app.services.bridge_client import BridgeClient

async def debug():
    # Master DB
    db_url = "postgresql+psycopg://significia:significia@localhost:5432/significia"
    engine = create_engine(db_url)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    try:
        # Get the voltfleet tenant (or any active tenant)
        tenant = db.query(Tenant).filter(Tenant.subdomain == "voltfleet").first()
        if not tenant:
            print("❌ Tenant 'voltfleet' not found.")
            # List all tenants
            tenants = db.query(Tenant).all()
            for t in tenants:
                print(f"  Found: {t.subdomain} (ID: {t.id})")
            return

        print(f"Found tenant: {tenant.name} (Slug: {tenant.subdomain})")
        print(f"  Bridge URL: {tenant.bridge_url}")
        print(f"  Status: {tenant.bridge_status}")
        
        # Mimic BridgeClient call
        bridge = BridgeClient(tenant)
        print(f"Connecting to Bridge at {bridge.base_url}...")
        
        try:
            result = await bridge.get("/clients")
            print(f"✅ Success! Bridge returned: {result}")
        except Exception as e:
            print(f"❌ Bridge call failed: {e}")
            if hasattr(e, 'status_code'):
                print(f"   Status Code: {e.status_code}")
            if hasattr(e, 'detail'):
                print(f"   Detail: {e.detail}")

    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(debug())
