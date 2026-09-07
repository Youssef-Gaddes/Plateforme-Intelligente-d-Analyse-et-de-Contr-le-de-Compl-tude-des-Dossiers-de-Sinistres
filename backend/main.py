from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session, joinedload
from database import SessionLocal
from models import User, Claim, Document
from schemas import ClaimType, UserCreate, UserOut, UserUpdate, LoginRequest, Token, ClaimCreate, ClaimOut, ClaimStatus, DocumentOut, DocumentUpdate, UserRole
from auth import hash_password, verify_password, create_access_token, get_current_user, require_role
from ocrHelper import extract_text, clean_ocr_text, extract_fields
from typing import List, Optional
import os
import shutil
import mimetypes
from classifier_service import predict_document_type, _classifier
import uuid

app = FastAPI()

# user tied to claim ony ?
# type de claims ?
# autorisation some funcs ?
# pour entrainement, how to get ids ?

UPLOAD_DIR = "uploads"
ALLOWED_EXTENSIONS = {".pdf", ".png", ".jpg"}
MAX_FILE_SIZE = 10 * 1024 * 1024
CONFIDENCE_THRESHOLD = 0.3

REQUIRED_DOCUMENTS = {
    "auto": ["declaration_sinistre", "carte_grise", "permis_conduire", "constat_amiable"],
    "habitation": ["declaration_sinistre", "devis"],
    "sante": ["declaration_sinistre", "facture"],
}

os.makedirs(UPLOAD_DIR, exist_ok=True)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def compute_completeness_score(claim: Claim) -> float:
    required = REQUIRED_DOCUMENTS.get(claim.claim_type, [])
    if not required:
        return 0.0

    valid_types = {
        doc.document_type
        for doc in claim.documents
        if doc.document_type in required
        and (
            (doc.classification_confidence is not None and doc.classification_confidence >= CONFIDENCE_THRESHOLD)
            or doc.is_manually_reviewed == 1
        )
    }
    matched_count = sum(1 for doc_type in required if doc_type in valid_types)
    return round((matched_count / len(required)) * 100.0, 2)


def refresh_claim_completeness(claim: Claim, db: Session):
    fresh_claim = db.query(Claim).options(joinedload(Claim.documents)).filter(Claim.id == claim.id).first()
    if not fresh_claim:
        return claim
    fresh_claim.completeness_score = compute_completeness_score(fresh_claim)
    db.commit()
    db.refresh(fresh_claim)
    return fresh_claim

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

    token = create_access_token({"sub": user.email, "role": user.role, "user_id": user.id})
    return {"access_token": token, "token_type": "bearer"}

@app.get("/users/me")
def read_current_user(current_user: dict = Depends(get_current_user)):
    return current_user

@app.get("/admin-only")
def admin_only_route(current_user: dict = Depends(require_role("admin"))):
    return {"message": f"Welcome admin {current_user['email']}"}

@app.get("/users", response_model=List[UserOut])
def list_users(
    role: Optional[UserRole] = None,
    current_user: dict = Depends(require_role("admin", "gestionnaire")),
    db: Session = Depends(get_db),
):
    query = db.query(User)
    if role is not None:
        query = query.filter(User.role == role.value)
    return query.all()

