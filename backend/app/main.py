"""
Main FastAPI Application Entrypoint.
Orchestrates API routers, cybersecurity middleware, standardized error handling,
database initialization, and pre-seeded default administrative users.
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from backend.app.core.config import settings
from backend.app.core.database import engine, Base, SessionLocal
from backend.app.core.security import get_password_hash
from backend.app.models.models import User
from backend.app.api.v1 import (
    auth, cases, documents, screening, blockchain, analytics, audit, demo
)


def init_db():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        if db.query(User).count() == 0:
            users_to_seed = [
                User(
                    email="admin@docai.gov",
                    hashed_password=get_password_hash("Admin@123456"),
                    full_name="Chief Administrator",
                    role="ADMIN",
                    is_active=True
                ),
                User(
                    email="officer@docai.gov",
                    hashed_password=get_password_hash("Officer@123456"),
                    full_name="Border Officer Alex Vance",
                    role="OFFICER",
                    is_active=True
                ),
                User(
                    email="supervisor@docai.gov",
                    hashed_password=get_password_hash("Supervisor@123456"),
                    full_name="Operations Supervisor Morgan Croft",
                    role="SUPERVISOR",
                    is_active=True
                ),
            ]
            db.add_all(users_to_seed)
            db.commit()
    finally:
        db.close()


# Ensure tables and default seed accounts exist immediately
init_db()


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Production-ready AI Fake Identity & Document Screening System with Blockchain and Image Forensics",
    lifespan=lifespan
)

# 1. CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 2. Cybersecurity Headers Middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response


# 3. Standardized Error Handling
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {
                "code": f"HTTP_{exc.status_code}",
                "message": exc.detail,
                "path": str(request.url.path)
            }
        }
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "success": False,
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Invalid request parameters or payload format",
                "details": exc.errors(),
                "path": str(request.url.path)
            }
        }
    )


# 4. Mount API v1 Routers
app.include_router(auth.router, prefix=settings.API_V1_STR)
app.include_router(cases.router, prefix=settings.API_V1_STR)
app.include_router(documents.router, prefix=settings.API_V1_STR)
app.include_router(screening.router, prefix=settings.API_V1_STR)
app.include_router(blockchain.router, prefix=settings.API_V1_STR)
app.include_router(analytics.router, prefix=settings.API_V1_STR)
app.include_router(audit.router, prefix=settings.API_V1_STR)
app.include_router(demo.router, prefix=settings.API_V1_STR)


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "blockchain_provider": settings.BLOCKCHAIN_PROVIDER,
        "storage_provider": settings.STORAGE_PROVIDER
    }


@app.get("/")
def root():
    return {
        "message": "AI-Based Fake Identity & Document Screening System API",
        "docs_url": "/docs",
        "health_url": "/health",
        "version": settings.VERSION
    }
