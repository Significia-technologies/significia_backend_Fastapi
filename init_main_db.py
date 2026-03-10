import uuid
from sqlalchemy import text
from app.database.session import engine
from app.database.base import Base
# Import all models to ensure they are registered with Base.metadata
from app.models.user import User
from app.models.tenant import Tenant
from app.models.connector import Connector
from app.models.ia_master import IAMaster, EmployeeDetails, AuditTrail

def init():
    print("Initializing main database...")
    Base.metadata.create_all(bind=engine)
    print("Tables created successfully.")
    
    with engine.connect() as conn:
        result = conn.execute(text("SELECT tablename FROM pg_catalog.pg_tables WHERE schemaname = 'public'"))
        tables = [row[0] for row in result]
        print(f"Current tables in public schema: {tables}")

if __name__ == "__main__":
    init()
