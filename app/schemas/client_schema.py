from typing import Optional
from pydantic import BaseModel, ConfigDict, EmailStr, field_validator, model_validator
import uuid
from datetime import datetime, date

class ClientLoginRequest(BaseModel):
    email: EmailStr
    password: str
    force: Optional[bool] = False

class ClientTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

class NomineeSchema(BaseModel):
    name: str
    relationship: str
    dob: date
    percentage: float
    guardian_name: Optional[str] = None

    @field_validator("name", "relationship", "guardian_name")
    @classmethod
    def validate_nominee_text(cls, v: Optional[str]) -> Optional[str]:
        if v is None or v == "":
            return v
        import re
        if not re.match(r"^[a-zA-Z\s]+$", v):
            raise ValueError("Nominee text fields must contain only alphabetic characters and spaces")
        return v

    @field_validator("dob")
    @classmethod
    def validate_nominee_dob(cls, v: date) -> date:
        if v > date.today():
            raise ValueError("Nominee Date of Birth cannot be in the future")
        return v

class ClientBase(BaseModel):
    email: EmailStr
    client_name: str
    date_of_birth: date
    pan_number: str
    phone_number: str
    address: str
    occupation: str
    gender: str
    marital_status: str
    nationality: str
    residential_status: str
    tax_residency: str
    pep_status: str
    father_name: str
    mother_name: str
    spouse_name: Optional[str] = None
    spouse_dob: Optional[date] = None
    aadhar_number: Optional[str] = None
    passport_number: Optional[str] = None
    
    annual_income: float
    net_worth: float
    income_source: str
    fatca_compliance: str
    existing_portfolio_value: Optional[float] = 0.0
    existing_portfolio_composition: Optional[str] = None
    
    bank_account_number: str
    bank_name: str
    bank_branch: str
    ifsc_code: str
    demat_account_number: Optional[str] = None
    trading_account_number: Optional[str] = None
    
    risk_profile: str
    investment_experience: str
    investment_objectives: str
    investment_horizon: str
    liquidity_needs: str
    
    advisor_name: str
    advisor_registration_number: str
    client_date: Optional[date] = None
    nominee_name: Optional[str] = None
    nominee_relationship: Optional[str] = None
    nominees: list[NomineeSchema] = []
    previous_advisor_name: Optional[str] = None
    referral_source: Optional[str] = None
    declaration_signed: bool = False
    agreement_date: Optional[date] = None
    assigned_employee_id: Optional[uuid.UUID] = None
    
    # KYC & IPV Details
    kyc_verified: bool = False
    ckyc_number: Optional[str] = None
    ipv_done_by_id: Optional[uuid.UUID] = None
    ipv_date: Optional[date] = None

    @field_validator("client_date", "agreement_date", "ipv_date")
    @classmethod
    def validate_dates_not_in_future(cls, v: Optional[date]) -> Optional[date]:
        if v and v > date.today():
            raise ValueError("Date cannot be in the future")
        return v

    @field_validator("phone_number")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        if not v.isdigit() or len(v) != 10:
            raise ValueError("Phone number must be exactly 10 digits")
        return v

    @field_validator("bank_account_number")
    @classmethod
    def validate_bank_account(cls, v: str) -> str:
        if not v.isdigit() or not (9 <= len(v) <= 18):
            raise ValueError("Bank account number must be between 9 and 18 digits and contain only numbers")
        return v

    @field_validator("bank_name", "bank_branch")
    @classmethod
    def validate_alphabets_and_spaces(cls, v: str) -> str:
        import re
        if not re.match(r"^[a-zA-Z\s]+$", v):
            raise ValueError("Must contain only alphabetic characters and spaces")
        return v

    @field_validator("ifsc_code")
    @classmethod
    def validate_ifsc(cls, v: str) -> str:
        import re
        val = v.upper().strip()
        if not re.match(r"^[A-Z]{4}0[A-Z0-9]{6}$", val):
            raise ValueError("Invalid IFSC code format (e.g. HDFC0001234, 5th character must be 0)")
        return val

    @field_validator("date_of_birth")
    @classmethod
    def validate_age(cls, v: date) -> date:
        today = date.today()
        age = today.year - v.year - ((today.month, today.day) < (v.month, v.day))
        if age < 18:
            raise ValueError("Age must be at least 18 years")
        return v

    @field_validator("nominees")
    @classmethod
    def validate_nominees_list(cls, v: list[NomineeSchema]) -> list[NomineeSchema]:
        if not v or len(v) < 1:
            raise ValueError("At least 1 nominee is required")
        if len(v) > 3:
            raise ValueError("Maximum 3 nominees are allowed")
        total_pct = round(sum(nom.percentage for nom in v), 2)
        if total_pct != 100.0:
            raise ValueError(f"Total nominee percentage must sum up to exactly 100% (currently {total_pct}%)")
        for idx, nom in enumerate(v, 1):
            today = date.today()
            age = today.year - nom.dob.year - ((today.month, today.day) < (nom.dob.month, nom.dob.day))
            if age < 18 and not (nom.guardian_name and nom.guardian_name.strip()):
                raise ValueError(f"Guardian Name is required for Nominee #{idx} as they are a minor under 18 years old")
        return v

    @model_validator(mode='after')
    def validate_identification(self) -> 'ClientBase':
        if self.residential_status == "Resident Individual":
            if not self.aadhar_number:
                raise ValueError("Aadhar number is required for Resident Individual")
            if not self.aadhar_number.isdigit() or len(self.aadhar_number) != 12:
                raise ValueError("Aadhar number must be exactly 12 digits")
        else:
            if not self.passport_number:
                raise ValueError("Passport number is required for non-resident status")
        return self

