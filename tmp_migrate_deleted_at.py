import sys
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add the backend directory to sys.path
sys.path.append(os.getcwd())

from app.database.session import SessionLocal
from app.models.connector import Connector
from app.services.provisioner_service import ProvisionerService

def migrate_all():
    db = SessionLocal()
    try:
        connectors = db.query(Connector).filter(Connector.initialization_status == "READY").all()
        print(f"Found {len(connectors)} connectors to migrate.")
        
        for connector in connectors:
            print(f"Migrating connector: {connector.name} ({connector.id})")
            success = ProvisionerService.initialize_database(db, connector.id, connector.tenant_id)
            if success:
                print(f"Successfully migrated {connector.name}")
            else:
                print(f"Failed to migrate {connector.name}")
    except Exception as e:
        print(f"Error during migration: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    migrate_all()
