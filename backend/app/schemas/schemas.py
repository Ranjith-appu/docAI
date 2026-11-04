"""
Pydantic v2 schemas for request validation and structured API responses.
"""
from datetime import datetime
from typing import List, Dict, Optional, Any
from pydantic import BaseModel, EmailStr, Field, ConfigDict


# --- Auth Schemas ---
class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: "UserOut"


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    role: str = "OFFICER"


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    email: str
    full_name: str
    role: str
    is_active: bool
    created_at: datetime


# --- Document Schemas ---
class DocumentFieldOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    field_name: str
    field_value: str
    confidence: float


class DocumentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    case_id: str
    document_type: str
    file_name: str
    sha256_hash: str
    mime_type: str
    file_size: int
    uploaded_at: datetime
    fields: List[DocumentFieldOut] = []


# --- Case Schemas ---
class CaseCreate(BaseModel):
    applicant_name: str = "JOHN DOE"
    document_type: str = "PASSPORT"


class CaseOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    case_number: str
    applicant_name: str
    document_type: str
    status: str
    created_at: datetime
    updated_at: Optional[datetime] = None


# --- AI Results Schemas ---
class OCRFieldSchema(BaseModel):
    field_name: str
    value: str
    confidence: float


class OCRResponse(BaseModel):
    document_id: str
    provider: str
    raw_text: str
    average_confidence: float
    fields: Dict[str, OCRFieldSchema]


class ValidationRuleSchema(BaseModel):
    rule_name: str
    passed: bool
    message: str
    severity: str


class ValidationResponse(BaseModel):
    case_id: str
    passed: bool
    rule_results: List[ValidationRuleSchema]
    errors: List[str]


class SuspiciousRegionSchema(BaseModel):
    region_type: str
    x: int
    y: int
    width: int
    height: int
    anomaly_score: float
    indicator: str
    explanation: str


class TamperingResponse(BaseModel):
    document_id: str
    tampering_score: float
    confidence: float
    detected_indicators: List[str]
    suspicious_regions: List[SuspiciousRegionSchema]
    metadata_anomalies: List[str]
    recommendation: str
    explanation: str


class FaceResponse(BaseModel):
    case_id: str
    similarity_score: float
    confidence: float
    status: str
    explanation: str


class RiskFactorSchema(BaseModel):
    factor_name: str
    weight: float
    contribution: float
    description: str


class RiskResponse(BaseModel):
    case_id: str
    overall_score: float
    classification: str
    contributing_factors: List[RiskFactorSchema]
    recommendation: str
    summary_explanation: str


# --- Blockchain Schemas ---
class BlockchainRegisterRequest(BaseModel):
    pass


class BlockchainRecordOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    case_id: str
    network: str
    contract_address: str
    tx_hash: str
    block_number: Optional[int]
    case_hash: str
    document_hash: str
    verification_hash: str
    status: str
    explorer_url: Optional[str] = None
    created_at: datetime


class BlockchainVerifyRequest(BaseModel):
    case_id: Optional[str] = None
    case_number: Optional[str] = None
    document_hash: Optional[str] = None


class BlockchainVerifyResponse(BaseModel):
    matched: bool
    status: str  # "MATCH", "DOES NOT MATCH", "RECORD NOT FOUND"
    case_number: str
    current_document_hash: str
    blockchain_document_hash: str
    blockchain_case_hash: str
    block_timestamp: Optional[str] = None
    risk_score: Optional[int] = None
    network: str
    contract_address: str
    explorer_url: Optional[str] = None
    details: str


# --- Officer Review Schemas ---
class OfficerReviewRequest(BaseModel):
    decision: str  # "VERIFIED", "SUSPICIOUS", "REJECTED", "SUPERVISOR_REVIEW"
    notes: Optional[str] = None


class OfficerReviewOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    case_id: str
    officer_id: str
    officer_name: Optional[str] = None
    decision: str
    notes: Optional[str]
    reviewed_at: datetime


# --- Audit Log Schemas ---
class AuditLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    case_id: Optional[str]
    user_id: Optional[str]
    action: str
    prev_hash: str
    entry_hash: str
    timestamp: datetime
    details: Dict[str, Any]


# --- Full Case Dossier Out ---
class CaseDetailOut(BaseModel):
    case: CaseOut
    documents: List[DocumentOut]
    ocr_results: List[OCRResponse] = []
    validation: Optional[ValidationResponse] = None
    tampering_results: List[TamperingResponse] = []
    face_verification: Optional[FaceResponse] = None
    risk_assessment: Optional[RiskResponse] = None
    blockchain_record: Optional[BlockchainRecordOut] = None
    officer_review: Optional[OfficerReviewOut] = None


# --- Analytics Schemas ---
class AnalyticsOverviewOut(BaseModel):
    total_screenings: int
    verified_count: int
    suspicious_count: int
    high_risk_count: int
    manual_reviews_count: int
    average_processing_seconds: float
    tampering_detected_count: int
    face_mismatch_count: int
    blockchain_registrations_count: int
    risk_distribution: Dict[str, int]
    document_type_distribution: Dict[str, int]
    daily_trend: List[Dict[str, Any]]
