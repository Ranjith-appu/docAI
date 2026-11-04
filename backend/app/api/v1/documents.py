"""
Document Management & Upload API Endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Response, status
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.core.security import get_current_user
from backend.app.models.models import ScreeningCase, Document, User
from backend.app.schemas.schemas import DocumentOut
from backend.app.services.storage_service import validate_and_save_upload
from backend.app.services.audit_service import AuditService

router = APIRouter(tags=["Document Management"])


@router.post("/cases/{case_id}/documents", response_model=DocumentOut, status_code=status.HTTP_201_CREATED)
def upload_document(
    case_id: str,
    document_type: str = Form("PASSPORT"),  # PASSPORT, VISA, NATIONAL_ID, PRESENTED_FACE
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    case = db.query(ScreeningCase).filter(
        (ScreeningCase.id == case_id) | (ScreeningCase.case_number == case_id)
    ).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    stored_path, sha256_hash, file_size, mime_type = validate_and_save_upload(file)

    doc = Document(
        case_id=case.id,
        document_type=document_type.upper(),
        file_name=file.filename or f"{document_type.lower()}.png",
        file_path=stored_path,
        sha256_hash=sha256_hash,
        mime_type=mime_type,
        file_size=file_size
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    AuditService.record_action(
        db,
        action="UPLOAD_DOCUMENT",
        case_id=case.id,
        user_id=current_user.id,
        details={
            "document_id": doc.id,
            "document_type": doc.document_type,
            "sha256": doc.sha256_hash,
            "file_size": doc.file_size
        }
    )

    return DocumentOut.model_validate(doc)


@router.get("/documents/{document_id}/file")
def get_document_file(
    document_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    try:
        with open(doc.file_path, "rb") as f:
            content = f.read()
    except Exception:
        raise HTTPException(status_code=404, detail="Underlying document file not found on disk")

    return Response(content=content, media_type=doc.mime_type)
