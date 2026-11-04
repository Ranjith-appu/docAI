"""
Blockchain Integrity Verification API Endpoint.
Allows officers and external auditors to independently verify document integrity against on-chain records.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.core.security import get_current_user
from backend.app.models.models import ScreeningCase, Document, User
from backend.app.schemas.schemas import BlockchainVerifyRequest, BlockchainVerifyResponse
from backend.app.services.blockchain_service import get_blockchain_provider
from backend.app.services.audit_service import AuditService

router = APIRouter(prefix="/blockchain", tags=["Blockchain Verification"])


@router.post("/verify", response_model=BlockchainVerifyResponse)
def verify_document_on_blockchain(
    request: BlockchainVerifyRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    case_query = request.case_number or request.case_id
    if not case_query and not request.document_hash:
        raise HTTPException(
            status_code=400,
            detail="Either case identifier (case_number / case_id) or document_hash must be supplied."
        )

    case = None
    if case_query:
        case = db.query(ScreeningCase).filter(
            (ScreeningCase.id == case_query) | (ScreeningCase.case_number == case_query)
        ).first()

    # Determine current document hash
    current_doc_hash = request.document_hash
    if not current_doc_hash and case:
        primary_doc = next((d for d in case.documents if d.document_type in ("PASSPORT", "NATIONAL_ID")), None)
        if not primary_doc and case.documents:
            primary_doc = case.documents[0]
        if primary_doc:
            current_doc_hash = primary_doc.sha256_hash

    if not current_doc_hash:
        current_doc_hash = "0000000000000000000000000000000000000000000000000000000000000000"

    blockchain_provider = get_blockchain_provider()
    target_case_id = case.case_number if case else (case_query or "UNKNOWN_CASE")

    matched, bc_record = blockchain_provider.verify_document(target_case_id, current_doc_hash)

    AuditService.record_action(
        db,
        action="BLOCKCHAIN_VERIFICATION_CHECK",
        case_id=case.id if case else None,
        user_id=current_user.id,
        details={
            "case_id": target_case_id,
            "checked_hash": current_doc_hash,
            "matched": matched
        }
    )

    if not bc_record:
        return BlockchainVerifyResponse(
            matched=False,
            status="RECORD NOT FOUND",
            case_number=target_case_id,
            current_document_hash=current_doc_hash,
            blockchain_document_hash="N/A",
            blockchain_case_hash="N/A",
            network="Ethereum Sepolia",
            contract_address="0x71C67e3FeB8Ab7e06a3B81C437e54F264DeEb852",
            details="No matching screening registration found on the blockchain for this Case identifier."
        )

    return BlockchainVerifyResponse(
        matched=matched,
        status="MATCH" if matched else "DOES NOT MATCH",
        case_number=target_case_id,
        current_document_hash=current_doc_hash,
        blockchain_document_hash=bc_record.document_hash,
        blockchain_case_hash=bc_record.case_hash,
        block_timestamp=str(bc_record.timestamp),
        risk_score=bc_record.risk_score,
        network=bc_record.network,
        contract_address=bc_record.contract_address,
        explorer_url=f"https://sepolia.etherscan.io/tx/{bc_record.tx_hash}",
        details=(
            "Cryptographic proof verified. Current document SHA-256 matches on-chain registration timestamp and hash."
            if matched else
            "CRITICAL INTEGRITY MISMATCH: The current document binary does not match the immutable cryptographic hash recorded on the blockchain!"
        )
    )
