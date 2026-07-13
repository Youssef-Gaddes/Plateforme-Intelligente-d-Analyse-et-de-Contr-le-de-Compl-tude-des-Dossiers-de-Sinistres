# models.py
from sqlalchemy import Float, Column, Integer, String, Date, DateTime, ForeignKey, Text, CheckConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import JSONB
from database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(150), unique=True, nullable=False)
    password = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False)  # admin / gestionnaire / lecteur
    created_at = Column(DateTime, server_default=func.now())

    __table_args__ = (
        CheckConstraint("role IN ('admin', 'gestionnaire', 'lecteur')", name="valid_role"),
    )


class Claim(Base):
    __tablename__ = "claims"

    id = Column(Integer, primary_key=True, index=True)
    claim_number = Column(String(50), unique=True, nullable=False)
    insured_name = Column(String(150), nullable=False)
    status = Column(String(30), default="ouvert")
    claim_type = Column(String(20), nullable=False, server_default="auto")   # NEW
    creation_date = Column(Date, server_default=func.current_date())
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    completeness_score = Column(Float, nullable=True)

    documents = relationship("Document", back_populates="claim", cascade="all, delete")
    owner = relationship("User", backref="claims")

    __table_args__ = (
        CheckConstraint("status IN ('ouvert', 'en_cours', 'ferme')", name="valid_status"),
        CheckConstraint("claim_type IN ('auto', 'habitation', 'sante')", name="valid_claim_type"),  # NEW
    )


class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    claim_id = Column(Integer, ForeignKey("claims.id", ondelete="CASCADE"), nullable=False)
    file_name = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    document_type = Column(String(50), nullable=True)
    ocr_text = Column(Text, nullable=True)
    upload_date = Column(DateTime, server_default=func.now())

    # NEW: model's confidence for the classification of this document
    classification_confidence = Column(Float, nullable=True)
    is_manually_reviewed = Column(Integer, server_default='0') # 0 or 1

    claim = relationship("Claim", back_populates="documents")