@app.get("/users/{user_id}", response_model=UserOut)
def get_user(user_id: int, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@app.post("/users", response_model=UserOut)
def create_user(user: UserCreate, current_user: dict = Depends(require_role("admin")), db: Session = Depends(get_db)):
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

@app.put("/users/{user_id}", response_model=UserOut)
def update_user(user_id: int, user: UserUpdate, current_user: dict = Depends(require_role("admin")), db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.id == user_id).first()
    if not existing_user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.name is not None:
        existing_user.name = user.name
    if user.email is not None:
        duplicate = db.query(User).filter(User.email == user.email, User.id != user_id).first()
        if duplicate:
            raise HTTPException(status_code=400, detail="Email already registered")
        existing_user.email = user.email
    if user.password is not None:
        existing_user.password = hash_password(user.password)
    if user.role is not None:
        existing_user.role = user.role
    db.commit()
    db.refresh(existing_user)
    return existing_user

@app.delete("/users/{user_id}")
def delete_user(user_id: int, current_user: dict = Depends(require_role("admin")), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    db.delete(user)
    db.commit()
    return {"detail": "User deleted successfully"}


@app.get("/claims", response_model=List[ClaimOut])
def list_claims(
    status: Optional[ClaimStatus] = None,
    claim_type: Optional[ClaimType] = None,   # NEW
    current_user: dict = Depends(require_role("admin", "gestionnaire", "lecteur")),
    db: Session = Depends(get_db),
):
    query = db.query(Claim)

    if current_user["role"] == "lecteur":
        query = query.filter(Claim.user_id == current_user["id"])

    if status is not None:
        query = query.filter(Claim.status == status.value)
    if claim_type is not None:
        query = query.filter(Claim.claim_type == claim_type.value)

    return query.all()

@app.get("/claims/{claim_id}", response_model=ClaimOut)
def get_claim(claim_id: int, current_user: dict = Depends(require_role("admin","gestionnaire","lecteur")), db: Session = Depends(get_db)):
    claim = db.query(Claim).options(joinedload(Claim.owner)).filter(Claim.id == claim_id).first()
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")

    if current_user["role"] == "lecteur" and claim.user_id != current_user["id"]:
        raise HTTPException(status_code=403, detail="Not authorized to view this claim")

    return claim

@app.get("/documents", response_model=List[DocumentOut])
def list_documents(
    claim_id: Optional[int] = None,
    current_user: dict = Depends(require_role("admin", "gestionnaire", "lecteur")),
    db: Session = Depends(get_db),
):
    query = db.query(Document).options(joinedload(Document.claim))
    if claim_id is not None:
        query = query.filter(Document.claim_id == claim_id)
    if current_user["role"] == "lecteur":
        query = query.join(Document.claim).filter(Claim.user_id == current_user["id"])
    return query.all()

@app.get("/documents/types", response_model=List[str])
def list_document_types(current_user: dict = Depends(require_role("admin", "gestionnaire", "lecteur"))):
    return sorted([str(t) for t in _classifier.classes_])

@app.post("/claims", response_model=ClaimOut)
def create_claim(claim: ClaimCreate, current_user: dict = Depends(require_role("admin","gestionnaire")), db: Session = Depends(get_db)):
    existing = db.query(Claim).filter(Claim.claim_number == claim.claim_number).first()
    if existing:
        raise HTTPException(status_code=400, detail="Claim number already exists")

    owner = db.query(User).filter(User.id == claim.user_id).first()
    if not owner:
        raise HTTPException(status_code=404, detail="Referenced user not found")
    if owner.role != "lecteur":
        raise HTTPException(status_code=400, detail="Claims must be assigned to a user with role 'lecteur'")

    new_claim = Claim(
        claim_number=claim.claim_number,
        insured_name=claim.insured_name,
        status=claim.status,
        claim_type=claim.claim_type,
        user_id=claim.user_id,
    )
    db.add(new_claim)
    db.commit()
    db.refresh(new_claim)
    return refresh_claim_completeness(new_claim, db)

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

    owner = db.query(User).filter(User.id == claim.user_id).first()
    if not owner:
        raise HTTPException(status_code=404, detail="Referenced user not found")
    if owner.role != "lecteur":
        raise HTTPException(status_code=400, detail="Claims must be assigned to a user with role 'lecteur'")

    existing_claim.claim_number = claim.claim_number
    existing_claim.insured_name = claim.insured_name
    existing_claim.status = claim.status
    existing_claim.claim_type = claim.claim_type
    existing_claim.user_id = claim.user_id
    db.commit()
    db.refresh(existing_claim)
    return refresh_claim_completeness(existing_claim, db)


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
    current_user: dict = Depends(require_role("admin", "gestionnaire", "lecteur")),
    db: Session = Depends(get_db),
):
    claim = db.query(Claim).filter(Claim.id == claim_id).first()
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")

    if current_user["role"] == "lecteur" and claim.user_id != current_user["id"]:
        raise HTTPException(status_code=403, detail="Not authorized to upload to this claim")

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

    raw_text = extract_text(file_path, ext)
    clean_text = clean_ocr_text(raw_text)
    document_type, confidence = predict_document_type(clean_text)

    new_doc = Document(
        claim_id=claim_id,
        file_name=file.filename,
        file_path=file_path,
        ocr_text=clean_text,
        document_type=document_type,
        classification_confidence=round(confidence, 4),
    )
    db.add(new_doc)
    db.commit()
    db.refresh(new_doc)
    refresh_claim_completeness(claim, db)
    return new_doc

@app.get("/documents/{doc_id}", response_model=DocumentOut)
def get_document(doc_id: int, current_user: dict = Depends(require_role("admin", "gestionnaire", "lecteur")), db: Session = Depends(get_db)):
    document = db.query(Document).options(joinedload(Document.claim)).filter(Document.id == doc_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    if current_user["role"] == "lecteur" and document.claim.user_id != current_user["id"]:
        raise HTTPException(status_code=403, detail="Not authorized to view this document")
    return document

@app.get("/documents/{doc_id}/file")
def get_document_file(doc_id: int, current_user: dict = Depends(require_role("admin", "gestionnaire", "lecteur")), db: Session = Depends(get_db)):
    document = db.query(Document).options(joinedload(Document.claim)).filter(Document.id == doc_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    if current_user["role"] == "lecteur" and document.claim.user_id != current_user["id"]:
        raise HTTPException(status_code=403, detail="Not authorized to view this document")

    if not os.path.exists(document.file_path):
        raise HTTPException(status_code=404, detail="Stored document file not found")

    mime_type, _ = mimetypes.guess_type(document.file_path)
    return FileResponse(document.file_path, media_type=mime_type or "application/octet-stream", filename=document.file_name)

@app.put("/documents/{doc_id}", response_model=DocumentOut)
def update_document(doc_id: int, doc_data: DocumentUpdate, current_user: dict = Depends(require_role("admin", "gestionnaire")), db: Session = Depends(get_db)):
    document = db.query(Document).filter(Document.id == doc_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    if doc_data.document_type is not None:
        document.document_type = doc_data.document_type
        document.is_manually_reviewed = 1
    if doc_data.ocr_text is not None:
        document.ocr_text = doc_data.ocr_text
    db.commit()
    db.refresh(document)

    claim = db.query(Claim).filter(Claim.id == document.claim_id).first()
    if claim:
        refresh_claim_completeness(claim, db)

    return document

@app.delete("/documents/{doc_id}")
def delete_document(doc_id: int, current_user: dict = Depends(require_role("admin")), db: Session = Depends(get_db)):
    document = db.query(Document).filter(Document.id == doc_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    if os.path.exists(document.file_path):
        os.remove(document.file_path)
    claim = db.query(Claim).filter(Claim.id == document.claim_id).first()
    db.delete(document)
    db.commit()
    if claim:
        refresh_claim_completeness(claim, db)
    return {"detail": "Document deleted successfully"}

@app.post("/documents/{doc_id}/ocr")
def run_ocr(doc_id: int, current_user: dict = Depends(require_role("admin", "gestionnaire")), db: Session = Depends(get_db)):
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    ext = os.path.splitext(doc.file_path)[1].lower()
    raw_text = extract_text(doc.file_path, ext)          
    clean_text = clean_ocr_text(raw_text)                 
    fields = extract_fields(clean_text)                   

    doc.ocr_text = clean_text
    doc.extracted_fields = fields
    doc.processing_status = "done"
    db.commit()

    return {"document_id": doc.id, "ocr_text": clean_text, "extracted_fields": fields}

@app.post("/documents/{doc_id}/classify")
def classify_document_endpoint(
    doc_id: int,
    current_user: dict = Depends(require_role("admin", "gestionnaire")),
    db: Session = Depends(get_db),
):
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    if not doc.ocr_text:
        raise HTTPException(status_code=400, detail="Document has not been OCR'd yet")

    document_type, confidence = predict_document_type(doc.ocr_text)

    doc.document_type = document_type
    doc.classification_confidence = round(confidence, 4) 
    db.commit()

    claim = db.query(Claim).filter(Claim.id == doc.claim_id).first()
    if claim:
        refresh_claim_completeness(claim, db)

    return {
        "document_id": doc.id,
        "document_type": document_type,
        "confidence": round(confidence, 4),
    }