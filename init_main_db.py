from app.database.session import engine
from sqlalchemy import text
from app.database.base import Base
# Import ONLY global models for Master DB
from app.models.user import User
from app.models.tenant import Tenant
from app.models.connector import Connector
from app.models.api_key import ApiKey
from app.models.refresh_token import RefreshToken
from app.models.user_session import UserSession
from app.models.login_attempt import LoginAttempt
from app.models.mfa_secret import MFASecret
from app.models.password_reset_token import PasswordResetToken
from app.models.verification_token import VerificationToken

def init():
    print("Initializing main database (Master Orchestrator)...")
    
    # Explicitly list only the tables we want in the Master DB
    # This prevents 'leakage' if other scripts import business models.
    master_tables = [
        User.__table__, Tenant.__table__, Connector.__table__,
        ApiKey.__table__, RefreshToken.__table__, UserSession.__table__,
        LoginAttempt.__table__, MFASecret.__table__, PasswordResetToken.__table__,
        VerificationToken.__table__
    ]
    
    Base.metadata.create_all(bind=engine, tables=master_tables)
    print("Master tables created successfully.")
    
    with engine.connect() as conn:
        result = conn.execute(text("SELECT tablename FROM pg_catalog.pg_tables WHERE schemaname = 'public'"))
        tables = [row[0] for row in result]
        print(f"Current tables in public schema: {tables}")

if __name__ == "__main__":
    init()

