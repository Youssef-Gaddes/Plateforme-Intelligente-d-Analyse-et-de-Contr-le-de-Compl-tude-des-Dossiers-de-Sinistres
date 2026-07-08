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

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class ClaimCreate(BaseModel):
    claim_number: str
    insured_name: str
    status: ClaimStatus = ClaimStatus.ouvert  # Default status

class ClaimOut(BaseModel):
    id: int
    claim_number: str
    insured_name: str
    status: ClaimStatus

    class Config:
        from_attributes = True

class DocumentOut(BaseModel):
    id: int
    claim_id: int
    file_name: str
    document_type: str | None = None

    class Config:
        from_attributes = True