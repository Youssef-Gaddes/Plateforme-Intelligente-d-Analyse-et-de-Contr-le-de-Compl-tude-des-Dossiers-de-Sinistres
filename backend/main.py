from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from database import SessionLocal
from models import User, Claim, Document
from schemas import UserCreate, UserOut, LoginRequest, Token, ClaimCreate, ClaimOut, ClaimStatus, DocumentOut
from auth import hash_password, verify_password, create_access_token, get_current_user, require_role
from ocrHelper import extract_text, clean_ocr_text, extract_fields
from typing import List, Optional
import os
import shutil
import uuid

app = FastAPI()

# user tied to claim ony ?
# type de claims ?
# autorisation some funcs ?
# pour entrainement, how to get ids ?

UPLOAD_DIR = "uploads"
ALLOWED_EXTENSIONS = {".pdf", ".png", ".jpg"}
MAX_FILE_SIZE = 10 * 1024 * 1024

os.makedirs(UPLOAD_DIR, exist_ok=True)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"status": "ok"}



@app.post("/auth/register", response_model=UserOut)
def register(user: UserCreate, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == user.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    new_user = User(
        name=user.name,
        email=user.email,
        password=hash_password(user.password),
        role=user.role,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@app.post("/auth/login", response_model=Token)
def login(credentials: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == credentials.email).first()
    if not user or not verify_password(credentials.password, user.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token({"sub": user.email, "role": user.role})
    return {"access_token": token, "token_type": "bearer"}

@app.get("/users/me")
def read_current_user(current_user: dict = Depends(get_current_user)):
    return current_user

@app.get("/admin-only")
def admin_only_route(current_user: dict = Depends(require_role("admin"))):
    return {"message": f"Welcome admin {current_user['email']}"}

@app.get("/users", response_model=List[UserOut])
def list_users(current_user: dict = Depends(require_role("admin")), db: Session = Depends(get_db)):
    return db.query(User).all()

@app.get("/users/{user_id}", response_model=UserOut)
def get_user(user_id: int, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@app.get("/claims", response_model=List[ClaimOut])
def list_claims(
    status: Optional[ClaimStatus] = None,
    current_user: dict = Depends(require_role("admin", "gestionnaire", "lecteur")),
    db: Session = Depends(get_db),
):
    query = db.query(Claim)
    if status != None:
        query = query.filter(Claim.status == status.value)
    return query.all()

@app.get("/claims/{claim_id}", response_model=ClaimOut)
def get_claim(claim_id: int, current_user: dict = Depends(require_role("admin","gestionnaire")), db: Session = Depends(get_db)):
    claim = db.query(Claim).filter(Claim.id == claim_id).first()
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")
    return claim

@app.post("/claims", response_model=ClaimOut)
def create_claim(claim: ClaimCreate, current_user: dict = Depends(require_role("admin","gestionnaire")), db: Session = Depends(get_db)):
    existing = db.query(Claim).filter(Claim.claim_number == claim.claim_number).first()
    if existing:
        raise HTTPException(status_code=400, detail="Claim number already exists")
    new_claim = Claim(
        claim_number=claim.claim_number,
        insured_name=claim.insured_name,
        status=claim.status,
    )
    db.add(new_claim)
    db.commit()
    db.refresh(new_claim)
    return new_claim

@app.put("/claims/{claim_id}", response_model=ClaimOut)
def update_claim(claim_id: int, claim: ClaimCreate, current_user: dict = Depends(require_role("admin","gestionnaire")), db: Session = Depends(get_db)):
    existing_claim = db.query(Claim).filter(Claim.id == claim_id).first()
    if not existing_claim:
        raise HTTPException(status_code=404, detail="Claim not found")
    
    # Check for unique claim_number if it's being updated
    if existing_claim.claim_number != claim.claim_number:
        duplicate_claim = db.query(Claim).filter(Claim.claim_number == claim.claim_number).first()
        if duplicate_claim:
            raise HTTPException(status_code=400, detail="Claim number already exists")

    existing_claim.claim_number = claim.claim_number
    existing_claim.insured_name = claim.insured_name
    existing_claim.status = claim.status
    db.commit()
    db.refresh(existing_claim)
    return existing_claim

@app.delete("/claims/{claim_id}")
def delete_claim(claim_id: int, current_user: dict = Depends(require_role("admin")), db: Session = Depends(get_db)):
    claim = db.query(Claim).filter(Claim.id == claim_id).first()
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")
    db.delete(claim)
    db.commit()
    return {"detail": "Claim deleted successfully"}

@app.post("/documents/upload", response_model=DocumentOut)
def upload_document(
    claim_id: int = Form(...),
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Validate claim exists
    claim = db.query(Claim).filter(Claim.id == claim_id).first()
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")

    # Validate extension
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {ext}")

    # Validate size
    file.file.seek(0, os.SEEK_END)
    size = file.file.tell()
    file.file.seek(0)
    if size > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File too large (max 10MB)")

    # Save to disk with a unique name to avoid collisions
    unique_name = f"{uuid.uuid4()}{ext}"
    file_path = os.path.join(UPLOAD_DIR, unique_name)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Save record in DB
    new_doc = Document(
        claim_id=claim_id,
        file_name=file.filename,
        file_path=file_path,
    )
    db.add(new_doc)
    db.commit()
    db.refresh(new_doc)
    return new_doc

@app.post("/documents/{doc_id}/ocr")
def run_ocr(doc_id: int, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    ext = os.path.splitext(doc.file_path)[1].lower()
    raw_text = extract_text(doc.file_path, ext)          
    clean_text = clean_ocr_text(raw_text)                 
    fields = extract_fields(clean_text)                   

    doc.ocr_text = raw_text
    doc.extracted_fields = fields
    doc.processing_status = "done"
    db.commit()

    return {"document_id": doc.id, "ocr_text": raw_text, "extracted_fields": fields}