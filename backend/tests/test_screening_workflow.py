"""
End-to-End Screening Pipeline & Report Verification Tests.
"""
from fastapi.testclient import TestClient
from backend.app.main import app
from ai.document.synthetic_generator import (
    generate_synthetic_passport,
    generate_synthetic_visa,
    generate_synthetic_presented_face
)

client = TestClient(app)


def test_full_screening_pipeline_and_pdf():
    # 1. Login
    login_res = client.post(
        "/api/v1/auth/login",
        json={"email": "officer@docai.gov", "password": "Officer@123456"}
    )
    assert login_res.status_code == 200
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Create Screening Case
    c_res = client.post(
        "/api/v1/cases",
        json={"applicant_name": "JOHNATHAN DOE", "document_type": "PASSPORT"},
        headers=headers
    )
    assert c_res.status_code == 201
    case_id = c_res.json()["id"]

    # 3. Upload Synthetic Passport, Visa, and Selfie
    pass_bytes = generate_synthetic_passport("JOHNATHAN DOE", "A87654321", "UTO", "1991-03-22", "2030-05-10")
    visa_bytes = generate_synthetic_visa("JOHNATHAN DOE", "A87654321", "V55443322", "2030-05-10")
    face_bytes = generate_synthetic_presented_face("JOHNATHAN DOE", is_mismatch=False)

    p_upload = client.post(
        f"/api/v1/cases/{case_id}/documents",
        data={"document_type": "PASSPORT"},
        files={"file": ("passport.png", pass_bytes, "image/png")},
        headers=headers
    )
    assert p_upload.status_code == 201
    doc_p_id = p_upload.json()["id"]

    v_upload = client.post(
        f"/api/v1/cases/{case_id}/documents",
        data={"document_type": "VISA"},
        files={"file": ("visa.png", visa_bytes, "image/png")},
        headers=headers
    )
    assert v_upload.status_code == 201
    doc_v_id = v_upload.json()["id"]

    f_upload = client.post(
        f"/api/v1/cases/{case_id}/documents",
        data={"document_type": "PRESENTED_FACE"},
        files={"file": ("selfie.png", face_bytes, "image/png")},
        headers=headers
    )
    assert f_upload.status_code == 201

    # 4. OCR Extraction
    ocr_res = client.post(f"/api/v1/documents/{doc_p_id}/ocr", headers=headers)
    assert ocr_res.status_code == 200
    ocr_data = ocr_res.json()
    assert ocr_data["average_confidence"] > 80.0
    assert "document_number" in ocr_data["fields"]

    # 5. Document Validation
    val_res = client.post(f"/api/v1/cases/{case_id}/validate", headers=headers)
    assert val_res.status_code == 200
    val_data = val_res.json()
    assert "rule_results" in val_data

    # 6. Tampering Forensics
    tamp_res = client.post(f"/api/v1/documents/{doc_p_id}/tampering-analysis", headers=headers)
    assert tamp_res.status_code == 200
    tamp_data = tamp_res.json()
    assert "tampering_score" in tamp_data
    assert "recommendation" in tamp_data

    # 7. Face Verification
    face_res = client.post(f"/api/v1/cases/{case_id}/face-verification", headers=headers)
    assert face_res.status_code == 200
    face_data = face_res.json()
    assert face_data["status"] in ("MATCH", "MISMATCH", "UNABLE TO VERIFY")
    assert face_data["similarity_score"] >= 0.0

    # 8. Risk Assessment
    risk_res = client.post(f"/api/v1/cases/{case_id}/risk-analysis", headers=headers)
    assert risk_res.status_code == 200
    risk_data = risk_res.json()
    assert 0 <= risk_data["overall_score"] <= 100
    assert risk_data["classification"] in ("LOW", "MEDIUM", "HIGH", "CRITICAL")
    assert len(risk_data["contributing_factors"]) >= 0

    # 9. Blockchain Anchoring
    bc_res = client.post(f"/api/v1/cases/{case_id}/blockchain/register", headers=headers)
    assert bc_res.status_code == 200
    assert bc_res.json()["status"] == "CONFIRMED"

    # 10. Officer Review
    rev_res = client.post(
        f"/api/v1/cases/{case_id}/review",
        json={"decision": "VERIFIED", "notes": "Approved after automated multi-factor biometric and OCR verification."},
        headers=headers
    )
    assert rev_res.status_code == 200
    assert rev_res.json()["decision"] == "VERIFIED"

    # 11. PDF Report Download
    pdf_res = client.get(f"/api/v1/cases/{case_id}/report", headers=headers)
    assert pdf_res.status_code == 200
    assert pdf_res.headers["content-type"] == "application/pdf"
    assert pdf_res.content.startswith(b"%PDF")

    # 12. Audit Chain Verification
    audit_res = client.get("/api/v1/audit-logs/verify-chain", headers=headers)
    assert audit_res.status_code == 200
    assert audit_res.json()["chain_intact"] is True
    assert audit_res.json()["status"] == "TAMPER_FREE"


def test_demo_seed_three_synthetic_cases():
    login_res = client.post(
        "/api/v1/auth/login",
        json={"email": "officer@docai.gov", "password": "Officer@123456"}
    )
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    seed_res = client.post("/api/v1/demo/seed", headers=headers)
    assert seed_res.status_code == 200
    data = seed_res.json()
    assert data["success"] is True
    assert len(data["cases"]) == 3
    profiles = [c["profile"] for c in data["cases"]]
    assert any("Verified" in p for p in profiles)
    assert any("Suspicious" in p for p in profiles)
    assert any("High Risk" in p for p in profiles)
