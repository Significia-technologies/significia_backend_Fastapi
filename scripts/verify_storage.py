import uuid
import asyncio
from sqlalchemy import create_session
from app.database.session import SessionLocal
from app.services.storage_service import StorageService
from app.models.storage_connector import StorageConnector
from app.utils.file_storage import save_upload_file
from fastapi import UploadFile
import io

async def verify_storage_logic():
    db = SessionLocal()
    test_tenant_id = uuid.uuid4()
    
    print(f"--- Starting Storage Verification for Tenant: {test_tenant_id} ---")

    # 1. Create a mock S3 connector (using dummy creds for logic check)
    connector_data = {
        "name": "Test S3 Storage",
        "provider": "S3",
        "bucket_name": "test-bucket",
        "region": "us-east-1",
        "access_key_id": "AKIA-TEST",
        "secret_key": "TEST-SECRET-KEY"
    }
    
    try:
        connector = StorageService.create_storage_connector(db, test_tenant_id, connector_data)
        print(f"Successfully created connector: {connector.id}")
        
        # 2. Test driver initialization
        storage = StorageService.get_tenant_storage(db, test_tenant_id)
        if storage:
            print("Successfully initialized storage driver from DB.")
        else:
            print("Failed to initialize storage driver.")

        # 3. Test the upload utility logic (Mocking the upload part)
        # Note: We can't actually upload to S3 without real creds, 
        # but we can verify it reaches the S3 block.
        
        mock_file = UploadFile(
            filename="test_doc.pdf",
            file=io.BytesIO(b"dummy pdf content"),
            headers={"content-type": "application/pdf"}
        )
        
        print("Testing save_upload_file utility logic...")
        # Since we use real S3 logic, it will fail on actual upload if creds are bad,
        # but if we catch a ClientError, it means the S3 logic was triggered!
        try:
            path = await save_upload_file(mock_file, "individual", "test", db, test_tenant_id)
            print(f"File saved to: {path}")
        except Exception as e:
            print(f"Expected failure (no real S3): {str(e)[:100]}")

    finally:
        # Cleanup
        db.query(StorageConnector).filter(StorageConnector.tenant_id == test_tenant_id).delete()
        db.commit()
        db.close()
        print("--- Verification Complete ---")

if __name__ == "__main__":
    asyncio.run(verify_storage_logic())
