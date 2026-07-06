from pydantic import BaseModel, EmailStr
from enum import Enum

class UserRole(str, Enum):
    admin = "admin"
    gestionnaire = "gestionnaire"
    lecteur = "lecteur"


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
    status: str = "ouvert"  # Default status

class ClaimOut(BaseModel):
    id: int
    claim_number: str
    insured_name: str
    status: str

    class Config:
        from_attributes = True