"""
Cryptographic Audit Logging Service.
Maintains a tamper-evident, append-only hash-chained audit trail.
Every record computes:
entry_hash = SHA-256(prev_hash + seq + case_id + user_id + action + timestamp_str + details_str)
"""
import json
import hashlib
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session

from backend.app.models.models import AuditLog

GENESIS_HASH = "0000000000000000000000000000000000000000000000000000000000000000"


class AuditService:
    @staticmethod
    def record_action(
        db: Session,
        action: str,
        case_id: Optional[str] = None,
        user_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> AuditLog:
        details_dict = details or {}
        details_str = json.dumps(details_dict, sort_keys=True)

        # Get latest record to link hash chain
        latest = db.query(AuditLog).order_by(AuditLog.seq.desc()).first()
        prev_hash = latest.entry_hash if latest else GENESIS_HASH
        seq = (latest.seq + 1) if latest else 1

        now = datetime.now(timezone.utc)
        ts_str = now.strftime("%Y-%m-%d %H:%M:%S.%f")

        payload = f"{prev_hash}|{seq}|{case_id or 'SYSTEM'}|{user_id or 'ANONYMOUS'}|{action}|{ts_str}|{details_str}"
        entry_hash = hashlib.sha256(payload.encode("utf-8")).hexdigest()

        log_entry = AuditLog(
            seq=seq,
            case_id=case_id,
            user_id=user_id,
            action=action,
            prev_hash=prev_hash,
            entry_hash=entry_hash,
            timestamp=now,
            timestamp_str=ts_str,
            details_json=details_str,
        )

        db.add(log_entry)
        db.commit()
        db.refresh(log_entry)
        return log_entry

    @staticmethod
    def verify_chain_integrity(db: Session) -> bool:
        """Verify the cryptographic hash chain of all audit entries."""
        logs = db.query(AuditLog).order_by(AuditLog.seq.asc()).all()
        if not logs:
            return True

        expected_prev = GENESIS_HASH
        for entry in logs:
            if entry.prev_hash != expected_prev:
                return False
            ts_str = entry.timestamp_str or entry.timestamp.strftime("%Y-%m-%d %H:%M:%S.%f")
            payload = f"{entry.prev_hash}|{entry.seq}|{entry.case_id or 'SYSTEM'}|{entry.user_id or 'ANONYMOUS'}|{entry.action}|{ts_str}|{entry.details_json}"
            calculated_hash = hashlib.sha256(payload.encode("utf-8")).hexdigest()
            if calculated_hash != entry.entry_hash:
                return False
            expected_prev = entry.entry_hash

        return True
