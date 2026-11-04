"""
Application configuration management via Pydantic Settings.
Reads environment variables with production defaults.
"""
import os
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="allow")

    PROJECT_NAME: str = "AI Fake Identity & Document Screening System"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"

    # Security
    SECRET_KEY: str = os.getenv("JWT_SECRET", "super-secret-production-docai-key-change-in-prod-12345678")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    REFRESH_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./docai.db")

    # File Storage
    STORAGE_PROVIDER: str = os.getenv("STORAGE_PROVIDER", "local")  # "local", "s3"
    STORAGE_DIR: str = os.getenv("STORAGE_DIR", "./storage/uploads")
    MAX_UPLOAD_SIZE_BYTES: int = 15 * 1024 * 1024  # 15 MB
    ALLOWED_EXTENSIONS: List[str] = [".jpg", ".jpeg", ".png", ".pdf"]
    ALLOWED_MIME_TYPES: List[str] = ["image/jpeg", "image/png", "application/pdf"]

    # AI Providers
    OCR_PROVIDER: str = os.getenv("OCR_PROVIDER", "auto")

    # Blockchain Configuration
    BLOCKCHAIN_PROVIDER: str = os.getenv("BLOCKCHAIN_PROVIDER", "local_evm")  # "sepolia", "local_evm"
    BLOCKCHAIN_RPC_URL: str = os.getenv("BLOCKCHAIN_RPC_URL", "https://rpc.sepolia.org")
    BLOCKCHAIN_CONTRACT_ADDRESS: str = os.getenv("BLOCKCHAIN_CONTRACT_ADDRESS", "0x71C67e3FeB8Ab7e06a3B81C437e54F264DeEb852")
    BLOCKCHAIN_PRIVATE_KEY: str = os.getenv("BLOCKCHAIN_PRIVATE_KEY", "0x0000000000000000000000000000000000000000000000000000000000000001")
    SEPOLIA_EXPLORER_URL: str = "https://sepolia.etherscan.io"

    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3001",
    ]


settings = Settings()
