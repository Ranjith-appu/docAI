"""
Tamper-Evident Audit Trail API Endpoints.
"""
import json
from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.core.security import get_current_user
from backend.app.models.models import AuditLog, User
from backend.app.schemas.schemas import AuditLogOut
from backend.app.services.audit_service import AuditService

router = APIRouter(prefix="/audit-logs", tags=["Audit Trail"])


@router.get("", response_model=List[AuditLogOut])
def get_audit_logs(
    case_id: Optional[str] = Query(None),
    action: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(AuditLog)
    if case_id:
        query = query.filter(AuditLog.case_id == case_id)
    if action:
        query = query.filter(AuditLog.action == action.upper())

    logs = query.order_by(AuditLog.timestamp.desc()).limit(limit).all()

    results = []
    for l in logs:
        try:
            d = json.loads(l.details_json or "{}")
        except Exception:
            d = {}
        results.append(
            AuditLogOut(
                id=l.id,
                case_id=l.case_id,
                user_id=l.user_id,
                action=l.action,
                prev_hash=l.prev_hash,
                entry_hash=l.entry_hash,
                timestamp=l.timestamp,
                details=d
            )
        )
    return results


@router.get("/verify-chain")
def verify_audit_chain(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    valid = AuditService.verify_chain_integrity(db)
    count = db.query(AuditLog).count()
    return {
        "chain_intact": valid,
        "total_verified_entries": count,
        "status": "TAMPER_FREE" if valid else "TAMPERING_DETECTED",
        "description": "Cryptographic SHA-256 hash sequence verified across all log blocks."
    }
