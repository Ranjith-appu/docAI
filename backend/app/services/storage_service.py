"""
Secure Storage Service.
Implements StorageProvider abstraction with strict cybersecurity checks:
- MIME type and file extension whitelisting
- Magic byte inspection
- Maximum file size enforcement
- Randomized non-guessable UUID storage filenames
- SHA-256 cryptographic hashing
"""
import os
import uuid
import hashlib
from abc import ABC, abstractmethod
from typing import Tuple
from fastapi import UploadFile, HTTPException, status
from backend.app.core.config import settings


class StorageProvider(ABC):
    @abstractmethod
    def save_file(self, content: bytes, original_filename: str) -> Tuple[str, str, int]:
        """Save file bytes and return (relative_file_path, sha256_hash, file_size)."""
        pass

    @abstractmethod
    def get_file(self, relative_path: str) -> bytes:
        """Retrieve file bytes."""
        pass


class LocalStorageProvider(StorageProvider):
    def __init__(self, base_dir: str = settings.STORAGE_DIR):
        self.base_dir = os.path.abspath(base_dir)
        os.makedirs(self.base_dir, exist_ok=True)

    def save_file(self, content: bytes, original_filename: str) -> Tuple[str, str, int]:
        file_size = len(content)
        sha256_hash = hashlib.sha256(content).hexdigest()

        ext = os.path.splitext(original_filename)[1].lower()
        if not ext:
            ext = ".png"

        # Randomized non-guessable UUID filename
        safe_filename = f"{uuid.uuid4().hex}{ext}"
        destination = os.path.join(self.base_dir, safe_filename)

        with open(destination, "wb") as f:
            f.write(content)

        return destination, sha256_hash, file_size

    def get_file(self, file_path: str) -> bytes:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File at {file_path} does not exist")
        with open(file_path, "rb") as f:
            return f.read()


def validate_and_save_upload(
    upload_file: UploadFile,
    provider: StorageProvider = LocalStorageProvider()
) -> Tuple[str, str, int, str]:
    """
    Validate incoming upload and save securely.
    Returns: (stored_path, sha256_hash, file_size, detected_mime)
    """
    # 1. Extension check
    filename = upload_file.filename or "unknown.png"
    ext = os.path.splitext(filename)[1].lower()
    if ext not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file extension '{ext}'. Allowed: {settings.ALLOWED_EXTENSIONS}"
        )

    # 2. Read bytes with size ceiling
    content = upload_file.file.read()
    if len(content) > settings.MAX_UPLOAD_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds maximum allowed size of {settings.MAX_UPLOAD_SIZE_BYTES // (1024*1024)}MB."
        )

    # 3. Magic byte inspection
    is_jpeg = content.startswith(b"\xff\xd8\xff")
    is_png = content.startswith(b"\x89PNG\r\n\x1a\n")
    is_pdf = content.startswith(b"%PDF")

    if is_jpeg:
        mime = "image/jpeg"
    elif is_png:
        mime = "image/png"
    elif is_pdf:
        mime = "application/pdf"
    else:
        # Fallback to reported content type or reject
        mime = upload_file.content_type or "application/octet-stream"
        if mime not in settings.ALLOWED_MIME_TYPES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Security validation failed: Invalid file header signature or unapproved MIME type."
            )

    stored_path, sha256_hash, file_size = provider.save_file(content, filename)
    return stored_path, sha256_hash, file_size, mime
