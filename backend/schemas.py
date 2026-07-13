from datetime import date
from typing import Optional

from pydantic import BaseModel, EmailStr
from enum import Enum

class UserRole(str, Enum):
    admin = "admin"
    gestionnaire = "gestionnaire"
    lecteur = "lecteur"

class ClaimStatus(str, Enum):
    ouvert = "ouvert"
    en_cours = "en_cours"
    ferme = "ferme"

class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str
    role: UserRole  # "admin" / "gestionnaire" / "lecteur"

class UserOut(BaseModel):
    id: int
    name: str
    email: str
    role: UserRole

    class Config:
        from_attributes = True

class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    role: Optional[UserRole] = None

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class ClaimType(str, Enum):
    auto = "auto"
    habitation = "habitation"
    sante = "sante"

class ClaimCreate(BaseModel):
    claim_number: str
    insured_name: str
    status: ClaimStatus = ClaimStatus.ouvert
    claim_type: ClaimType = ClaimType.auto   # NEW
    user_id: int

class ClaimOut(BaseModel):
    id: int
    claim_number: str
    insured_name: str
    status: ClaimStatus
    claim_type: ClaimType   # NEW
    creation_date: date
    user_id: Optional[int] = None
    completeness_score: Optional[float] = None

    class Config:
        from_attributes = True

class DocumentOut(BaseModel):
    id: int
    claim_id: int
    file_name: str
    document_type: Optional[str] = None
    classification_confidence: Optional[float] = None
    is_manually_reviewed: Optional[int] = None
    ocr_text: Optional[str] = None

    class Config:
        from_attributes = True

class DocumentUpdate(BaseModel):
    document_type: Optional[str] = None
    ocr_text: Optional[str] = None