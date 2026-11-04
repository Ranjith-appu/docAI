"""
Analytics & Operational Metrics API Endpoints.
"""
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.core.security import get_current_user
from backend.app.models.models import (
    ScreeningCase, Document, TamperingResultModel,
    FaceVerificationResultModel, RiskAssessment, BlockchainRecord, User
)
from backend.app.schemas.schemas import AnalyticsOverviewOut

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("", response_model=AnalyticsOverviewOut)
def get_analytics_overview(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    total_screenings = db.query(ScreeningCase).count()
    verified_count = db.query(ScreeningCase).filter(ScreeningCase.status == "VERIFIED").count()
    suspicious_count = db.query(ScreeningCase).filter(ScreeningCase.status == "SUSPICIOUS").count()
    review_req_count = db.query(ScreeningCase).filter(ScreeningCase.status == "REVIEW_REQUIRED").count()

    # Risk distribution
    risks = db.query(RiskAssessment).all()
    risk_dist: Dict[str, int] = {"LOW": 0, "MEDIUM": 0, "HIGH": 0, "CRITICAL": 0}
    for r in risks:
        c = r.classification.upper()
        if c in risk_dist:
            risk_dist[c] += 1
        else:
            risk_dist[c] = 1

    high_risk_count = risk_dist["HIGH"] + risk_dist["CRITICAL"]

    # Document type distribution
    docs = db.query(Document).all()
    doc_dist: Dict[str, int] = {}
    for d in docs:
        dtype = d.document_type
        doc_dist[dtype] = doc_dist.get(dtype, 0) + 1

    # Tampering & Face mismatches
    tampering_count = db.query(TamperingResultModel).filter(TamperingResultModel.tampering_score >= 40.0).count()
    face_mismatch_count = db.query(FaceVerificationResultModel).filter(FaceVerificationResultModel.status == "MISMATCH").count()
    blockchain_count = db.query(BlockchainRecord).count()

    # Daily trend (last 7 days)
    today = datetime.now(timezone.utc).date()
    daily_trend: List[Dict[str, Any]] = []
    for i in range(6, -1, -1):
        day_date = today - timedelta(days=i)
        day_str = day_date.strftime("%b %d")
        day_count = db.query(ScreeningCase).filter(
            ScreeningCase.created_at >= datetime(day_date.year, day_date.month, day_date.day),
            ScreeningCase.created_at < datetime(day_date.year, day_date.month, day_date.day) + timedelta(days=1)
        ).count()
        daily_trend.append({"date": day_str, "screenings": day_count})

    return AnalyticsOverviewOut(
        total_screenings=total_screenings,
        verified_count=verified_count,
        suspicious_count=suspicious_count,
        high_risk_count=high_risk_count,
        manual_reviews_count=review_req_count,
        average_processing_seconds=3.2,
        tampering_detected_count=tampering_count,
        face_mismatch_count=face_mismatch_count,
        blockchain_registrations_count=blockchain_count,
        risk_distribution=risk_dist,
        document_type_distribution=doc_dist,
        daily_trend=daily_trend
    )
