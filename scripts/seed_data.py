import os
import sys
import uuid
import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Ensure the app module is in the python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database.session import SessionLocal
from app.services.auth_service import AuthService
from app.schemas.auth_schema import UserRegisterRequest
from app.repositories.user_repository import UserRepository
from app.repositories.tenant_repository import TenantRepository
from app.services.connector_service import ConnectorService
from app.schemas.connector_schema import ConnectorCreate
from app.services.provisioner_service import ProvisionerService
from app.models.ia_master import IAMaster, EmployeeDetails
from app.models.client import ClientProfile
from app.utils.encryption import decrypt_string
from init_main_db import init as init_master_db

def seed_database():
    print("=========================================")
    print("      Starting Data Seeding Process     ")
    print("=========================================")
    
    print("\n[1/5] Initializing Master Database...")
    try:
        init_master_db()
    except Exception as e:
        print(f"Master DB Init skipped or failed (might already exist): {e}")

    db = SessionLocal()
    auth_service = AuthService()
    user_repo = UserRepository()
    tenant_repo = TenantRepository()
    
    try:
        # SUPER USER
        print("\n[2/5] Setting up Super User...")
        sys_email = "alamtanbir@gmail.com"
        # Using the script we just updated to keep logic centralized
        import create_superuser
        create_superuser.create_superuser(sys_email, "T@nbir#2026")

        # IA MASTER (TENANT OWNER)
        print("\n[3/5] Setting up Demo IA Master (Tenant Owner)...")
        demo_email = "demo.master@example.com"
        demo_company = "Demo Advisors LLC"
        demo_subdomain = "demo"
        
        existing_owner = user_repo.get_by_email(db, demo_email)
        if not existing_owner:
            owner_req = UserRegisterRequest(
                email=demo_email,
                password="Password123!",
                company_name=demo_company,
                subdomain=demo_subdomain
            )
            print(f"[*] Registering IA Master '{demo_company}'...")
            demo_user = auth_service.register_user(db, owner_req)
            demo_tenant_id = demo_user.tenant_id
            print(f"[+] IA Master created. Tenant ID: {demo_tenant_id}")
            
            # Update tenant to have a custom domain for testing domain resolution
            tenant_db = tenant_repo.get_by_id(db, demo_tenant_id)
            if tenant_db:
                tenant_db.custom_domain = "demo.significia.com"
                db.commit()
                print(f"[+] Set custom domain: demo.significia.com")
        else:
            print(f"[*] Demo IA Master already exists. Tenant ID: {existing_owner.tenant_id}")
            demo_tenant_id = existing_owner.tenant_id

        # DATABASE PROVISIONING (SILO)
        print("\n[4/5] Provisioning Database Silo for Demo IA...")
        connectors = ConnectorService.list_connectors(db, demo_tenant_id)
        
        if not connectors:
            print("[*] Creating Connector for existing database...")
            # For simplicity in local dev, point to the same DB, Provisioner creates schema
            conn_in = ConnectorCreate(
                name="Demo Postgres DB",
                type="postgresql",
                host="localhost",
                port=5432,
                database_name="significia",
                username="significia",
                password="significia"
            )
            connector = ConnectorService.create_connector(db, demo_tenant_id, conn_in)
            print(f"[+] Connector created with ID: {connector.id}")
            
            print("[*] Running Provisioner (creating schemas and silo tables)...")
            success = ProvisionerService.initialize_database(db, connector.id, dict(id=demo_tenant_id)['id']) # Ensure we pass uuid
            if success:
                print("[+] Provisioning Successful!")
            else:
                print("[-] Provisioning Failed.")
                return
        else:
            connector = connectors[0]
            print(f"[*] Connector already exists. Status: {connector.initialization_status}")
            if connector.initialization_status != "READY":
                print("[*] Provisioning now...")
                success = ProvisionerService.initialize_database(db, connector.id, demo_tenant_id)
                if not success:
                    print("[-] Provisioning Failed.")
                    return

        # SEED SILO DATA (BUSINESS TABLES)
        print("\n[5/5] Seeding Business Data into Silo...")
        password = decrypt_string(connector.encrypted_password)
        db_url = f"postgresql+psycopg://{connector.username}:{password}@{connector.host}:{connector.port}/{connector.database_name}"
        engine = create_engine(db_url, connect_args={"options": "-c search_path=significia_core,public"})
        RemoteSession = sessionmaker(bind=engine)
        client_db = RemoteSession()
        
        try:
            # Check if IAMaster already exists in silo
            existing_ia = client_db.query(IAMaster).first()
            if not existing_ia:
                print("[*] Creating IAMaster Profile...")
                ia_profile = IAMaster(
                    name_of_ia="Demo Advisors LLC",
                    date_of_birth=datetime.date(2000, 1, 1),
                    nature_of_entity="LLC",
                    ia_registration_number=f"INA{uuid.uuid4().hex[:10].upper()}",
                    date_of_registration=datetime.date(2020, 1, 1),
                    date_of_registration_expiry=datetime.date(2025, 1, 1),
                    registered_address="123 Financial Ave, NY",
                    registered_contact_number="555-0100",
                    registered_email_id=demo_email,
                    bank_account_number="1234567890",
                    bank_name="Test Bank",
                    bank_branch="Main",
                    ifsc_code="TEST0001234"
                )
                client_db.add(ia_profile)
                client_db.commit()
                client_db.refresh(ia_profile)
                print(f"[+] IAMaster Profile Created (ID: {ia_profile.id})")
                
                print("[*] Creating Employee Details...")
                employee = EmployeeDetails(
                    ia_master_id=ia_profile.id,
                    name_of_employee="Alice Advisor",
                    date_of_birth=datetime.date(1990, 5, 15),
                    designation="Senior Analyst",
                    ia_registration_number=ia_profile.ia_registration_number,
                    date_of_registration=datetime.date(2021, 1, 1)
                )
                client_db.add(employee)
                client_db.commit()
                
                print("[*] Creating Client Profiles...")
                client1 = ClientProfile(
                    email="client1@example.com",
                    email_normalized="client1@example.com",
                    password_hash="dummyhash",
                    client_code="C001",
                    client_name="Bob Investor",
                    date_of_birth=datetime.date(1985, 10, 20),
                    pan_number="ABCDE1234F",
                    phone_number="555-0101",
                    address="456 Wall St",
                    occupation="Engineer",
                    gender="Male",
                    marital_status="Married",
                    nationality="Indian",
                    residential_status="Resident",
                    tax_residency="India",
                    pep_status="No",
                    father_name="John Investor",
                    mother_name="Jane Investor",
                    annual_income=150000.0,
                    net_worth=500000.0,
                    income_source="Salary",
                    fatca_compliance="Yes",
                    bank_account_number="9876543210",
                    bank_name="Client Bank",
                    bank_branch="Downtown",
                    ifsc_code="CLBNK0001",
                    risk_profile="Aggressive",
                    investment_experience="Expert",
                    investment_objectives="Growth",
                    investment_horizon="Long Term",
                    liquidity_needs="Low",
                    advisor_name="Alice Advisor",
                    advisor_registration_number=ia_profile.ia_registration_number
                )
                client_db.add(client1)
                client_db.commit()
                print(f"[+] Added Client: Bob Investor (C001)")
            else:
                print("[*] Silo data already seeded.")
        finally:
            client_db.close()

        print("\n=========================================")
        print("          Seeding Complete!              ")
        print("=========================================")
        print("Test Accounts:")
        print(f"1. Super Admin: {sys_email} / T@nbir#2026 (Root Domain)")
        print(f"2. IA Master:   {demo_email} / Password123! (Subdomain: {demo_subdomain} or demo.significia.com)")

    except Exception as e:
        print(f"\n[!] Fatal Error during seeding: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
