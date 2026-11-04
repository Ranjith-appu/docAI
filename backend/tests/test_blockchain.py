"""
Tests for Blockchain Proof Registration and Integrity Verification.
Verifies that:
1. Valid documents register cryptographic hashes without PII.
2. Identical document hashes return MATCH / VERIFIED.
3. Modified document hashes trigger CRITICAL INTEGRITY MISMATCH.
"""
import hashlib
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)


def get_officer_token():
    res = client.post(
        "/api/v1/auth/login",
        json={"email": "officer@docai.gov", "password": "Officer@123456"}
    )
    return res.json()["access_token"]


def test_blockchain_verification_matching_and_mismatch():
    token = get_officer_token()
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Create a Case
    c_res = client.post(
        "/api/v1/cases",
        json={"applicant_name": "BLOCKCHAIN TEST APPLICANT", "document_type": "PASSPORT"},
        headers=headers
    )
    assert c_res.status_code == 201
    case_data = c_res.json()
    case_id = case_data["id"]
    case_number = case_data["case_number"]

    # 2. Upload Document
    doc_bytes = b"AUTHENTIC_SYNTHETIC_DOCUMENT_CONTENT_12345"
    sha_orig = hashlib.sha256(doc_bytes).hexdigest()

    u_res = client.post(
        f"/api/v1/cases/{case_id}/documents",
        data={"document_type": "PASSPORT"},
        files={"file": ("passport.png", doc_bytes, "image/png")},
        headers=headers
    )
    assert u_res.status_code == 201

    # 3. Register on Blockchain
    bc_reg_res = client.post(
        f"/api/v1/cases/{case_id}/blockchain/register",
        headers=headers
    )
    assert bc_reg_res.status_code == 200
    bc_rec = bc_reg_res.json()
    assert bc_rec["status"] == "CONFIRMED"
    assert "0x" in bc_rec["tx_hash"]
    assert sha_orig in bc_rec["document_hash"]

    # 4. Verify with EXACT document hash -> Expect MATCH
    v_res = client.post(
        "/api/v1/blockchain/verify",
        json={"case_number": case_number, "document_hash": sha_orig},
        headers=headers
    )
    assert v_res.status_code == 200
    v_data = v_res.json()
    assert v_data["matched"] is True
    assert v_data["status"] == "MATCH"
    assert "verified" in v_data["details"].lower()

    # 5. Verify with ALTERED document hash -> Expect DOES NOT MATCH
    altered_sha = hashlib.sha256(b"ALTERED_OR_FORGED_DOCUMENT_CONTENT_999").hexdigest()
    v_mismatch = client.post(
        "/api/v1/blockchain/verify",
        json={"case_number": case_number, "document_hash": altered_sha},
        headers=headers
    )
    assert v_mismatch.status_code == 200
    v_mismatch_data = v_mismatch.json()
    assert v_mismatch_data["matched"] is False
    assert v_mismatch_data["status"] == "DOES NOT MATCH"
    assert "mismatch" in v_mismatch_data["details"].lower()
