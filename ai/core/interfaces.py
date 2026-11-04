"""
AI Core interfaces and abstractions for Document Screening System.
Ensures modules are decoupled and interchangeable (Tesseract, EasyOCR, S3, Sepolia, etc.)
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class BoundingBox(BaseModel):
    x: int
    y: int
    width: int
    height: int


class OCRField(BaseModel):
    field_name: str
    value: str
    confidence: float  # 0.0 - 100.0
    bounding_box: Optional[BoundingBox] = None


class OCRResult(BaseModel):
    provider: str
    raw_text: str
    fields: Dict[str, OCRField] = Field(default_factory=dict)
    average_confidence: float
    document_type_detected: Optional[str] = None


class SuspiciousRegion(BaseModel):
    region_type: str  # e.g. "photo_area", "text_area", "mrz_area"
    bounding_box: BoundingBox
    anomaly_score: float  # 0.0 - 100.0
    indicator: str
    explanation: str


class TamperingResult(BaseModel):
    provider: str
    tampering_score: float  # 0.0 - 100.0 (higher means more suspicious)
    confidence: float  # 0.0 - 100.0
    detected_indicators: List[str] = Field(default_factory=list)
    suspicious_regions: List[SuspiciousRegion] = Field(default_factory=list)
    metadata_anomalies: List[str] = Field(default_factory=list)
    ela_anomaly_score: float = 0.0
    recommendation: str  # "LOW RISK - STANDARD PROCESSING", "MANUAL INSPECTION RECOMMENDED", etc.
    explanation: str


class FaceVerificationResult(BaseModel):
    provider: str
    similarity_score: float  # 0.0 - 100.0
    confidence: float
    status: str  # "MATCH", "MISMATCH", "UNABLE TO VERIFY"
    document_face_detected: bool
    presented_face_detected: bool
    explanation: str


class RiskFactorDetail(BaseModel):
    factor_name: str
    weight: float
    contribution: float
    description: str


class RiskAssessmentResult(BaseModel):
    overall_score: float  # 0.0 - 100.0
    classification: str  # "LOW", "MEDIUM", "HIGH", "CRITICAL"
    contributing_factors: List[RiskFactorDetail]
    recommendation: str  # "VERIFY PROCEED", "MANUAL REVIEW RECOMMENDED", "SUPERVISOR ESCALATION REQUIRED"
    summary_explanation: str


class OCRProvider(ABC):
    @abstractmethod
    def extract_text(self, image_bytes: bytes, filename: str = "") -> OCRResult:
        pass


class TamperingDetectionProvider(ABC):
    @abstractmethod
    def analyze_tampering(self, image_bytes: bytes, filename: str = "") -> TamperingResult:
        pass


class FaceVerificationProvider(ABC):
    @abstractmethod
    def verify_faces(self, document_image_bytes: bytes, presented_image_bytes: bytes) -> FaceVerificationResult:
        pass


class RiskEngineInterface(ABC):
    @abstractmethod
    def calculate_risk(
        self,
        ocr_result: Optional[OCRResult],
        tampering_result: Optional[TamperingResult],
        face_result: Optional[FaceVerificationResult],
        validation_errors: List[str]
    ) -> RiskAssessmentResult:
        pass
