"""
Screening Pipeline & AI Processing API Endpoints.
"""
import json
from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.core.security import get_current_user
from backend.app.models.models import ScreeningCase, Document, User
from backend.app.schemas.schemas import (
    OCRResponse, ValidationResponse, TamperingResponse,
    FaceResponse, RiskResponse, BlockchainRecordOut,
    OfficerReviewRequest, OfficerReviewOut
)
from backend.app.services.screening_service import ScreeningService
from backend.app.services.report_service import ReportService

router = APIRouter(tags=["Screening Pipeline"])


@router.post("/documents/{document_id}/ocr", response_model=OCRResponse)
def run_ocr(
    document_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    ocr_model = ScreeningService.process_ocr(db, document_id, officer_id=current_user.id)
    doc = db.query(Document).filter(Document.id == document_id).first()

    fields_dict = {
        f.field_name: {
            "field_name": f.field_name,
            "value": f.field_value,
            "confidence": f.confidence
        }
        for f in doc.fields
    }

    return OCRResponse(
        document_id=doc.id,
        provider=ocr_model.provider,
        raw_text=ocr_model.raw_text or "",
        average_confidence=ocr_model.average_confidence,
        fields=fields_dict
    )


@router.post("/cases/{case_id}/validate", response_model=ValidationResponse)
def run_validation(
    case_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    val_model = ScreeningService.process_validation(db, case_id, officer_id=current_user.id)
    return ValidationResponse(
        case_id=case_id,
        passed=val_model.passed,
        rule_results=json.loads(val_model.rule_details_json or "[]"),
        errors=json.loads(val_model.errors_json or "[]")
    )


@router.post("/documents/{document_id}/tampering-analysis", response_model=TamperingResponse)
def run_tampering(
    document_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    tamp_model = ScreeningService.process_tampering(db, document_id, officer_id=current_user.id)
    return TamperingResponse(
        document_id=document_id,
        tampering_score=tamp_model.tampering_score,
        confidence=tamp_model.confidence,
        detected_indicators=json.loads(tamp_model.indicators_json or "[]"),
        suspicious_regions=json.loads(tamp_model.regions_json or "[]"),
        metadata_anomalies=json.loads(tamp_model.metadata_anomalies_json or "[]"),
        recommendation=tamp_model.recommendation,
        explanation=f"Tampering suspicion score: {tamp_model.tampering_score}%. {tamp_model.recommendation}."
    )


@router.post("/cases/{case_id}/face-verification", response_model=FaceResponse)
def run_face_verification(
    case_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    fv_model = ScreeningService.process_face_verification(db, case_id, officer_id=current_user.id)
    return FaceResponse(
        case_id=case_id,
        similarity_score=fv_model.similarity_score,
        confidence=fv_model.confidence,
        status=fv_model.status,
        explanation=fv_model.explanation
    )


@router.post("/cases/{case_id}/risk-analysis", response_model=RiskResponse)
def run_risk_analysis(
    case_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    risk_model = ScreeningService.process_risk_analysis(db, case_id, officer_id=current_user.id)
    return RiskResponse(
        case_id=case_id,
        overall_score=risk_model.overall_score,
        classification=risk_model.classification,
        contributing_factors=json.loads(risk_model.factors_json or "[]"),
        recommendation=risk_model.recommendation,
        summary_explanation=risk_model.summary_explanation
    )


@router.post("/cases/{case_id}/blockchain/register", response_model=BlockchainRecordOut)
def register_blockchain(
    case_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    bc_model = ScreeningService.register_on_blockchain(db, case_id, officer_id=current_user.id)
    return BlockchainRecordOut.model_validate(bc_model)


@router.post("/cases/{case_id}/review", response_model=OfficerReviewOut)
def submit_officer_review(
    case_id: str,
    payload: OfficerReviewRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    review = ScreeningService.record_officer_review(
        db,
        case_id=case_id,
        officer_id=current_user.id,
        decision=payload.decision.upper(),
        notes=payload.notes
    )
    return OfficerReviewOut(
        id=review.id,
        case_id=review.case_id,
        officer_id=review.officer_id,
        officer_name=current_user.full_name,
        decision=review.decision,
        notes=review.notes,
        reviewed_at=review.reviewed_at
    )


@router.get("/cases/{case_id}/report")
def download_pdf_report(
    case_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    case = db.query(ScreeningCase).filter(
        (ScreeningCase.id == case_id) | (ScreeningCase.case_number == case_id)
    ).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    pdf_bytes = ReportService.generate_case_pdf(case)
    filename = f"Screening_Report_{case.case_number}.pdf"

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
