"""
Case Management API Endpoints.
"""
import json
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.core.security import get_current_user
from backend.app.models.models import ScreeningCase, User
from backend.app.schemas.schemas import (
    CaseCreate, CaseOut, CaseDetailOut, DocumentOut,
    OCRResponse, ValidationResponse, TamperingResponse, FaceResponse,
    RiskResponse, BlockchainRecordOut, OfficerReviewOut
)
from backend.app.services.screening_service import ScreeningService

router = APIRouter(prefix="/cases", tags=["Case Management"])


@router.post("", response_model=CaseOut, status_code=status.HTTP_201_CREATED)
def create_case(
    payload: CaseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    case = ScreeningService.create_case(
        db,
        applicant_name=payload.applicant_name,
        document_type=payload.document_type,
        officer_id=current_user.id
    )
    return CaseOut.model_validate(case)


@router.get("", response_model=List[CaseOut])
def list_cases(
    status_filter: Optional[str] = Query(None, alias="status"),
    search: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    skip: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(ScreeningCase)
    if status_filter:
        query = query.filter(ScreeningCase.status == status_filter.upper())
    if search:
        search_fmt = f"%{search}%"
        query = query.filter(
            (ScreeningCase.case_number.ilike(search_fmt)) |
            (ScreeningCase.applicant_name.ilike(search_fmt))
        )
    cases = query.order_by(ScreeningCase.created_at.desc()).offset(skip).limit(limit).all()
    return [CaseOut.model_validate(c) for c in cases]


@router.get("/{id}", response_model=CaseDetailOut)
def get_case_detail(
    id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    case = db.query(ScreeningCase).filter(
        (ScreeningCase.id == id) | (ScreeningCase.case_number == id)
    ).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    # Construct documents
    docs_out = [DocumentOut.model_validate(d) for d in case.documents]

    # OCR results
    ocr_results_out = []
    for doc in case.documents:
        if doc.ocr_result:
            fields_dict = {
                f.field_name: {
                    "field_name": f.field_name,
                    "value": f.field_value,
                    "confidence": f.confidence
                }
                for f in doc.fields
            }
            ocr_results_out.append(
                OCRResponse(
                    document_id=doc.id,
                    provider=doc.ocr_result.provider,
                    raw_text=doc.ocr_result.raw_text or "",
                    average_confidence=doc.ocr_result.average_confidence,
                    fields=fields_dict
                )
            )

    # Validation
    val_out = None
    latest_val = db.query(ScreeningCase).filter(ScreeningCase.id == case.id).first().validation_results
    if latest_val:
        v = latest_val[-1]
        val_out = ValidationResponse(
            case_id=case.id,
            passed=v.passed,
            rule_results=json.loads(v.rule_details_json or "[]"),
            errors=json.loads(v.errors_json or "[]")
        )

    # Tampering results
    tampering_out = []
    for doc in case.documents:
        if doc.tampering_result:
            tr = doc.tampering_result
            tampering_out.append(
                TamperingResponse(
                    document_id=doc.id,
                    tampering_score=tr.tampering_score,
                    confidence=tr.confidence,
                    detected_indicators=json.loads(tr.indicators_json or "[]"),
                    suspicious_regions=json.loads(tr.regions_json or "[]"),
                    metadata_anomalies=json.loads(tr.metadata_anomalies_json or "[]"),
                    recommendation=tr.recommendation,
                    explanation=f"Tampering score is {tr.tampering_score}%. {tr.recommendation}"
                )
            )

    # Face verification
    face_out = None
    if case.face_verification:
        fv = case.face_verification
        face_out = FaceResponse(
            case_id=case.id,
            similarity_score=fv.similarity_score,
            confidence=fv.confidence,
            status=fv.status,
            explanation=fv.explanation
        )

    # Risk Assessment
    risk_out = None
    if case.risk_assessment:
        ra = case.risk_assessment
        risk_out = RiskResponse(
            case_id=case.id,
            overall_score=ra.overall_score,
            classification=ra.classification,
            contributing_factors=json.loads(ra.factors_json or "[]"),
            recommendation=ra.recommendation,
            summary_explanation=ra.summary_explanation
        )

    # Blockchain Record
    bc_out = None
    if case.blockchain_record:
        br = case.blockchain_record
        bc_out = BlockchainRecordOut.model_validate(br)

    # Officer Review
    review_out = None
    if case.officer_review:
        orv = case.officer_review
        review_out = OfficerReviewOut(
            id=orv.id,
            case_id=orv.case_id,
            officer_id=orv.officer_id,
            officer_name=orv.officer.full_name if orv.officer else "Authorized Officer",
            decision=orv.decision,
            notes=orv.notes,
            reviewed_at=orv.reviewed_at
        )

    return CaseDetailOut(
        case=CaseOut.model_validate(case),
        documents=docs_out,
        ocr_results=ocr_results_out,
        validation=val_out,
        tampering_results=tampering_out,
        face_verification=face_out,
        risk_assessment=risk_out,
        blockchain_record=bc_out,
        officer_review=review_out
    )
