# DocAI — Fake Identity & Document Screening System

> **AI-Powered Document Forensics, Biometric Verification & Zero-PII Blockchain Proofs**

[![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688?style=flat&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Next.js](https://img.shields.io/badge/Next.js-14.2-black?style=flat&logo=next.js&logoColor=white)](https://nextjs.org)
[![Solidity](https://img.shields.io/badge/Solidity-0.8.20-363636?style=flat&logo=solidity&logoColor=white)](https://soliditylang.org)
[![Ethereum Sepolia](https://img.shields.io/badge/Ethereum-Sepolia-blue?style=flat&logo=ethereum&logoColor=white)](https://sepolia.etherscan.io)
[![OpenCV](https://img.shields.io/badge/OpenCV-Forensics-5C3EE8?style=flat&logo=opencv&logoColor=white)](https://opencv.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

An enterprise-grade document screening platform designed for border security, KYC, and immigration checkpoints. Combines OCR extraction, image tampering forensics (Error Level Analysis), 1:1 facial biometric matching, explainable risk scoring, and zero-PII cryptographic blockchain verification on Ethereum Sepolia.

---

##  Key Highlights

| Feature | Description |
|:---|:---|
| ** Forensic Analysis** | ELA compression heatmaps, Laplacian edge noise variance, and EXIF software tampering tags. |
| ** ICAO Doc 9303 OCR** | Automated passport & visa MRZ parsing, checksum validation, and field confidence scoring. |
| ** 1:1 Face Verification**| Document portrait extraction vs. live selfie comparison with HSV skin-tone distribution. |
| ** Explainable Risk** | 0–100 normalized score with itemized penalty points (`LOW`, `MEDIUM`, `HIGH`, `CRITICAL`). |
| ** Zero-PII Blockchain** | Anchors cryptographic SHA-256 hashes on Ethereum Sepolia / local EVM sandbox. |
| ** Tamper-Evident Audit**| Append-only hash-chained ledger (`entry_hash = SHA256(prev_hash + data)`). |
| ** PDF Dossier Export** | Generates official, tamper-evident security clearance reports via ReportLab. |

---

##  Architecture

```
Next.js 14 Frontend (App Router, Tailwind CSS, Lucide UI)
   └─► REST API (FastAPI, Pydantic v2, JWT Auth, RBAC)
         ├─► AI Engines (MRZ OCR • ELA Forensics • 1:1 Face Match • Risk Scoring)
         ├─► Database (PostgreSQL / SQLite • Hash-Chained Audit Ledger)
         └─► Blockchain (Solidity Smart Contract • Sepolia / Local EVM Sandbox)
```

---

##  Quickstart

### 1. Backend (FastAPI)
```bash
# Navigate to project root & install dependencies
pip install -r requirements.txt
cp .env.example .env

# Start server (Swagger docs at http://127.0.0.1:8000/docs)
python -m uvicorn backend.app.main:app --reload --port 8000
```

### 2. Frontend (Next.js)
```bash
cd frontend
npm install
npm run dev
# Open http://localhost:3000
```

>  **Need step-by-step help, port conflict fixes, or alternative ports?**  
> Check the **[EXECUTION_GUIDE.md](EXECUTION_GUIDE.md)**.

---

##  Demo Accounts

Pre-seeded roles available on the login screen with 1-click quick-fill buttons:

| Role | Email | Password | Scope |
|:---|:---|:---|:---|
| **Border Officer** | `officer@docai.gov` | `Officer@123456` | Case intake, upload documents, run AI screening |
| **Supervisor** | `supervisor@docai.gov` | `Supervisor@123456` | Review flagged cases, audit inspection |
| **Administrator** | `admin@docai.gov` | `Admin@123456` | Full platform governance, risk engine tuning |

*Tip: Click **"Load Demo Dataset"** in the dashboard to populate 3 synthetic test cases (Clean Passport, Tampered Visa, Biometric Mismatch).*

---

##  Testing & Verification

```bash
# Backend unit & integration test suite (8 tests)
python -m pytest backend/tests/ -v

# Frontend production build check
cd frontend && npm run build
```

---

## Docker Deployment

```bash
docker-compose up --build -d
```
- Frontend: `http://localhost:3000` | Backend API: `http://localhost:8000` | Database: PostgreSQL `5432`

---

## Responsible AI & Zero-PII Notice
- **Decision Support Only**: AI outputs are strictly advisory (`MANUAL REVIEW REQUIRED`) to support human officer sovereignty.
- **Zero-PII On-Chain**: No personal identity attributes, document images, or biometric templates are ever recorded on the blockchain—only irreversible cryptographic hashes.
