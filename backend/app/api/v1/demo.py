"""
Demo & Synthetic Seeding API Endpoints.
Pre-seeds the 3 required demonstration cases (Verified, Suspicious, High Risk).
All documents are strictly labeled 'SYNTHETIC / DEMO DATA - NOT AN OFFICIAL DOCUMENT'.
"""
import os
import hashlib
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.core.security import get_current_user
from backend.app.models.models import ScreeningCase, Document, User
from backend.app.services.screening_service import ScreeningService
from backend.app.services.storage_service import LocalStorageProvider
from ai.document.synthetic_generator import (
    generate_synthetic_passport,
    generate_synthetic_visa,
    generate_synthetic_presented_face
)

router = APIRouter(prefix="/demo", tags=["Demo Mode"])


@router.post("/seed")
def seed_demo_cases(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    storage = LocalStorageProvider()
    created_cases = []

    # ==========================================
    # CASE 1: VERIFIED (Low Risk, Clean Pass)
    # ==========================================
    case1 = ScreeningService.create_case(
        db,
        applicant_name="JOHN DOE (SYNTHETIC)",
        document_type="PASSPORT",
        officer_id=current_user.id
    )

    # 1. Generate clean passport & visa & selfie
    c1_pass = generate_synthetic_passport("JOHN DOE", "A12345678", "UTO", "1992-05-14", "2029-08-20", is_tampered=False)
    c1_visa = generate_synthetic_visa("JOHN DOE", "A12345678", "V98765432", "2029-08-20")
    c1_face = generate_synthetic_presented_face("JOHN DOE", is_mismatch=False)

    p1_path, p1_hash, p1_sz = storage.save_file(c1_pass, "john_doe_passport_synthetic.png")
    v1_path, v1_hash, v1_sz = storage.save_file(c1_visa, "john_doe_visa_synthetic.png")
    f1_path, f1_hash, f1_sz = storage.save_file(c1_face, "john_doe_selfie_synthetic.png")

    doc1_p = Document(case_id=case1.id, document_type="PASSPORT", file_name="john_doe_passport_synthetic.png", file_path=p1_path, sha256_hash=p1_hash, mime_type="image/png", file_size=p1_sz)
    doc1_v = Document(case_id=case1.id, document_type="VISA", file_name="john_doe_visa_synthetic.png", file_path=v1_path, sha256_hash=v1_hash, mime_type="image/png", file_size=v1_sz)
    doc1_f = Document(case_id=case1.id, document_type="PRESENTED_FACE", file_name="john_doe_selfie_synthetic.png", file_path=f1_path, sha256_hash=f1_hash, mime_type="image/png", file_size=f1_sz)
    db.add_all([doc1_p, doc1_v, doc1_f])
    db.commit()

    # Process pipeline
    ScreeningService.process_ocr(db, doc1_p.id, current_user.id)
    ScreeningService.process_ocr(db, doc1_v.id, current_user.id)
    ScreeningService.process_validation(db, case1.id, current_user.id)
    ScreeningService.process_tampering(db, doc1_p.id, current_user.id)
    ScreeningService.process_face_verification(db, case1.id, current_user.id)
    ScreeningService.process_risk_analysis(db, case1.id, current_user.id)
    ScreeningService.register_on_blockchain(db, case1.id, current_user.id)
    ScreeningService.record_officer_review(db, case1.id, current_user.id, "VERIFIED", "Clean synthetic demo case. All biometric and OCR indicators matched.")
    created_cases.append({"case_number": case1.case_number, "profile": "Verified / Low Risk", "applicant": case1.applicant_name})

    # ==========================================
    # CASE 2: SUSPICIOUS (Tampering / Mismatch)
    # ==========================================
    case2 = ScreeningService.create_case(
        db,
        applicant_name="JANE SMITH (SYNTHETIC)",
        document_type="PASSPORT",
        officer_id=current_user.id
    )

    c2_pass = generate_synthetic_passport("JANE SMITH", "B98765432", "UTO", "1995-11-23", "2028-10-15", is_tampered=True)
    c2_visa = generate_synthetic_visa("JANE SMITH", "B98765430", "V12345678", "2028-10-15")  # Number mismatch: 32 vs 30
    c2_face = generate_synthetic_presented_face("JANE SMITH", is_mismatch=False)

    p2_path, p2_hash, p2_sz = storage.save_file(c2_pass, "jane_smith_passport_tampered_synthetic.png")
    v2_path, v2_hash, v2_sz = storage.save_file(c2_visa, "jane_smith_visa_mismatch_synthetic.png")
    f2_path, f2_hash, f2_sz = storage.save_file(c2_face, "jane_smith_selfie_synthetic.png")

    doc2_p = Document(case_id=case2.id, document_type="PASSPORT", file_name="jane_smith_passport_tampered_synthetic.png", file_path=p2_path, sha256_hash=p2_hash, mime_type="image/png", file_size=p2_sz)
    doc2_v = Document(case_id=case2.id, document_type="VISA", file_name="jane_smith_visa_mismatch_synthetic.png", file_path=v2_path, sha256_hash=v2_hash, mime_type="image/png", file_size=v2_sz)
    doc2_f = Document(case_id=case2.id, document_type="PRESENTED_FACE", file_name="jane_smith_selfie_synthetic.png", file_path=f2_path, sha256_hash=f2_hash, mime_type="image/png", file_size=f2_sz)
    db.add_all([doc2_p, doc2_v, doc2_f])
    db.commit()

    ScreeningService.process_ocr(db, doc2_p.id, current_user.id)
    ScreeningService.process_ocr(db, doc2_v.id, current_user.id)
    ScreeningService.process_validation(db, case2.id, current_user.id)
    ScreeningService.process_tampering(db, doc2_p.id, current_user.id)
    ScreeningService.process_face_verification(db, case2.id, current_user.id)
    ScreeningService.process_risk_analysis(db, case2.id, current_user.id)
    ScreeningService.register_on_blockchain(db, case2.id, current_user.id)
    ScreeningService.record_officer_review(db, case2.id, current_user.id, "SUSPICIOUS", "Document number mismatch between passport and visa. Visual alteration marker on photo border.")
    created_cases.append({"case_number": case2.case_number, "profile": "Suspicious / Moderate-High Risk", "applicant": case2.applicant_name})

    # ==========================================
    # CASE 3: HIGH RISK (Face Mismatch & Expired)
    # ==========================================
    case3 = ScreeningService.create_case(
        db,
        applicant_name="ALEX RIVERA (SYNTHETIC)",
        document_type="PASSPORT",
        officer_id=current_user.id
    )

    c3_pass = generate_synthetic_passport("ALEX RIVERA", "C45678901", "UTO", "1988-02-19", "2022-01-01", is_tampered=True)  # Expired
    c3_face = generate_synthetic_presented_face("ALEX RIVERA", is_mismatch=True)  # Biometric mismatch

    p3_path, p3_hash, p3_sz = storage.save_file(c3_pass, "alex_rivera_expired_passport_synthetic.png")
    f3_path, f3_hash, f3_sz = storage.save_file(c3_face, "alex_rivera_imposter_selfie_synthetic.png")

    doc3_p = Document(case_id=case3.id, document_type="PASSPORT", file_name="alex_rivera_expired_passport_synthetic.png", file_path=p3_path, sha256_hash=p3_hash, mime_type="image/png", file_size=p3_sz)
    doc3_f = Document(case_id=case3.id, document_type="PRESENTED_FACE", file_name="alex_rivera_imposter_selfie_synthetic.png", file_path=f3_path, sha256_hash=f3_hash, mime_type="image/png", file_size=f3_sz)
    db.add_all([doc3_p, doc3_f])
    db.commit()

    ScreeningService.process_ocr(db, doc3_p.id, current_user.id)
    ScreeningService.process_validation(db, case3.id, current_user.id)
    ScreeningService.process_tampering(db, doc3_p.id, current_user.id)
    ScreeningService.process_face_verification(db, case3.id, current_user.id)
    ScreeningService.process_risk_analysis(db, case3.id, current_user.id)
    ScreeningService.register_on_blockchain(db, case3.id, current_user.id)
    ScreeningService.record_officer_review(db, case3.id, current_user.id, "REJECTED", "Biometric face comparison failed. Travel document has expired.")
    created_cases.append({"case_number": case3.case_number, "profile": "High Risk / Rejected", "applicant": case3.applicant_name})

    return {
        "success": True,
        "message": "Seeded 3 realistic synthetic demonstration cases with full OCR, Forensics, Biometrics, and Blockchain proof.",
        "cases": created_cases
    }
