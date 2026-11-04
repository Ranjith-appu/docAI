"""
Screening Orchestration Service.
Coordinates the end-to-end multi-step screening pipeline:
Create Case -> Upload Document -> OCR -> Validation -> Tampering -> Face Verification -> Risk Engine -> Blockchain Registration.
"""
import json
import hashlib
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from backend.app.models.models import (
    ScreeningCase, Document, DocumentField, OCRResultModel,
    ValidationResult, TamperingResultModel, FaceVerificationResultModel,
    RiskAssessment, BlockchainRecord, OfficerReview
)
from backend.app.services.audit_service import AuditService
from backend.app.services.blockchain_service import get_blockchain_provider
from ai.ocr.provider import get_ocr_provider
from ai.tampering.analyzer import ComputerVisionTamperingAnalyzer
from ai.face.verifier import OpenCVFaceVerifier
from ai.risk.engine import ConfigurableRiskEngine, RiskWeightsConfig
from ai.document.validator import DocumentValidator


class ScreeningService:
    @staticmethod
    def create_case(
        db: Session,
        applicant_name: str,
        document_type: str,
        officer_id: Optional[str] = None
    ) -> ScreeningCase:
        # Generate sequence case number
        count = db.query(ScreeningCase).count() + 101
        year = datetime.now(timezone.utc).year
        case_number = f"SCR-{year}-{count:06d}"

        new_case = ScreeningCase(
            case_number=case_number,
            applicant_name=applicant_name,
            document_type=document_type,
            status="CREATED",
            officer_id=officer_id,
        )
        db.add(new_case)
        db.commit()
        db.refresh(new_case)

        # Audit log
        AuditService.record_action(
            db,
            action="CREATE_CASE",
            case_id=new_case.id,
            user_id=officer_id,
            details={"case_number": case_number, "applicant": applicant_name, "type": document_type}
        )

        return new_case

    @staticmethod
    def process_ocr(db: Session, document_id: str, officer_id: Optional[str] = None) -> OCRResultModel:
        doc = db.query(Document).filter(Document.id == document_id).first()
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")

        with open(doc.file_path, "rb") as f:
            content = f.read()

        ocr_provider = get_ocr_provider()
        ocr_res = ocr_provider.extract_text(content, filename=doc.file_name)

        # Remove old OCR result if exists
        old_ocr = db.query(OCRResultModel).filter(OCRResultModel.document_id == doc.id).first()
        if old_ocr:
            db.delete(old_ocr)

        # Clear old fields
        db.query(DocumentField).filter(DocumentField.document_id == doc.id).delete()

        ocr_model = OCRResultModel(
            document_id=doc.id,
            provider=ocr_res.provider,
            raw_text=ocr_res.raw_text,
            average_confidence=ocr_res.average_confidence
        )
        db.add(ocr_model)

        # Persist extracted fields
        for field_key, field_obj in ocr_res.fields.items():
            df = DocumentField(
                document_id=doc.id,
                field_name=field_key,
                field_value=field_obj.value,
                confidence=field_obj.confidence
            )
            db.add(df)

        db.commit()
        db.refresh(ocr_model)

        AuditService.record_action(
            db,
            action="OCR_COMPLETED",
            case_id=doc.case_id,
            user_id=officer_id,
            details={"document_id": doc.id, "avg_confidence": ocr_res.average_confidence, "field_count": len(ocr_res.fields)}
        )

        return ocr_model

    @staticmethod
    def process_tampering(db: Session, document_id: str, officer_id: Optional[str] = None) -> TamperingResultModel:
        doc = db.query(Document).filter(Document.id == document_id).first()
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")

        with open(doc.file_path, "rb") as f:
            content = f.read()

        analyzer = ComputerVisionTamperingAnalyzer()
        tamp_res = analyzer.analyze_tampering(content, filename=doc.file_name)

        # Remove old result
        old_tamp = db.query(TamperingResultModel).filter(TamperingResultModel.document_id == doc.id).first()
        if old_tamp:
            db.delete(old_tamp)

        regions_serialized = [
            {
                "region_type": r.region_type,
                "x": r.bounding_box.x,
                "y": r.bounding_box.y,
                "width": r.bounding_box.width,
                "height": r.bounding_box.height,
                "anomaly_score": r.anomaly_score,
                "indicator": r.indicator,
                "explanation": r.explanation
            }
            for r in tamp_res.suspicious_regions
        ]

        tamp_model = TamperingResultModel(
            document_id=doc.id,
            tampering_score=tamp_res.tampering_score,
            confidence=tamp_res.confidence,
            indicators_json=json.dumps(tamp_res.detected_indicators),
            regions_json=json.dumps(regions_serialized),
            metadata_anomalies_json=json.dumps(tamp_res.metadata_anomalies),
            recommendation=tamp_res.recommendation,
            explanation=tamp_res.explanation
        )
        db.add(tamp_model)
        db.commit()
        db.refresh(tamp_model)

        AuditService.record_action(
            db,
            action="TAMPERING_ANALYSIS_COMPLETED",
            case_id=doc.case_id,
            user_id=officer_id,
            details={"document_id": doc.id, "tampering_score": tamp_res.tampering_score, "recommendation": tamp_res.recommendation}
        )

        return tamp_model

    @staticmethod
    def process_face_verification(db: Session, case_id: str, officer_id: Optional[str] = None) -> FaceVerificationResultModel:
        case = db.query(ScreeningCase).filter(ScreeningCase.id == case_id).first()
        if not case:
            raise HTTPException(status_code=404, detail="Case not found")

        # Find document image and presented face image
        doc_img = next((d for d in case.documents if d.document_type in ("PASSPORT", "NATIONAL_ID", "DRIVING_LICENSE")), None)
        pres_img = next((d for d in case.documents if d.document_type == "PRESENTED_FACE"), None)

        if not doc_img or not pres_img:
            raise HTTPException(
                status_code=400,
                detail="Case must contain at least one primary ID document and one presented face selfie."
            )

        with open(doc_img.file_path, "rb") as f:
            doc_bytes = f.read()
        with open(pres_img.file_path, "rb") as f:
            pres_bytes = f.read()

        verifier = OpenCVFaceVerifier()
        face_res = verifier.verify_faces(doc_bytes, pres_bytes)

        # Clear old face verification
        old_fv = db.query(FaceVerificationResultModel).filter(FaceVerificationResultModel.case_id == case.id).first()
        if old_fv:
            db.delete(old_fv)

        fv_model = FaceVerificationResultModel(
            case_id=case.id,
            similarity_score=face_res.similarity_score,
            status=face_res.status,
            confidence=face_res.confidence,
            explanation=face_res.explanation
        )
        db.add(fv_model)
        db.commit()
        db.refresh(fv_model)

        AuditService.record_action(
            db,
            action="FACE_VERIFICATION_COMPLETED",
            case_id=case.id,
            user_id=officer_id,
            details={"status": face_res.status, "similarity": face_res.similarity_score}
        )

        return fv_model

    @staticmethod
    def process_validation(db: Session, case_id: str, officer_id: Optional[str] = None) -> ValidationResult:
        case = db.query(ScreeningCase).filter(ScreeningCase.id == case_id).first()
        if not case:
            raise HTTPException(status_code=404, detail="Case not found")

        validator = DocumentValidator()
        all_rules = []
        all_errors = []

        # Validate single documents
        doc_fields_map = {}
        for doc in case.documents:
            fields = {f.field_name: f.field_value for f in doc.fields}
            doc_fields_map[doc.document_type] = fields
            summary = validator.validate_document_fields(doc.document_type, fields)
            all_rules.extend(summary.rule_results)
            all_errors.extend(summary.errors)

        # Cross validate if both Passport and Visa exist
        if "PASSPORT" in doc_fields_map and "VISA" in doc_fields_map:
            cross_summary = validator.cross_validate_documents(
                "Passport", doc_fields_map["PASSPORT"],
                "Visa", doc_fields_map["VISA"]
            )
            all_rules.extend(cross_summary.rule_results)
            all_errors.extend(cross_summary.errors)

        # Clear old validation
        db.query(ValidationResult).filter(ValidationResult.case_id == case.id).delete()

        rules_serialized = [
            {"rule_name": r.rule_name, "passed": r.passed, "message": r.message, "severity": r.severity}
            for r in all_rules
        ]

        val_model = ValidationResult(
            case_id=case.id,
            passed=(len(all_errors) == 0),
            rule_details_json=json.dumps(rules_serialized),
            errors_json=json.dumps(all_errors)
        )
        db.add(val_model)
        db.commit()
        db.refresh(val_model)

        AuditService.record_action(
            db,
            action="VALIDATION_COMPLETED",
            case_id=case.id,
            user_id=officer_id,
            details={"passed": val_model.passed, "error_count": len(all_errors)}
        )

        return val_model

    @staticmethod
    def process_risk_analysis(db: Session, case_id: str, officer_id: Optional[str] = None) -> RiskAssessment:
        case = db.query(ScreeningCase).filter(ScreeningCase.id == case_id).first()
        if not case:
            raise HTTPException(status_code=404, detail="Case not found")

        # Collect results
        primary_doc = next((d for d in case.documents if d.document_type in ("PASSPORT", "NATIONAL_ID")), None)
        if not primary_doc and case.documents:
            primary_doc = case.documents[0]

        ocr_res = None
        tampering_res = None

        if primary_doc:
            if primary_doc.ocr_result:
                from ai.core.interfaces import OCRResult, OCRField
                ocr_fields = {
                    f.field_name: OCRField(field_name=f.field_name, value=f.field_value, confidence=f.confidence)
                    for f in primary_doc.fields
                }
                ocr_res = OCRResult(
                    provider=primary_doc.ocr_result.provider,
                    raw_text=primary_doc.ocr_result.raw_text or "",
                    fields=ocr_fields,
                    average_confidence=primary_doc.ocr_result.average_confidence
                )

            if primary_doc.tampering_result:
                from ai.core.interfaces import TamperingResult
                tr = primary_doc.tampering_result
                tampering_res = TamperingResult(
                    provider="ComputerVisionTamperingAnalyzer",
                    tampering_score=tr.tampering_score,
                    confidence=tr.confidence,
                    detected_indicators=json.loads(tr.indicators_json or "[]"),
                    suspicious_regions=[],
                    metadata_anomalies=json.loads(tr.metadata_anomalies_json or "[]"),
                    recommendation=tr.recommendation,
                    explanation=""
                )

        face_res = None
        if case.face_verification:
            from ai.core.interfaces import FaceVerificationResult
            fv = case.face_verification
            face_res = FaceVerificationResult(
                provider="OpenCVFaceVerifier",
                similarity_score=fv.similarity_score,
                confidence=fv.confidence,
                status=fv.status,
                document_face_detected=True,
                presented_face_detected=True,
                explanation=fv.explanation
            )

        validation_errors = []
        latest_val = db.query(ValidationResult).filter(ValidationResult.case_id == case.id).first()
        if latest_val:
            validation_errors = json.loads(latest_val.errors_json or "[]")

        engine = ConfigurableRiskEngine()
        risk_result = engine.calculate_risk(ocr_res, tampering_res, face_res, validation_errors)

        # Clear old risk assessment
        db.query(RiskAssessment).filter(RiskAssessment.case_id == case.id).delete()

        factors_serialized = [
            {
                "factor_name": f.factor_name,
                "weight": f.weight,
                "contribution": f.contribution,
                "description": f.description
            }
            for f in risk_result.contributing_factors
        ]

        risk_model = RiskAssessment(
            case_id=case.id,
            overall_score=risk_result.overall_score,
            classification=risk_result.classification,
            factors_json=json.dumps(factors_serialized),
            recommendation=risk_result.recommendation,
            summary_explanation=risk_result.summary_explanation
        )
        db.add(risk_model)

        # Update case status based on risk
        if risk_result.classification in ("HIGH", "CRITICAL"):
            case.status = "REVIEW_REQUIRED"
        elif risk_result.classification == "LOW":
            case.status = "PROCESSING"
        else:
            case.status = "PROCESSING"

        db.commit()
        db.refresh(risk_model)

        AuditService.record_action(
            db,
            action="RISK_CALCULATED",
            case_id=case.id,
            user_id=officer_id,
            details={"risk_score": risk_result.overall_score, "classification": risk_result.classification}
        )

        return risk_model

    @staticmethod
    def register_on_blockchain(db: Session, case_id: str, officer_id: Optional[str] = None) -> BlockchainRecord:
        case = db.query(ScreeningCase).filter(ScreeningCase.id == case_id).first()
        if not case:
            raise HTTPException(status_code=404, detail="Case not found")

        primary_doc = next((d for d in case.documents if d.document_type in ("PASSPORT", "NATIONAL_ID")), None)
        if not primary_doc and case.documents:
            primary_doc = case.documents[0]

        if not primary_doc:
            raise HTTPException(status_code=400, detail="Cannot register case with zero uploaded documents.")

        risk_score = int(case.risk_assessment.overall_score) if case.risk_assessment else 25

        # Compute verification payload hash
        payload_hash = hashlib.sha256(
            f"{case.case_number}:{primary_doc.sha256_hash}:{risk_score}".encode()
        ).hexdigest()

        blockchain_provider = get_blockchain_provider()
        bc_record = blockchain_provider.register_document(
            case_id=case.case_number,
            document_hash_hex=primary_doc.sha256_hash,
            verification_hash_hex=payload_hash,
            risk_score=risk_score
        )

        # Clear old record
        db.query(BlockchainRecord).filter(BlockchainRecord.case_id == case.id).delete()

        record_model = BlockchainRecord(
            case_id=case.id,
            network=bc_record.network,
            contract_address=bc_record.contract_address,
            tx_hash=bc_record.tx_hash,
            block_number=bc_record.block_number,
            case_hash=bc_record.case_hash,
            document_hash=bc_record.document_hash,
            verification_hash=bc_record.verification_hash,
            status="CONFIRMED"
        )
        db.add(record_model)
        db.commit()
        db.refresh(record_model)

        AuditService.record_action(
            db,
            action="BLOCKCHAIN_REGISTERED",
            case_id=case.id,
            user_id=officer_id,
            details={"tx_hash": bc_record.tx_hash, "case_hash": bc_record.case_hash, "network": bc_record.network}
        )

        return record_model

    @staticmethod
    def record_officer_review(
        db: Session,
        case_id: str,
        officer_id: str,
        decision: str,
        notes: Optional[str] = None
    ) -> OfficerReview:
        case = db.query(ScreeningCase).filter(ScreeningCase.id == case_id).first()
        if not case:
            raise HTTPException(status_code=404, detail="Case not found")

        # Update case status
        if decision == "VERIFIED":
            case.status = "VERIFIED"
        elif decision in ("SUSPICIOUS", "REJECTED"):
            case.status = "SUSPICIOUS"
        elif decision == "SUPERVISOR_REVIEW":
            case.status = "REVIEW_REQUIRED"

        # Remove old review
        db.query(OfficerReview).filter(OfficerReview.case_id == case.id).delete()

        review = OfficerReview(
            case_id=case.id,
            officer_id=officer_id,
            decision=decision,
            notes=notes
        )
        db.add(review)
        db.commit()
        db.refresh(review)

        AuditService.record_action(
            db,
            action="OFFICER_REVIEW",
            case_id=case.id,
            user_id=officer_id,
            details={"decision": decision, "notes": notes or ""}
        )

        return review
