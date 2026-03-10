import uuid
import json
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from fastapi import UploadFile

from app.repositories.ia_master_repository import IAMasterRepository
from app.repositories.audit_trail_repository import AuditTrailRepository
from app.utils.file_storage import save_upload_file
from app.utils.pdf_generator import IAPDFGenerator
from app.schemas.ia_master import IAMasterCreate, EmployeeCreate

class IAMasterService:
    def __init__(self):
        self.ia_repo = IAMasterRepository()
        self.audit_repo = AuditTrailRepository()

    def validate_ia_number(self, db: Session, ia_number: str) -> bool:
        return self.ia_repo.exists_by_reg_number(db, ia_number)

    async def create_ia_entry(
        self, 
        db: Session, 
        ia_data: dict, 
        employees_data: List[dict],
        ia_cert: Optional[UploadFile],
        ia_sig: Optional[UploadFile],
        ia_logo: Optional[UploadFile],
        employee_certs: List[Optional[UploadFile]],
        user_ip: Optional[str] = None,
        user_agent: Optional[str] = None
    ):
        # 1. Check for duplicates
        if self.ia_repo.exists_by_reg_number(db, ia_data['ia_registration_number']):
            raise ValueError(f"IA Registration Number {ia_data['ia_registration_number']} already exists.")

        for emp in employees_data:
            if self.ia_repo.exists_by_reg_number(db, emp['ia_registration_number']):
                raise ValueError(f"Employee IA Registration Number {emp['ia_registration_number']} already exists.")

        # 2. Save IA Files
        nature = ia_data['nature_of_entity']
        if ia_cert:
            ia_data['ia_certificate_path'] = await save_upload_file(ia_cert, nature, "ia_cert")
        if ia_sig:
            ia_data['ia_signature_path'] = await save_upload_file(ia_sig, nature, "ia_sig")
        if ia_logo:
            ia_data['ia_logo_path'] = await save_upload_file(ia_logo, nature, "ia_logo")

        # 3. Create IA Master Record
        db_ia = self.ia_repo.create(db, ia_data)
        
        # 4. Save Employee Records and Files
        for i, emp_data in enumerate(employees_data):
            emp_data['ia_master_id'] = db_ia.id
            if i < len(employee_certs) and employee_certs[i]:
                emp_data['certificate_path'] = await save_upload_file(employee_certs[i], nature, f"emp_cert_{i}")
            self.ia_repo.create_employee(db, emp_data)

        # 5. Log Audit Trail
        changes = f"Created IA Master: {ia_data['name_of_ia']} (Reg No: {ia_data['ia_registration_number']})"
        self.audit_repo.log_event(
            db, "INSERT", "ia_master", str(db_ia.id), 
            changes=changes, user_ip=user_ip, user_agent=user_agent
        )

        return db_ia

    def get_latest_ia(self, db: Session):
        db_ia = self.ia_repo.get_latest(db)
        if db_ia:
            self.audit_repo.log_event(db, "VIEW", "ia_master", str(db_ia.id), f"Viewed IA Master ID: {db_ia.id}")
        return db_ia

    def generate_pdf(self, db: Session, ia_id: uuid.UUID) -> Tuple[bytes, str]:
        db_ia = self.ia_repo.get_by_id(db, ia_id)
        if not db_ia:
            raise ValueError("IA record not found")

        employees = self.ia_repo.get_employees_by_master_id(db, ia_id)
        
        # Convert to dict for generator
        ia_dict = {c.name: getattr(db_ia, c.name) for c in db_ia.__table__.columns}
        emp_list = [{c.name: getattr(emp, c.name) for c in emp.__table__.columns} for emp in employees]
        
        pdf_bytes = IAPDFGenerator.generate_ia_report(ia_dict, emp_list)
        
        filename = f"IA_Master_Entry_{db_ia.ia_registration_number}.pdf"
        
        self.audit_repo.log_event(db, "PDF_EXPORT", "ia_master", str(db_ia.id), f"Exported PDF for IA Master ID: {db_ia.id}")
        
        return pdf_bytes, filename
