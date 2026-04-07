import uuid
from sqlalchemy.orm import Session
from app.database.session import SessionLocal
from app.models.tenant import Tenant
from app.models.user import User
from app.core.security import get_password_hash

def seed_db():
    print("Seeding database with initial super user...")
    db: Session = SessionLocal()
    try:
        # 1. Create System Tenant
        tenant = db.query(Tenant).filter(Tenant.subdomain == "admin").first()
        if not tenant:
            tenant = Tenant(
                id=uuid.uuid4(),
                name="Significia Admin",
                subdomain="admin",
                is_active=True,
                billing_plan="enterprise"
            )
            db.add(tenant)
            db.flush()
            print(f"Created System Tenant: {tenant.id}")
        else:
            print("System Tenant already exists.")

        # 2. Create Super Admin User
        admin_email = "admin@significia.com"
        admin_user = db.query(User).filter(User.email == admin_email).first()
        if not admin_user:
            admin_user = User(
                id=uuid.uuid4(),
                tenant_id=tenant.id,
                email=admin_email,
                email_normalized=admin_email.lower(),
                password_hash=get_password_hash("Admin@123"), # Default password
                role="super_admin",
                status="active",
                is_email_verified=True
            )
            db.add(admin_user)
            print(f"Created Super Admin: {admin_email}")
        else:
            print("Super Admin user already exists.")

        db.commit()
        print("Database seeding completed.")
    except Exception as e:
        print(f"Error seeding database: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_db()
