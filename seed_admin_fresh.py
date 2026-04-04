import uuid
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.tenant import Tenant
from app.models.user import User
from app.core.security import get_password_hash

DATABASE_URL = "postgresql+psycopg://significia:significia@localhost:5432/significia"

def seed():
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()

    try:
        # 1. Create Master Tenant
        tenant = db.query(Tenant).filter(Tenant.subdomain == "master").first()
        if not tenant:
            tenant = Tenant(
                id=uuid.uuid4(),
                name="Significia Core",
                subdomain="master",
                is_active=True
            )
            db.add(tenant)
            db.commit()
            db.refresh(tenant)
            print(f"Created Master Tenant: {tenant.id}")

        # 2. Create Super Admin User
        admin_email = "admin@significia.com"
        user = db.query(User).filter(User.email == admin_email).first()
        if not user:
            user = User(
                id=uuid.uuid4(),
                tenant_id=tenant.id,
                email=admin_email,
                email_normalized=admin_email.lower(),
                password_hash=get_password_hash("Admin@123"),
                role="super_admin",
                status="active"
            )
            db.add(user)
            db.commit()
            print(f"Created Super Admin: {admin_email}")
        else:
            print("Super Admin already exists.")

    except Exception as e:
        print(f"Seeding failed: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed()
