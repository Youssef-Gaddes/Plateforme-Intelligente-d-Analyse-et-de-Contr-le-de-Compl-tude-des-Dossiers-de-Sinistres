# models.py
from sqlalchemy import Column, Integer, String, Date, DateTime, ForeignKey, Text, CheckConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
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
    creation_date = Column(DateTime, server_default=func.now())

    documents = relationship("Document", back_populates="claim", cascade="all, delete")


class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    claim_id = Column(Integer, ForeignKey("claims.id", ondelete="CASCADE"), nullable=False)
    file_name = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    document_type = Column(String(50), nullable=True)
    ocr_text = Column(Text, nullable=True)
    upload_date = Column(DateTime, server_default=func.now())

    claim = relationship("Claim", back_populates="documents")