"""
SQLAlchemy ORM Data Models for Document Screening System.
Implements normalized, flexible relational structure with UUID primary keys and JSON details.
"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Column, String, Boolean, DateTime, Float, Integer, Text, ForeignKey, Index
)
from sqlalchemy.orm import relationship
from backend.app.core.database import Base


def generate_uuid() -> str:
    return str(uuid.uuid4())


class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    role = Column(String(50), default="OFFICER", nullable=False)  # ADMIN, OFFICER, SUPERVISOR
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    screening_cases = relationship("ScreeningCase", back_populates="officer")
    officer_reviews = relationship("OfficerReview", back_populates="officer")


class ScreeningCase(Base):
    __tablename__ = "screening_cases"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    case_number = Column(String(50), unique=True, index=True, nullable=False)  # e.g. SCR-2026-000101
    applicant_name = Column(String(255), nullable=False, default="ANONYMIZED_APPLICANT")
    document_type = Column(String(50), nullable=False, default="PASSPORT")
    status = Column(String(50), default="CREATED", nullable=False, index=True)
    # CREATED, PROCESSING, REVIEW_REQUIRED, VERIFIED, SUSPICIOUS, CLOSED
    officer_id = Column(String(36), ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    officer = relationship("User", back_populates="screening_cases")
    documents = relationship("Document", back_populates="case", cascade="all, delete-orphan")
    validation_results = relationship("ValidationResult", back_populates="case", cascade="all, delete-orphan")
    face_verification = relationship("FaceVerificationResultModel", back_populates="case", uselist=False, cascade="all, delete-orphan")
    risk_assessment = relationship("RiskAssessment", back_populates="case", uselist=False, cascade="all, delete-orphan")
    blockchain_record = relationship("BlockchainRecord", back_populates="case", uselist=False, cascade="all, delete-orphan")
    officer_review = relationship("OfficerReview", back_populates="case", uselist=False, cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="case", cascade="all, delete-orphan")


class Document(Base):
    __tablename__ = "documents"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    case_id = Column(String(36), ForeignKey("screening_cases.id"), nullable=False, index=True)
    document_type = Column(String(50), nullable=False)  # PASSPORT, VISA, NATIONAL_ID, PRESENTED_FACE
    file_name = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    sha256_hash = Column(String(64), nullable=False, index=True)
    mime_type = Column(String(100), nullable=False)
    file_size = Column(Integer, nullable=False)
    uploaded_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    case = relationship("ScreeningCase", back_populates="documents")
    fields = relationship("DocumentField", back_populates="document", cascade="all, delete-orphan")
    ocr_result = relationship("OCRResultModel", back_populates="document", uselist=False, cascade="all, delete-orphan")
    tampering_result = relationship("TamperingResultModel", back_populates="document", uselist=False, cascade="all, delete-orphan")


class DocumentField(Base):
    """
    Flexible schema: Allows adding new document types without database migrations.
    """
    __tablename__ = "document_fields"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    document_id = Column(String(36), ForeignKey("documents.id"), nullable=False, index=True)
    field_name = Column(String(100), nullable=False, index=True)
    field_value = Column(Text, nullable=False)
    confidence = Column(Float, default=100.0)

    document = relationship("Document", back_populates="fields")


class OCRResultModel(Base):
    __tablename__ = "ocr_results"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    document_id = Column(String(36), ForeignKey("documents.id"), nullable=False, unique=True)
    provider = Column(String(50), nullable=False)
    raw_text = Column(Text, nullable=True)
    average_confidence = Column(Float, default=0.0)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    document = relationship("Document", back_populates="ocr_result")


class ValidationResult(Base):
    __tablename__ = "validation_results"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    case_id = Column(String(36), ForeignKey("screening_cases.id"), nullable=False, index=True)
    passed = Column(Boolean, default=True)
    rule_details_json = Column(Text, nullable=False, default="[]")
    errors_json = Column(Text, nullable=False, default="[]")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    case = relationship("ScreeningCase", back_populates="validation_results")


class TamperingResultModel(Base):
    __tablename__ = "tampering_results"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    document_id = Column(String(36), ForeignKey("documents.id"), nullable=False, unique=True)
    tampering_score = Column(Float, nullable=False)  # 0.0 - 100.0
    confidence = Column(Float, default=85.0)
    indicators_json = Column(Text, default="[]")
    regions_json = Column(Text, default="[]")
    metadata_anomalies_json = Column(Text, default="[]")
    recommendation = Column(String(255), nullable=False)
    explanation = Column(Text, default="")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    document = relationship("Document", back_populates="tampering_result")


class FaceVerificationResultModel(Base):
    __tablename__ = "face_verification_results"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    case_id = Column(String(36), ForeignKey("screening_cases.id"), nullable=False, unique=True)
    similarity_score = Column(Float, nullable=False)
    status = Column(String(50), nullable=False)  # MATCH, MISMATCH, UNABLE TO VERIFY
    confidence = Column(Float, default=90.0)
    explanation = Column(Text, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    case = relationship("ScreeningCase", back_populates="face_verification")


class RiskAssessment(Base):
    __tablename__ = "risk_assessments"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    case_id = Column(String(36), ForeignKey("screening_cases.id"), nullable=False, unique=True)
    overall_score = Column(Float, nullable=False)
    classification = Column(String(50), nullable=False)  # LOW, MEDIUM, HIGH, CRITICAL
    factors_json = Column(Text, nullable=False, default="[]")
    recommendation = Column(String(255), nullable=False)
    summary_explanation = Column(Text, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    case = relationship("ScreeningCase", back_populates="risk_assessment")


class BlockchainRecord(Base):
    __tablename__ = "blockchain_records"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    case_id = Column(String(36), ForeignKey("screening_cases.id"), nullable=False, unique=True)
    network = Column(String(50), default="Ethereum Sepolia")
    contract_address = Column(String(66), nullable=False)
    tx_hash = Column(String(66), nullable=False, index=True)
    block_number = Column(Integer, nullable=True)
    case_hash = Column(String(66), nullable=False, index=True)
    document_hash = Column(String(66), nullable=False, index=True)
    verification_hash = Column(String(66), nullable=False)
    status = Column(String(50), default="CONFIRMED")  # PENDING, CONFIRMED, FAILED
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    case = relationship("ScreeningCase", back_populates="blockchain_record")


class OfficerReview(Base):
    __tablename__ = "officer_reviews"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    case_id = Column(String(36), ForeignKey("screening_cases.id"), nullable=False, unique=True)
    officer_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    decision = Column(String(50), nullable=False)  # VERIFIED, SUSPICIOUS, REJECTED, SUPERVISOR_REVIEW
    notes = Column(Text, nullable=True)
    reviewed_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    case = relationship("ScreeningCase", back_populates="officer_review")
    officer = relationship("User", back_populates="officer_reviews")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    seq = Column(Integer, default=1, index=True)
    case_id = Column(String(36), ForeignKey("screening_cases.id"), nullable=True, index=True)
    user_id = Column(String(36), nullable=True)
    action = Column(String(100), nullable=False, index=True)
    prev_hash = Column(String(64), nullable=False)
    entry_hash = Column(String(64), nullable=False, unique=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    timestamp_str = Column(String(50), nullable=False, default="")
    details_json = Column(Text, default="{}")

    case = relationship("ScreeningCase", back_populates="audit_logs")
