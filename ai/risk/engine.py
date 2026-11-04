"""
Configurable, Explainable Risk Assessment Engine.
Calculates transparent risk scores and provides detailed itemized contributing factors
based on OCR confidence, format checks, cross-document mismatches, image tampering,
and biometric face verification.
"""
from typing import List, Dict, Optional
from pydantic import BaseModel

from ai.core.interfaces import (
    RiskEngineInterface,
    RiskAssessmentResult,
    RiskFactorDetail,
    OCRResult,
    TamperingResult,
    FaceVerificationResult,
)


class RiskWeightsConfig(BaseModel):
    expired_document: float = 30.0
    document_mismatch: float = 25.0
    possible_tampering: float = 30.0
    face_mismatch: float = 40.0
    low_ocr_confidence: float = 10.0
    invalid_format: float = 20.0
    suspicious_metadata: float = 10.0


class ConfigurableRiskEngine(RiskEngineInterface):
    """
    Production-grade rule-based risk engine with dynamic weighting and full explainability.
    """

    def __init__(self, weights: Optional[RiskWeightsConfig] = None):
        self.weights = weights or RiskWeightsConfig()

    def calculate_risk(
        self,
        ocr_result: Optional[OCRResult],
        tampering_result: Optional[TamperingResult],
        face_result: Optional[FaceVerificationResult],
        validation_errors: List[str],
        custom_penalties: Optional[List[RiskFactorDetail]] = None,
    ) -> RiskAssessmentResult:
        factors: List[RiskFactorDetail] = []
        raw_score = 0.0

        # 1. Check Document Format & Expiry Errors
        has_expired = any("expired" in err.lower() for err in validation_errors)
        if has_expired:
            factors.append(
                RiskFactorDetail(
                    factor_name="Expired Document",
                    weight=self.weights.expired_document,
                    contribution=self.weights.expired_document,
                    description="The identity or travel document validity date has lapsed."
                )
            )
            raw_score += self.weights.expired_document

        # 2. Check Document Mismatches (Cross-document validation)
        has_mismatch = any("mismatch" in err.lower() for err in validation_errors)
        if has_mismatch:
            factors.append(
                RiskFactorDetail(
                    factor_name="Document Mismatch",
                    weight=self.weights.document_mismatch,
                    contribution=self.weights.document_mismatch,
                    description="Discrepancies found between passport, visa, or identity card data fields."
                )
            )
            raw_score += self.weights.document_mismatch

        # Format errors (not mismatch or expiry)
        format_errors = [e for e in validation_errors if "expired" not in e.lower() and "mismatch" not in e.lower()]
        if format_errors:
            factors.append(
                RiskFactorDetail(
                    factor_name="Invalid Format",
                    weight=self.weights.invalid_format,
                    contribution=self.weights.invalid_format,
                    description=f"Field format irregularity: {'; '.join(format_errors[:2])}"
                )
            )
            raw_score += self.weights.invalid_format

        # 3. Check OCR Confidence
        if ocr_result and ocr_result.average_confidence < 85.0:
            factors.append(
                RiskFactorDetail(
                    factor_name="Low OCR Confidence",
                    weight=self.weights.low_ocr_confidence,
                    contribution=self.weights.low_ocr_confidence,
                    description=f"Average OCR confidence is {ocr_result.average_confidence}%, indicating blurry or degraded text."
                )
            )
            raw_score += self.weights.low_ocr_confidence

        # 4. Check Tampering Analysis
        if tampering_result:
            if tampering_result.tampering_score >= 50.0:
                factors.append(
                    RiskFactorDetail(
                        factor_name="Possible Tampering",
                        weight=self.weights.possible_tampering,
                        contribution=self.weights.possible_tampering,
                        description=f"Tampering indicators detected: {', '.join(tampering_result.detected_indicators[:2]) or 'compression anomalies'}."
                    )
                )
                raw_score += self.weights.possible_tampering
            elif tampering_result.tampering_score >= 25.0:
                score_contrib = round(self.weights.possible_tampering * 0.5, 1)
                factors.append(
                    RiskFactorDetail(
                        factor_name="Possible Tampering (Moderate)",
                        weight=self.weights.possible_tampering,
                        contribution=score_contrib,
                        description="Mild compression discrepancy or non-standard image encoding."
                    )
                )
                raw_score += score_contrib

            if tampering_result.metadata_anomalies:
                factors.append(
                    RiskFactorDetail(
                        factor_name="Suspicious Metadata",
                        weight=self.weights.suspicious_metadata,
                        contribution=self.weights.suspicious_metadata,
                        description=tampering_result.metadata_anomalies[0]
                    )
                )
                raw_score += self.weights.suspicious_metadata

        # 5. Check Face Verification
        if face_result:
            if face_result.status == "MISMATCH":
                factors.append(
                    RiskFactorDetail(
                        factor_name="Face Mismatch",
                        weight=self.weights.face_mismatch,
                        contribution=self.weights.face_mismatch,
                        description=f"Biometric similarity ({face_result.similarity_score}%) falls below authentication threshold."
                    )
                )
                raw_score += self.weights.face_mismatch
            elif face_result.status == "UNABLE TO VERIFY":
                # Give a mild verification penalty without treating it as fraud
                factors.append(
                    RiskFactorDetail(
                        factor_name="Face Inconclusive",
                        weight=15.0,
                        contribution=15.0,
                        description="Unable to extract facial landmarks cleanly. Live inspection needed."
                    )
                )
                raw_score += 15.0

        if custom_penalties:
            for p in custom_penalties:
                factors.append(p)
                raw_score += p.contribution

        # Cap score between 0 and 100
        overall_score = min(100.0, max(0.0, round(raw_score, 1)))

        # Classification according to specs
        if overall_score < 25.0:
            classification = "LOW"
            recommendation = "STANDARD CLEARANCE ELIGIBLE"
            summary = "All automated screening checks passed within normal thresholds. Human officer review to confirm."
        elif overall_score < 50.0:
            classification = "MEDIUM"
            recommendation = "ADDITIONAL VERIFICATION REQUIRED"
            summary = "Minor issues detected across document fields or image indicators. Secondary verification recommended."
        elif overall_score < 75.0:
            classification = "HIGH"
            recommendation = "MANUAL REVIEW REQUIRED"
            summary = "Significant anomalies identified in document validation or biometric matching. Mandatory inspection."
        else:
            classification = "CRITICAL"
            recommendation = "SUPERVISOR ESCALATION REQUIRED"
            summary = "Critical multi-factor discrepancies detected. Document must be held for authorized supervisor review."

        return RiskAssessmentResult(
            overall_score=overall_score,
            classification=classification,
            contributing_factors=factors,
            recommendation=recommendation,
            summary_explanation=summary
        )