class ClientCreate(ClientBase):
    password: str
    client_signature_path: Optional[str] = None
    advisor_signature_path: Optional[str] = None

class ClientUpdate(BaseModel):
    # Personal info
    email: Optional[EmailStr] = None
    client_name: Optional[str] = None
    date_of_birth: Optional[date] = None
    pan_number: Optional[str] = None
    phone_number: Optional[str] = None
    address: Optional[str] = None
    occupation: Optional[str] = None
    gender: Optional[str] = None
    marital_status: Optional[str] = None
    nationality: Optional[str] = None
    residential_status: Optional[str] = None
    tax_residency: Optional[str] = None
    pep_status: Optional[str] = None
    father_name: Optional[str] = None
    mother_name: Optional[str] = None
    spouse_name: Optional[str] = None
    spouse_dob: Optional[date] = None
    aadhar_number: Optional[str] = None
    passport_number: Optional[str] = None
    
    # Financial info
    annual_income: Optional[float] = None
    net_worth: Optional[float] = None
    income_source: Optional[str] = None
    fatca_compliance: Optional[str] = None
    existing_portfolio_value: Optional[float] = None
    existing_portfolio_composition: Optional[str] = None
    
    # Banking info
    bank_account_number: Optional[str] = None
    bank_name: Optional[str] = None
    bank_branch: Optional[str] = None
    ifsc_code: Optional[str] = None
    demat_account_number: Optional[str] = None
    trading_account_number: Optional[str] = None
    
    # Investment info
    risk_profile: Optional[str] = None
    investment_experience: Optional[str] = None
    investment_objectives: Optional[str] = None
    investment_horizon: Optional[str] = None
    liquidity_needs: Optional[str] = None
    
    # Metadata & Nominee
    advisor_name: Optional[str] = None
    advisor_registration_number: Optional[str] = None
    client_date: Optional[date] = None
    nominee_name: Optional[str] = None
    nominee_relationship: Optional[str] = None
    nominees: Optional[list[NomineeSchema]] = None
    previous_advisor_name: Optional[str] = None
    referral_source: Optional[str] = None
    declaration_signed: Optional[bool] = None
    agreement_date: Optional[date] = None
    is_active: Optional[bool] = None
    assigned_employee_id: Optional[uuid.UUID] = None

    # KYC & IPV Details
    kyc_verified: Optional[bool] = None
    ckyc_number: Optional[str] = None
    ipv_done_by_id: Optional[uuid.UUID] = None
    ipv_date: Optional[date] = None
    
    # Audit reference
    rectification_serial_no: Optional[str] = None

    @field_validator("client_date", "agreement_date", "ipv_date")
    @classmethod
    def validate_dates_not_in_future(cls, v: Optional[date]) -> Optional[date]:
        if v and v > date.today():
            raise ValueError("Date cannot be in the future")
        return v

    @field_validator("nominees")
    @classmethod
    def validate_nominees_list(cls, v: Optional[list[NomineeSchema]]) -> Optional[list[NomineeSchema]]:
        if v is not None:
            if len(v) < 1:
                raise ValueError("At least 1 nominee is required")
            if len(v) > 3:
                raise ValueError("Maximum 3 nominees are allowed")
            total_pct = round(sum(nom.percentage for nom in v), 2)
            if total_pct != 100.0:
                raise ValueError(f"Total nominee percentage must sum up to exactly 100% (currently {total_pct}%)")
            for idx, nom in enumerate(v, 1):
                today = date.today()
                age = today.year - nom.dob.year - ((today.month, today.day) < (nom.dob.month, nom.dob.day))
                if age < 18 and not (nom.guardian_name and nom.guardian_name.strip()):
                    raise ValueError(f"Guardian Name is required for Nominee #{idx} as they are a minor under 18 years old")
        return v

class ClientDocumentResponse(BaseModel):
    id: uuid.UUID
    document_type: str
    file_path: str
    uploaded_at: datetime

    model_config = ConfigDict(from_attributes=True)

class ClientResponse(ClientBase):
    id: uuid.UUID
    client_code: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
    assigned_employee_id: Optional[uuid.UUID] = None
    
    client_signature_path: Optional[str] = None
    advisor_signature_path: Optional[str] = None
    
    # KYC & IPV Details
    kyc_verified: bool
    ckyc_number: Optional[str] = None
    ipv_done_by_id: Optional[uuid.UUID] = None
    ipv_date: Optional[date] = None

    aadhar_number: Optional[str] = None
    passport_number: Optional[str] = None
    
    documents: list[ClientDocumentResponse] = []

    model_config = ConfigDict(from_attributes=True)
